# KEY = "Orangestar"
key_hex = [0x4F, 0x72, 0x61, 0x6E, 0x67, 0x65, 0x73, 0x74, 0x61, 0x72]
key_bits = []
for byte_val in key_hex:
  for i in range(7, -1, -1):
    key_bits.append((byte_val >> i) & 1)

ciphertext_bin = "000001110011101100110101001011010011001100100011000010000001110000010101000001100011111100000001010110110100000101001000000100100000010000000011010011110000101100100000000001110001010100011011000001010000000001011101000101110000111000011111011000000000010100000000000110100000010000001101010011000000001001011100000010100111011000110000001110110000101100100101001011000000100100010111001010110100001000110010"
ciphertext_bits = [int(b) for b in ciphertext_bin]

print("module chall(")

input_lines = []
for i in range(408):
  input_lines.append(f"    input plaintext_{407 - i}")

print(",\n".join(input_lines) + ",")

output_lines = []
for i in range(408):
  output_lines.append(f"    output result_{407 - i}")

print(",\n".join(output_lines))
print(");")
print()

for i in range(408):
  byte_idx = i // 8
  key_byte_idx = byte_idx % 10
  bit_in_byte = i % 8
  key_idx = key_byte_idx * 8 + bit_in_byte
  key_bit = key_bits[key_idx]
  cipher_bit = ciphertext_bits[i]
  pt_bit = f"plaintext_{407 - i}"
  c0 = "(plaintext_0 & ~plaintext_0)"
  c1 = "(plaintext_0 | ~plaintext_0)"
  key_signal = c1 if key_bit else c0
  cipher_signal = c1 if cipher_bit else c0
  expr = f"~({pt_bit} ^ {key_signal} ^ {cipher_signal})"
  print(f"    assign result_{407 - i} = {expr};")

print()
print("endmodule")
