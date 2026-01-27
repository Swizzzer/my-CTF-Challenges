from __future__ import annotations
import os
import secrets
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
from PIL import Image
import torch
import torchvision.transforms as T
from predict import predict_image_with_saved_model

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
UPLOAD_FOLDER = "./uploads"
FIXED_IMAGE_PATH = "./test_dir/test.png"
FLAG = os.environ.get("GZCTF_FLAG", "H3CTF{test_flag}")
L2_MAX = float("0.5")
MAX_CONTENT_LENGTH = 2 * 1024 * 1024
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
app = Flask(__name__)
app.config.update(
  UPLOAD_FOLDER=UPLOAD_FOLDER,
  MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
  SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(16)),
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
  return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_open_image(path: str) -> Image.Image:
  """Strict image open: verify then reopen in RGB to thwart trivial polyglots."""
  with Image.open(path) as im:
    im.verify()
  im = Image.open(path).convert("RGB")
  return im


def l2_between_images(
  img1: Image.Image, img2: Image.Image, img_size: int = 288
) -> float:
  tfm = T.Compose(
    [
      T.Resize((img_size, img_size)),
      T.ToTensor(),
    ]
  )
  x1 = tfm(img1).view(-1)
  x2 = tfm(img2).view(-1)
  return torch.norm(x1 - x2, p=2).item()


TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Anime Check · CTF</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="min-h-screen bg-gray-50 text-gray-800">
    <div class="mx-auto max-w-xl px-4 py-12">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-semibold tracking-tight">Anime Check</h1>
        <p class="text-sm text-gray-500 mt-2">Is this Mizore?</p>
      </div>

      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <form class="space-y-4" action="/" method="post" enctype="multipart/form-data">
          <div>
            <label for="file" class="block text-sm font-medium text-gray-700">选择图片（.png /.jpg）</label>
            <input id="file" name="file" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                   class="mt-2 block w-full rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white" required />
          </div>
          <button type="submit" class="w-full rounded-xl bg-black text-white py-2.5 text-sm font-medium hover:opacity-90">上传鉴定</button>
        </form>
      </div>

      {% if error %}
        <div class="mt-6 rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-800">{{ error }}</div>
      {% endif %}

      {% if checked %}
        {% if success %}
          <div class="mt-6 rounded-xl bg-emerald-50 border border-emerald-200 p-4">
            <div class="text-sm text-emerald-800">She is surely NOT Mizore!</div>
            <div class="mt-1 font-mono text-emerald-900 text-base select-all">{{ flag }}</div>
          </div>
        {% else %}
          <div class="mt-6 rounded-xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
            Not so good...
            <div class="mt-1 font-mono text-emerald-900 text-base select-all">L2 norm = {{ l2 }}</div>
          </div>
        {% endif %}
      {% endif %}

      <footer class="mt-10 text-center text-xs text-gray-400">© Kitauji, FIGHT!</footer>
    </div>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  if not os.path.exists(FIXED_IMAGE_PATH):
    return render_template_string(
      TEMPLATE,
      error="服务器配置错误：后端参考图不存在。",
      checked=False,
    ), 503

  if request.method == "GET":
    return render_template_string(TEMPLATE, checked=False)

  file = request.files.get("file")
  if file is None or file.filename == "":
    return render_template_string(TEMPLATE, error="未选择文件。", checked=False), 400

  if not allowed_file(file.filename):
    return render_template_string(
      TEMPLATE, error="仅支持 .png / .jpg。", checked=False
    ), 400

  ext = file.filename.rsplit(".", 1)[1].lower()
  fname = f"{secrets.token_hex(8)}.{ext}"
  save_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(fname))

  try:
    file.save(save_path)
  except Exception:
    return render_template_string(TEMPLATE, error="保存上传失败。", checked=False), 500

  try:
    user_img = safe_open_image(save_path)
  except Exception:
    try:
      os.remove(save_path)
    except Exception:
      pass
    return render_template_string(
      TEMPLATE, error="文件不是有效图片。", checked=False
    ), 400

  try:
    fixed_img = safe_open_image(FIXED_IMAGE_PATH)
  except Exception:
    try:
      os.remove(save_path)
    except Exception:
      pass
    return render_template_string(
      TEMPLATE, error="服务器图像读取失败。", checked=False
    ), 503
  try:
    l2 = l2_between_images(user_img, fixed_img, img_size=288)
  except Exception:
    try:
      os.remove(save_path)
    except Exception:
      pass
    return render_template_string(TEMPLATE, error="图像对比失败。", checked=False), 500
  try:
    is_target = predict_image_with_saved_model(save_path)[0]
  except Exception:
    is_target = False

  success = ((l2 <= L2_MAX) and (not is_target))
  try:
    os.remove(save_path)
  except Exception:
    pass

  if success:
    return render_template_string(
      TEMPLATE,
      checked=True,
      success=True,
      flag=FLAG,
    )
  else:
    return render_template_string(
      TEMPLATE,
      checked=True,
      success=False,
      l2=f"{l2:.6f}",
    )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=1337, debug=False)
