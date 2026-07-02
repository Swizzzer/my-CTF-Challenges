FROM alpine:3.22.4
RUN apk add --no-cache qemu-system-x86_64
COPY disk.img /disk.img
CMD qemu-system-x86_64 -drive file=disk.img,format=raw -m 256M -nographic -serial mon:stdio -netdev user,id=n1,hostfwd=tcp::8000-:8000 -device e1000,netdev=n1