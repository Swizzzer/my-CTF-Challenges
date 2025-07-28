from flask import Flask, render_template, request, send_from_directory, abort, send_file
import os
import secrets
import shutil
import requests
from advocate import get as ssrf_check
app = Flask(__name__)
app.config["ENV"] = "production"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["UPLOAD_PASSWORD"] = secrets.token_hex(16)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def err(message):
    return render_template("index.html", links=[], error=message)


def ok(links):
    return render_template("index.html", links=links, error=None)


@app.route("/", methods=["GET"])
def index():
    return ok([])


@app.route("/", methods=["POST"])
def upload():

    # ⚠️ Password is required
    input_password = request.form.get("password")
    if not input_password:
        return err("Password is required")
    if input_password != app.config["UPLOAD_PASSWORD"]:
        return err("Incorrect password")

    if "tarfile" not in request.files:
        return err("File not sent")

    tarfile_obj = request.files["tarfile"]
    if tarfile_obj.filename == "":
        return err("File not sent")

    tarfile_obj.seek(0, os.SEEK_END)
    if tarfile_obj.tell() > 10240:
        return err("File too big")
    tarfile_obj.seek(0)

    path = secrets.token_hex(16)
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], path)
    os.makedirs(upload_path, mode=0o755)

    temp_path = os.path.join(upload_path, "temp.tar")
    tarfile_obj.save(temp_path)

    try:
        os.system(f"tar -xvf {temp_path} -C {upload_path}")
    except:
        shutil.rmtree(upload_path, ignore_errors=True)
        return err("Error extracting tar file")

    os.remove(temp_path)

    links = []

    # 😡 Directory traversal is not allowed
    # 😆 And all the symlinks will be removed
    for root, dirs, files in os.walk(upload_path):
        for dir in dirs:
            if dir.startswith("."):
                continue
            full_path = os.path.join(root, dir)
            relative_path = os.path.relpath(
                full_path, app.config["UPLOAD_FOLDER"])
            links.append(relative_path)
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.islink(full_path):
                os.unlink(full_path)
                continue
            else:
                relative_path = os.path.relpath(
                    full_path, app.config["UPLOAD_FOLDER"])
                links.append(relative_path)

    return ok(links)


@app.route("/uploads/<path:filepath>")
def serve_upload(filepath):
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], filepath)
    if not os.path.isfile(full_path) or filepath.startswith("."):
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filepath)


# Super Secure Reverse Forwarder
# It may be useless, but having a window to look outside is always good😯💨
@app.route("/forward", methods=["GET", "POST"])
def forward():
    if request.method == "POST":
        url = request.form["url"]
        try:
            # You should check SSRF first!
            ssrf_check(url)
        except:
            return render_template("forward.html", error=f"🚫")

        req = requests.get(url)

        # 😋 You can even get the raw content of the request
        return req.content

    return render_template("forward.html")


# If the local user forgot his password, then he can get it here🤣
@app.route("/password")
def flag():
    if request.remote_addr == "127.0.0.1":
        return render_template("password.html", password=app.config["UPLOAD_PASSWORD"])
    else:
        abort(403)


@app.route("/favicon.ico")
def favicon():
    return send_file("favicon.ico")


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


if __name__ == "__main__":
    app.run("0.0.0.0", port=1337)
