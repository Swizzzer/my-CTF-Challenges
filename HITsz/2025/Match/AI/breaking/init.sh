#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag.txt
unset GZCTF_FLAG
python3 -u /home/ctf/chall.py