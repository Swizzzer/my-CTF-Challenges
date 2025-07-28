FROM ruby:3.4.3-slim-bullseye
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y gcc make
RUN gem install sinatra rackup puma
RUN useradd -m ctf
COPY --chown=ctf:ctf app.rb /home/ctf/app.rb
COPY --chown=ctf:ctf views /home/ctf/views
COPY --chown=ctf:ctf --chmod=500 init.sh /init.sh

USER ctf
WORKDIR /home/ctf

CMD /init.sh && ruby "/home/ctf/app.rb"
