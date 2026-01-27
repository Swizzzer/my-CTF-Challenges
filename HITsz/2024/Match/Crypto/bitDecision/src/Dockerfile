FROM ghcr.io/mirrorshub/docker/python:3.12.2

RUN apt-get update
RUN apt-get install -y xinetd
RUN pip install --no-cache-dir pycryptodome
COPY xinetd.conf /etc/xinetd.conf
RUN useradd -m ctf
COPY --chown=ctf:ctf chall.py /home/ctf/chall.py
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

USER ctf
WORKDIR /home/ctf

CMD /init.sh && xinetd -dontfork