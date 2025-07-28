
def reverse_file_content(input_file, output_file):
    try:
        with open(input_file, 'rb') as file:
            content = file.read()
        
        reversed_content = content[::-1]

        with open(output_file, 'wb') as file:
            file.write(reversed_content)
        
        print(f"Finished.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_filename = input("filename: ")
    output_filename = "reversed_"+input_filename
    reverse_file_content(input_filename, output_filename)
