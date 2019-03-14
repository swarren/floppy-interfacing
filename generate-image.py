#!/usr/bin/env python3

# Copyright 2019 Stephen Warren <swarren@wwwdotorg.org>
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import subprocess
import sys

if len(sys.argv) > 1:
    data_dir = sys.argv[1]
else:
    data_dir = 'data'
if len(sys.argv) > 2:
    image_fn = sys.argv[2]
else:
    image_fn = 'image.bin'

data_fns = os.listdir(data_dir)
data_fns = [fn for fn in data_fns if fn.endswith('.vcd')]

sectors = []
#n = 0
for data_fn in data_fns:
    cmd = [
        'sigrok-cli',
        '-I', 'vcd',
        '-i', os.path.join(data_dir, data_fn),
        '-P', 'floppy_flux:flux=2:frequency=1000000,floppy_ibm_pc',
        '-B', 'floppy_ibm_pc'
    ]
    print('+', ' '.join(cmd))
    cp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, encoding='UTF-8')
    for l in cp.stdout.splitlines():
        sectors.append(eval(l))
    #n += 1
    #if n >= 4:
    #    break

cylinders = max([sector[0] for sector in sectors]) + 1
heads = max([sector[1] for sector in sectors]) + 1
num_secs = max([sector[2] for sector in sectors]) # 1-based
sec_sizes = {len(sector[3]) for sector in sectors}
if len(sec_sizes) != 1:
    raise Exception("More than one sector size!")
sec_size = sec_sizes.pop()
print(cylinders, heads, num_secs, sec_size)

image = bytearray(cylinders * heads * num_secs * sec_size)

for c, h, s, data, found_crc, calc_crc in sectors:
    offset = c * heads
    offset += h
    offset *= num_secs
    offset += s - 1
    offset *= sec_size
    image[offset:offset+sec_size] = data

with open(image_fn, 'wb') as f:
    f.write(image)
