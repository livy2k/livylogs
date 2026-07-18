
import sys

def xor_obfuscate(s, key=0x7A):
    res = []
    for char in s:
        res.append(ord(char) ^ key)
    res.append(0 ^ key) # Null terminator XORed
    return res

strings = [
    "knockdown",
    "kneel",
    "intimidated",
    "prone",
    "knocked down",
    "kneeling",
    "incapacitated"
]

for s in strings:
    obs = xor_obfuscate(s)
    hex_vals = ", ".join([hex(v) for v in obs[:-1]]) + ", 0x00"
    print(f'unsigned char s_{s.replace(" ", "_")}[] = {{{hex_vals}}}; // {s}')
