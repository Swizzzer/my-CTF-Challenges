from flask import Flask, redirect
app = Flask(__name__)
i = 0
@app.route('/')
def index():
    global i 
    if i == 0:
        i += 1
        return "Nothing"
    else:
        return redirect("http://localhost:1337/password")
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
