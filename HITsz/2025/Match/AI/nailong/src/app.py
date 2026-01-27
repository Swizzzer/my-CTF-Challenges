# app.py
from flask import Flask, render_template, request, flash, redirect
import os
import numpy as np
from PIL import Image
import torch
import torchvision
from torchvision import transforms
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = "./uploads"
app.config["SECRET_IMAGE"] = "./nailong.png"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB
app.config["FLAG"] = open("flag.txt").read().strip()

# Initialize model
device = "cpu"
model = torchvision.models.resnet50()
num_ftrs = model.fc.in_features
model.fc = torch.nn.Linear(num_ftrs, 2)
# XiC1/nailong_model
model.load_state_dict(torch.load("./model_best.pth", map_location=device)["model"])
model = model.to(device)
model.eval()

# Image transforms
img_transform = transforms.Compose(
    [transforms.Resize(224), transforms.CenterCrop(224), transforms.ToTensor()]
)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "png"


def compare_images_l_inf(image_path1, image_path2):
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)

    if img1.size != img2.size:
        raise ValueError("Image dimensions must match secret image")
    if img1.mode != img2.mode:
        raise ValueError("Image color mode must match secret image")

    arr1 = np.array(img1, dtype=np.int16)
    arr2 = np.array(img2, dtype=np.int16)
    delta = np.abs(arr1 - arr2)
    print(delta.max())
    return delta.max() <= 2


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Only PNG files are allowed")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(upload_path)

        try:
            # Check L-infinity condition
            if not compare_images_l_inf(upload_path, app.config["SECRET_IMAGE"]):
                flash("Image modification exceeds allowed threshold (L∞ > 2)")
                return redirect(request.url)

            # Check model prediction
            img = Image.open(upload_path).convert("RGB")
            img_tensor = img_transform(img).unsqueeze(0).to(device)

            with torch.no_grad():
                outputs = model(img_tensor)
                prob = torch.nn.functional.softmax(outputs, dim=1)[0][1].item()

            if prob >= 0.6:
                flash(f"Classified as nailong! ({prob * 100:.1f}%)")
                flash("😡")
                return redirect(request.url)

            return app.config["FLAG"]

        except Exception as e:
            flash(str(e))
            return redirect(request.url)

    return render_template("index.html")


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=8000)
