FROM python:3.10-slim-bullseye

RUN useradd -m ctf

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt-get update 
RUN apt-get install -y ruby make 

RUN python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    flask 
RUN gem install doublehelix

COPY --chown=ctf:ctf build/app.py /home/ctf/

COPY --chown=ctf:ctf --chmod=700 build/src/* /home/ctf/
COPY --chown=ctf:ctf --chmod=500 build/src/init.sh /init.sh

WORKDIR /home/ctf
USER ctf

CMD /init.sh