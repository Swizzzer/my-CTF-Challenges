FROM python:3.13-alpine

RUN adduser -D -h /home/ctf ctf
RUN pip install --no-cache-dir flask
COPY --chown=ctf:ctf app.py /home/ctf/app.py
COPY --chown=ctf:ctf templates/ /home/ctf/templates/
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

USER ctf
WORKDIR /home/ctf


CMD /init.sh