with open("/home/ctf/flag", "r") as f:
    flag = f.read().strip()

with open('gen.rb', 'r') as f:
    content = f.read()

modified_content = content.replace('FLAG_TEMPLATE', flag)

with open('gen.rb', 'w') as f:
    f.write(modified_content)
