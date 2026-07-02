flag = b"HITCTF{https://www.youtube.com/watch?v=x9BZeBIzcJ0}"
key = b"Orangestar"
ct = bytes([b ^ key[i % len(key)] for i, b in enumerate(flag)])
print("".join(f"{b:08b}" for b in ct))
