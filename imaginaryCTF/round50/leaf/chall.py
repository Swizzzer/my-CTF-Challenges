def encrypt_string(string):
    def encrypt_recursive(start, end, ind):
        if start == end:
            cipher[ind] = ord(string[start])
        else:
            mid = (start + end) // 2
            encrypt_recursive(start, mid, 2 * ind + 1)
            encrypt_recursive(mid + 1, end, 2 * ind + 2)
            cipher[ind] = cipher[2 * ind + 1] + cipher[2 * ind + 2]

    n = len(string)
    cipher = [0] * (4 * n)
    encrypt_recursive(0, n - 1, 0)
    return cipher


flag = open("flag.txt", "r").read().strip()
c = encrypt_string(flag)
print(c)
