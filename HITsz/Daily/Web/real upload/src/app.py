from flask import Flask, render_template, request, send_from_directory, abort
import os
import tarfile
import secrets
import shutil

app = Flask(__name__)
app.config['ENV'] = 'production'
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def err(message):
    return render_template('index.html', links=[], error=message)

def ok(links):
    return render_template('index.html', links=links, error=None)

@app.route('/', methods=['GET'])
def index():
    return ok([])

@app.route('/', methods=['POST'])
def upload():
    if 'tarfile' not in request.files:
        return err("File not sent")
    
    tarfile_obj = request.files['tarfile']
    if tarfile_obj.filename == '':
        return err("File not sent")
    
    tarfile_obj.seek(0, os.SEEK_END)
    if tarfile_obj.tell() > 10240:
        return err("File too big")
    tarfile_obj.seek(0)

    path = secrets.token_hex(16)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    os.makedirs(upload_path, mode=0o755)

    temp_path = os.path.join(upload_path, 'temp.tar')
    tarfile_obj.save(temp_path)

    try:
        os.system(f'tar -xvf {temp_path} -C {upload_path}')
    except:
        shutil.rmtree(upload_path, ignore_errors=True)
        return err("Error extracting tar file")
    
    os.remove(temp_path)

    links = []
    for root, dirs, files in os.walk(upload_path):
        for dir in dirs:
            if dir.startswith('.'):
                continue
            full_path = os.path.join(root, dir)
            relative_path = os.path.relpath(full_path, app.config['UPLOAD_FOLDER'])
            links.append(relative_path)
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.islink(full_path):
                os.unlink(full_path)
                continue
            else:
                relative_path = os.path.relpath(full_path, app.config['UPLOAD_FOLDER'])
                links.append(relative_path)

    return ok(links)

@app.route('/uploads/<path:filepath>')
def serve_upload(filepath):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
    if not os.path.isfile(full_path) or filepath.startswith('.'):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

@app.errorhandler(404)
def not_found(error):
    return '404', 404

@app.errorhandler(500)
def server_error(error):
    return '500', 500

if __name__ == '__main__':
    app.run("0.0.0.0", port=1337)