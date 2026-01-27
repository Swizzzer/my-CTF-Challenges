F = Zmod(256)

c = [244,234,44,232,127,51,130,1,186,20,223,108,112]
k = [237,193,38,244,27,112,148,47,141,63,213,47,102]
p = []
flag = ""
for (cc,kk) in zip(c,k):
    tmp = cc^^kk
    p.append(F(tmp))
for pp in p:
    flag+=chr((pp-71)/3)
print(flag)


