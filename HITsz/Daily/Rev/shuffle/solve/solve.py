def reverse_shuffle(output_block):
    vec1_order = [11, 2, 7, 4, 3, 9, 10, 0]
    vec2_order = [12, 8, 13, 6, 14, 5, 1, 15]
    
    vec1 = [output_block[i] for i in vec1_order]
    vec2 = [output_block[i] for i in vec2_order]
    
    return bytes(vec1 + vec2)

def recover_input(input_path, output_path):
    with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        while True:
            chunk = f_in.read(16)
            if not chunk:
                break
            output_block = list(chunk)
            if len(output_block) < 16:
                output_block += [0] * (16 - len(output_block))
            original_block = reverse_shuffle(output_block)
            f_out.write(original_block)

if __name__ == "__main__":
    recover_input('output.txt', 'recovered.txt')
    print("Finished: output.txt -> recovered.txt")