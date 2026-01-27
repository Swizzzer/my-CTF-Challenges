proc lcg(n: int): int =
    var m = (69 * n + 42) mod 24
    return m

echo "Enter the flag: "
var flag: string
flag = stdin.readLine()

assert flag.len == 24

var flag_perm: array[24, char]
for i in 0..<24:
    flag_perm[i] = '\0'

var tmp = 7312

for i in 0..<24:
    tmp = lcg(tmp)
    while flag_perm[tmp] != '\0':
        tmp = (tmp + 1) mod 24
    flag_perm[tmp] = flag[i]

let c = "gs3t_capaw_eladhs}f{_aa2"

# 拼接 flag_perm 数组
var flag_perm_str: string = ""
for i in 0..<24:
    flag_perm_str.add(flag_perm[i])

if flag_perm_str == c:
    echo "Correct!"
else:
    echo "Wrong!"
