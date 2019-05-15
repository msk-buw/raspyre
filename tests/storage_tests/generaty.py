'''
Create synthetic data for testing purposes, approx 100Hz and linear in x and sinus in y.
'''

import time
import random
import math
import struct

start=1488201843.464029

with open('tests/binary.rm01', 'ab') as f:
    for i in range(1000):
        x = i/500 - 0.5 + random.random()*0.01
        y = math.sin(i/20) + random.random()*0.01
        w = struct.pack('ddd', start, x, y)
        f.write(w)
        start = start + 0.01 + (random.random()-0.5)*0.001


