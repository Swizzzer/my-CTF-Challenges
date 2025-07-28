#! /usr/bin/env python3

import os

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print('\nWrite your safe Rust code below: (at most 32 bytes, "//EOF" to stop)')
    program = b''
    while True:
        line = input().encode('utf-8')
        if line==b'//EOF':
            break
        program += line+b'\n'
        assert len(program) <= 32

    if b'std' in program:
        print('Your code is rejected, because it is not safe enough...')
        exit(1)

    file = open('saferust/src/program.rs', 'wb')
    file.write(program)
    file.close()

    print('Compiling...')
    os.chdir('saferust')
    os.execlp('cargo', 'cargo', 'build', '--release')

if __name__ == '__main__':
    main()
