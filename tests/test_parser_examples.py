# Simple test script to exercise parser functions in helpers.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from custom_components.dtrelay_binary import helpers

# example binary find frame (header 05 AA + 32 bytes)
frame = bytes.fromhex('05AA') + ( (12345).to_bytes(4,'little') + (0x0100).to_bytes(4,'little') + (0x0100).to_bytes(4,'little') + (16).to_bytes(4,'little') + ( (127).to_bytes(1,'little')*4 ) + (0xFFFFFF00).to_bytes(4,'little') + ( (127).to_bytes(1,'little')*4 ) + ( (127).to_bytes(1,'little')*4 ) )
res = helpers._parse_binary_frame(frame)
print('Find parse ->', res)

# example status frame: command(FF) result xor, session, relay_cmd=0, pwd_lo, pwd_hi, relay(2 bytes), input(2 bytes)
status = bytes([0xFF, 0x00 ^ 0xAA, 1, 0x00, 0, 0]) + bytes([0x03, 0x00, 0x05, 0x00])
res2 = helpers._parse_binary_frame(status)
print('Status parse ->', res2)
