FROM python:3.12-slim-bullseye

RUN useradd -m ctf

RUN apt-get update 
RUN python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    flask

ADD --chown=ctf:ctf src /home/ctf
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

WORKDIR /home/ctf
USER ctf

CMD /init.sh
