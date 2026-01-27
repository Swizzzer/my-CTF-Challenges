FROM --platform=linux/amd64 python:3.12-alpine 

RUN apk add --no-cache socat && adduser -D -h /home/ctf ctf
RUN pip install --no-cache-dir pycryptodome
COPY --chown=ctf:ctf chall.py /home/ctf/chall.py
COPY --chown=ctf:ctf flag.txt /home/ctf/flag.txt

USER ctf
WORKDIR /home/ctf


CMD socat tcp-l:8000,reuseaddr,fork exec:"python3 -u /home/ctf/chall.py",stderr
