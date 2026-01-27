#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag
unset GZCTF_FLAG
make
python app.py