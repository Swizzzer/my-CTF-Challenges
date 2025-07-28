#!/bin/sh

echo $GZCTF_FLAG > /home/ctf/flag.txt
unset GZCTF_FLAG
python -u /home/ctf/app.py
while true; do
  sleep 30
  echo "Keeping Alive..."
done