FROM archlinux:latest

RUN useradd -m ctf

RUN pacman -Syy
RUN pacman -Syy zig make rustup python python-flask --noconfirm

COPY --chown=ctf:ctf build/app.py /home/ctf/
COPY --chown=ctf:ctf --chmod=700 build/src/* /home/ctf/src/
COPY --chown=ctf:ctf --chmod=700 build/Cargo.toml build/catflag.py build/Makefile /home/ctf/
COPY --chown=ctf:ctf --chmod=500 build/init.sh /init.sh

WORKDIR /home/ctf
USER ctf
RUN rustup default stable
RUN rustup target add riscv64gc-unknown-linux-musl
RUN cargo install --locked cargo-zigbuild

CMD /init.sh