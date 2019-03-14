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
import struct
import subprocess
import sys
import time

# Set to false to debug without Teensy attached
if True:
    from serial import Serial
else:
    class Serial(object):
        def __init__(self, filename):
            pass

        def write(self, data):
            pass

        def flush(self):
            pass

        def reset_input_buffer(self):
            pass

        def read(self):
            return bytes([0])

        def close(self):
            pass

BIT = lambda bit: 1 << bit

DRIVE_SEL_B = BIT(0)
MOTOR_EN_B  = BIT(1)
DIRECTION   = BIT(2)
STEP        = BIT(3)
HEAD        = BIT(4)

TRACK0      = BIT(4)
WRITE_PROT  = BIT(5)
CHANGE_RDY  = BIT(6)

def monotonic_ms(do_round_up):
    t = time.monotonic()
    if do_round_up:
        t += 0.001
    return int(t * 1000)

class Floppy(object):
    def __init__(self):
        # So that __del__ can always read self.s;  an exception thrown opening
        # the serial port will skip assigning the variable.
        self.s = None
        self.s = Serial('/dev/ttyACM0')
        self._out(0xff)
        self._selected = False
        self._direction = True
        self._track = 999

        self._last_motor_on = 0
        self._last_select = 0
        self._last_direction = 0
        self._last_step_direction = None
        self._last_step = 0
        self._last_head = 0

        self.select()
        self.track0()
        self.deselect()

    def _set(self, val):
        self._out(self._out_val | val)

    def _clr(self, val):
        self._out(self._out_val & ~val)

    def _out(self, out):
        self._out_val = out
        self.s.write(b'=' + struct.pack("B", self._out_val))
        self.s.flush()

    def _in(self):
        self.s.reset_input_buffer()
        self.s.write(b'?')
        self.s.flush()
        v = self.s.read()
        vi = int.from_bytes(v, "little")
        print('In:', vi)
        return vi

    def _wait_since(self, wait_since, wait_at_least_ms):
        t = monotonic_ms(do_round_up=False)
        wait_until_ms = wait_since + wait_at_least_ms
        wait_ms = wait_until_ms - t
        print(
            'Wait:',
            'since', wait_since,
            'at least', wait_at_least_ms,
            'until', wait_until_ms,
            't', t,
            'delay', wait_ms)
        if wait_ms < 0:
            return
        wait_ms = int(wait_ms + 0.999999)
        time.sleep(wait_ms / 1000.0)

    def select(self):
        if self._selected:
            return
        self._clr(DRIVE_SEL_B)
        self._last_select = monotonic_ms(do_round_up=True)
        self._clr(MOTOR_EN_B)
        self._last_motor = monotonic_ms(do_round_up=True)
        self._selected = True

    def deselect(self):
        if not self._selected:
            return
        self.settle_seek_complete()
        self._set(MOTOR_EN_B)
        self._set(DRIVE_SEL_B)
        self._selected = False

    def _set_direction(self, direction):
        if not self._selected:
            raise Exception('Not selected')
        direction = bool(direction)
        if self._direction == direction:
            return
        self.settle_seek_complete()
        if direction:
            self._set(DIRECTION)
        else:
            self._clr(DIRECTION)
        self._last_direction = monotonic_ms(do_round_up=True)
        self._direction = direction

    def _step(self, force):
        if not self._selected:
            raise Exception('Not selected')
        if self._direction:
            if (not force) and (self._track == 0):
                return
            incr = -1
        else:
            if (not force) and (self._track == 79):
                return
            incr = 1
        print('Step', incr)
        if self._direction == self._last_step_direction:
            wait_for_ms = 3
        else:
            wait_for_ms = 4
        self._last_step_direction = self._direction
        self._wait_since(self._last_step, wait_for_ms)
        self._wait_since(self._last_select, 1)
        self._clr(STEP)
        self._set(STEP)
        self._last_step = monotonic_ms(do_round_up=True)
        self._track += incr

    def track0(self):
        self._wait_since(self._last_select, 1)
        self._set_direction(True)
        ctr = 0
        while True:
            v = self._in()
            if not (v & TRACK0):
                break
            print('Step in to track0:', ctr)
            ctr += 1
            self._step(True)
        self._track = 0

    def seek(self, track):
        if not self._selected:
            raise Exception('Not selected')
        track = int(track)
        if track < 0 or track > 79:
            raise Exception('Bad track')
        if self._track == track:
            return
        print('Seek', track)
        diff = track - self._track
        self._set_direction(1 if (diff < 0) else 0)
        for iter in range(abs(diff)):
            self._step(False)

    def set_head(self, head):
        if not self._selected:
            raise Exception('Not selected')
        print('Head:', head)
        if head:
            self._clr(HEAD)
        else:
            self._set(HEAD)
        self._last_head = monotonic_ms(do_round_up=True)

    def settle_seek_complete(self):
        self._wait_since(self._last_step, 18)

    def settle_before_read(self):
        self._wait_since(self._last_motor_on, 1000)
        self._wait_since(self._last_select, 1)
        self.settle_seek_complete()
        self._wait_since(self._last_head, 1)
        time.sleep(0.18 - 0.03)

    def __del__(self):
        if self.s:
            self._out(0xff)
            self.s.close()

def capture(filename):
    print('Capturing...')
    cmd = [
        'sigrok-cli',
        '-d', 'asix-sigma',
        '-O', 'vcd',
        '-o', filename,
        '--config', 'samplerate=25m',
        '--channels', '1-2',
        '--time', '425ms'
    ]
    print('+', ' '.join(cmd))
    subprocess.run(cmd, check=True)

if len(sys.argv) > 1:
    dirname = sys.argv[1]
else:
    dirname = 'data'
if not os.path.exists(dirname):
    os.makedirs(dirname)

f = Floppy()
f.select()
for track in range(80):
    f.seek(track)
    for head in range(2):
        f.set_head(head)
        f.settle_before_read()
        capture(os.path.join(dirname, 'track-t%02d-h%d.vcd' % (track, head)))
f.deselect()
del f
