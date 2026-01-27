#!/bin/sh

echo $GZCTF_FLAG > /home/guest/flag.txt
unset GZCTF_FLAG

socat -v -s TCP4-LISTEN:9999,tcpwrap=script,reuseaddr,fork EXEC:"python3 /home/guest/service.py",stderr
