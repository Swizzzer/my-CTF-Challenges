#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag
unset GZCTF_FLAG
python catflag.py
make
python app.py