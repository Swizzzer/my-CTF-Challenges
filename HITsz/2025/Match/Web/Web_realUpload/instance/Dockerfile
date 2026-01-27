FROM python:3.10-slim

RUN useradd -m ctf && apt update
RUN apt install -y gcc
RUN pip install --no-cache-dir flask advocate

ADD --chown=ctf:ctf src /home/ctf
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

WORKDIR /home/ctf
USER ctf

CMD /init.sh
