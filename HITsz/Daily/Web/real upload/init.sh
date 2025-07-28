#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag.txt
unset GZCTF_FLAG
python app.py