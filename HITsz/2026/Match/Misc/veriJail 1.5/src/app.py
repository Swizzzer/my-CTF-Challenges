from flask import Flask, request, render_template
import subprocess
from secrets import token_hex

app = Flask(__name__)


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/writefile", methods=["POST"])
def write_file():
  filename = request.args.get("filename", f"{token_hex(4)}")
  filename = filename.removesuffix(".html")

  if (
    filename.startswith(("home", "ctf", "/", ".", "~"))
    or ".." in filename
    or len(filename) <= 8
  ):
    filename = f"{token_hex(4)}"
  content = request.data
  try:
    with open(filename, "wb") as f:
      f.write(content)
      f.flush()
    return "🍻 File written successfully", 200
  except Exception as e:
    return str(e), 500


@app.route("/execute")
def execute():
  BLACKLISTS = ["*", "|", "-", ":", ">", "&", "\\", "$", " ", ".", "/", "<"]

  cmd = request.args.get("cmd", "")
  for blk in BLACKLISTS:
    if blk in cmd:
      return "💥 Invalid command", 400
  if len(cmd) > 4:
    return "💥 Invalid command", 400
  try:
    output = subprocess.check_output(cmd, shell=True)
    return output, 200
  except Exception as e:
    return str(e), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=1337)
