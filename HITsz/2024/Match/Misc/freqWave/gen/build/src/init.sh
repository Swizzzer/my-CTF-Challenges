#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag.txt
unset GZCTF_FLAG
python chall.py
python app.py