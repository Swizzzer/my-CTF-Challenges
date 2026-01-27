FROM python:3.12-slim

RUN useradd -m ctf
RUN pip install --no-cache-dir -i https://mirrors.osa.moe/pypi/web/simple flask pillow werkzeug
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY --chown=ctf:ctf app.py /home/ctf/app.py
COPY --chown=ctf:ctf predict.py /home/ctf/predict.py
COPY --chown=ctf:ctf models /home/ctf/models
COPY --chown=ctf:ctf test_dir /home/ctf/test_dir

USER ctf
WORKDIR /home/ctf

CMD python app.py