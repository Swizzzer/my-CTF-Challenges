FROM python:3.13-alpine

RUN apk add --no-cache socat && adduser -D -h /home/ctf ctf
COPY --chown=ctf:ctf src/chall.py /home/ctf/chall.py
COPY --chown=ctf:ctf src/cipher.py /home/ctf/cipher.py
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

USER ctf
WORKDIR /home/ctf


CMD /init.sh && socat tcp-l:8000,reuseaddr,fork exec:"python3 -u /home/ctf/chall.py",stderr