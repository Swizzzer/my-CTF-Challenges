import subprocess
import re
import string
from tqdm import trange
def extract_instructions(perf_output):
    match = re.search(r'(\d+)::instructions:([a-zA-Z]):(\d+):([\d.]+)::', perf_output)
    if not match:
        raise ValueError("Failed to extract instructions count")
    return int(match.group(1))

def run_perf(binary, input_str):
    cmd = ["perf", "stat", "-x:","-e", "instructions:u", binary]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )
    _, stderr = proc.communicate(input=input_str)
    return extract_instructions(stderr)

def dynamic_bruteforce(binary, length=9):
    charset = string.ascii_lowercase + string.digits + '_' + string.ascii_uppercase
    correct = ['_'] * length
    
    for position in trange(length):
        max_instr = 0
        candidate = '_'
        history = []
        
        for char in charset:
            test_input = ''.join(correct[:position]) + char + '_' * (length - position - 1)
            
            try:
                instr = run_perf(binary, test_input)
            except Exception as e:
                print(f"Error testing {char}: {str(e)}")
                continue
            
            # print(f"Testing {char}: {instr} instructions")
            history.append(instr)
            if len(history) > 1:
                if instr > max_instr + 100:
                    # print(f"Jitter found in {char}")
                    candidate = char
                    break

            if instr > max_instr:
                max_instr = instr
                candidate = char
        
        correct[position] = candidate
        # print(f"Position {position} = {candidate}")
        print(f"Current string: {''.join(correct)}")
    
    return ''.join(correct)

if __name__ == "__main__":
    target_binary = "./chall"
    result = dynamic_bruteforce(target_binary)
    print(f"The possible input is: {result}")