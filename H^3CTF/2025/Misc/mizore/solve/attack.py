import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from torchvision.transforms import InterpolationMode
from torchvision.models import efficientnet_v2_m
from predict import predict_image_with_saved_model
from tqdm import trange

MODEL_PATH = "../src/models/anime_classifier_efficientnetv2m_best.pt"
FIXED_IMAGE_PATH = "../src/test_dir/test.png"
OUT_PATH = "./adv_submit.png"

IMG_SIZE = 288
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
EPS_L2 = 0.5
STEPS = 500
STEP_SIZE = 0.0000035
THRESH = 0.5

# 设备
if torch.backends.mps.is_available():
  DEVICE = torch.device("mps")
elif torch.cuda.is_available():
  DEVICE = torch.device("cuda")
else:
  DEVICE = torch.device("cpu")

_server_tfm = transforms.Compose(
  [
    transforms.Resize((IMG_SIZE, IMG_SIZE), interpolation=InterpolationMode.BILINEAR),
    transforms.ToTensor(),
  ]
)


def server_feat_from_pil(pil_img: Image.Image) -> torch.Tensor:
  return _server_tfm(pil_img.convert("RGB")).reshape(-1)


def server_l2_from_tensors(y_pixel_01: torch.Tensor, x0_pil: Image.Image) -> float:
  y_pil = transforms.ToPILImage()(y_pixel_01.clamp(0, 1).detach().cpu())
  fy = server_feat_from_pil(y_pil)
  return torch.norm(fy - server_feat_from_pil(x0_pil), p=2).item()


def load_model_and_meta(model_path: str):
  assert os.path.exists(model_path), f"ckpt 不存在：{model_path}"
  raw = torch.load(model_path, map_location="cpu")

  if (
    isinstance(raw, dict)
    and "state_dict" in raw
    and isinstance(raw["state_dict"], dict)
  ):
    state_dict = raw["state_dict"]
    meta_ckpt = raw
  elif isinstance(raw, dict):
    state_dict = raw
    meta_ckpt = {}
  else:
    raise RuntimeError("无法识别的 checkpoint 格式。")

  PREFIXES = ("module.", "model.", "_orig_mod.", "_forward_module.")

  def strip_prefix(k):
    for p in PREFIXES:
      if k.startswith(p):
        return strip_prefix(k[len(p) :])
    return k

  state_dict = {strip_prefix(k): v for k, v in state_dict.items()}

  keys = list(state_dict.keys())
  if "classifier.1.weight" in state_dict:
    fc_w_name = "classifier.1.weight"
  elif "classifier.0.weight" in state_dict:
    fc_w_name = "classifier.0.weight"
  else:
    cand = [k for k in keys if k.endswith(".weight")]
    cand.sort()
    fc_w_name = cand[-1]
  num_classes = state_dict[fc_w_name].shape[0]

  model = efficientnet_v2_m(weights=None)
  in_features = model.classifier[-1].in_features
  model.classifier[-1] = nn.Linear(in_features, num_classes)
  model.load_state_dict(state_dict, strict=False)
  model.eval().to(DEVICE)

  classes = (
    meta_ckpt.get("classes")
    or meta_ckpt.get("meta", {}).get("classes")
    or (
      ["positve", "negative"][:num_classes]
      if num_classes <= 2
      else [f"class_{i}" for i in range(num_classes)]
    )
  )
  pos_name = (
    meta_ckpt.get("positive_class_name")
    or meta_ckpt.get("meta", {}).get("positive_class_name")
    or next((c for c in classes if c.lower() != "negative"), classes[0])
  )
  if pos_name not in classes:
    classes = [pos_name] + [c for c in classes if c != pos_name]
  pos_idx = classes.index(pos_name)

  return model, pos_idx


def preprocess_tensor_pixel01(x01: torch.Tensor) -> torch.Tensor:
  x = x01.unsqueeze(0)
  x = F.interpolate(
    x,
    size=(IMG_SIZE, IMG_SIZE),
    mode="bilinear",
    align_corners=False,
    antialias=True,
  )
  mean = torch.tensor(IMAGENET_MEAN, device=x.device)[None, :, None, None]
  std = torch.tensor(IMAGENET_STD, device=x.device)[None, :, None, None]
  x = (x - mean) / std
  return x


def main():
  assert os.path.exists(FIXED_IMAGE_PATH), f"原图不存在：{FIXED_IMAGE_PATH}"
  x0_pil = Image.open(FIXED_IMAGE_PATH).convert("RGB")
  x0_pixel = transforms.ToTensor()(x0_pil)
  y = x0_pixel.to(DEVICE).clone().detach().requires_grad_(True)
  model, pos_idx = load_model_and_meta(MODEL_PATH)

  fx0 = server_feat_from_pil(x0_pil)

  for _ in trange(STEPS):
    logits = model(preprocess_tensor_pixel01(y))
    loss = logits[0, pos_idx]
    g = torch.autograd.grad(loss, y, retain_graph=False, create_graph=False)[0]

    with torch.no_grad():
      g_norm = g.reshape(-1).norm(p=2).clamp(min=1e-12)
      y.add_(-STEP_SIZE * g / g_norm)
      y.clamp_(0.0, 1.0)

      y_pil = transforms.ToPILImage()(y.detach().cpu())
      fy = server_feat_from_pil(y_pil)
      l2_now = torch.norm(fy - fx0, p=2).item()
      if l2_now > EPS_L2:
        alpha = EPS_L2 / l2_now
        y = (x0_pixel.to(DEVICE) + (y - x0_pixel.to(DEVICE)) * alpha).clamp(0, 1)
        y.requires_grad_(True)

  adv_pil = transforms.ToPILImage()(y.clamp(0, 1).detach().cpu())
  adv_pil.save(OUT_PATH, format="PNG")
  adv_disk = Image.open(OUT_PATH).convert("RGB")
  l2_check = torch.norm(server_feat_from_pil(adv_disk) - fx0, p=2).item()

  is_target, pos_prob = predict_image_with_saved_model(
    OUT_PATH, model_path=MODEL_PATH, threshold=THRESH
  )

  print(f"[RESULT] Saved: {OUT_PATH}  (size={adv_disk.size}, orig={x0_pil.size})")
  print(
    f"[CHECK] L2 (server-style) = {l2_check:.6f}  (<= {EPS_L2}? {'YES' if l2_check <= EPS_L2 else 'NO'})"
  )
  print(f"[PRED ] pos_prob = {pos_prob:.6f}  -> is_target = {is_target}  (need False)")


if __name__ == "__main__":
  main()
