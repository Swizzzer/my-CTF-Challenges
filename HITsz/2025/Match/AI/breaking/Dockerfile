FROM python:3.12-slim

RUN useradd -m ctf
RUN pip install --no-cache-dir -i https://mirrors.ustc.edu.cn/pypi/simple gradio openai
COPY --chown=ctf:ctf chall.py /home/ctf/chall.py
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

ENV OPENAI_API_BASE="https://api.deepseek.com"
ENV OPENAI_API_KEY="sk-*****************"
ENV MODEL_NAME="deepseek-chat"

USER ctf
WORKDIR /home/ctf


CMD /init.sh
