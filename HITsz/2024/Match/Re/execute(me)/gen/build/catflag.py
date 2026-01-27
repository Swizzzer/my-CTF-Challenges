ALPHABET = "982647513ABCDEJHGFKLMNPQRSTUVWZXYabcdefghijkmnopqrstuv!@#$"


def encode(input_string):

    input_numbers = list(input_string.encode('utf-8'))
    output = []

    for num in input_numbers:
        in_byte = num

        for i in range(len(output)):
            in_byte += output[i] << 8
            output[i] = in_byte % 58
            in_byte //= 58

        while in_byte > 0:
            output.append(in_byte % 58)
            in_byte //= 58

    for num in input_numbers:
        if num == 0:
            output.append(0)
        else:
            break

    encoded_output = ''.join(ALPHABET[byte] for byte in output)
    return encoded_output


if __name__ == "__main__":

    with open("/home/ctf/flag", "r") as f:
        flag = f.read().strip()

    with open('/home/ctf/src/main.rs', 'r') as f:
        content = f.read()
    encoded_string = encode(flag)
    modified_content = content.replace('FLAG_TEMPLATE', encoded_string)

    with open('/home/ctf/src/main.rs', 'w') as f:
        f.write(modified_content)
