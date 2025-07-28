FROM ghcr.io/rust-lang/rust:nightly-bullseye-slim

COPY init.sh /init

RUN apt-get update -y
RUN apt-get install -y socat
RUN useradd -m -s /bin/bash guest

COPY --chown=guest app /home/guest/

RUN cd /home/guest/saferust

ENTRYPOINT [ "/init" ]
