FROM python:3.12-slim

RUN useradd -m ctf
RUN pip install --no-cache-dir -i https://mirrors.ustc.edu.cn/pypi/simple flask pillow numpy werkzeug
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY --chown=ctf:ctf app.py /home/ctf/app.py
COPY --chown=ctf:ctf model_best.pth /home/ctf/model_best.pth
COPY --chown=ctf:ctf nailong.png /home/ctf/nailong.png
COPY --chown=ctf:ctf templates /home/ctf/templates/
COPY --chown=ctf:ctf uploads /home/ctf/uploads/
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

USER ctf
WORKDIR /home/ctf


CMD /init.sh