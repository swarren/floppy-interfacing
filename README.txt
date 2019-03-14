Background
========================================

This repository contains code to control an IBM PC 3.5" floppy drive using a
Teensy2.0++ micro-controller, and capture data using an ASIX Sigma2 logic
analyzer using sigrok. As a bonus there's a program to play music on the floppy
drive. The Python code was written under Linux, but probably works anywhere
that sigrok and Python work.

Hardware configuration
========================================

The code assumes that the following hardware connections are made:

Teensy2.0++ port/pin  Floppy drive signal
--------------------  -------------------
GND                   Ground (3)
PORT C pin 0          DRIVE_SEL_B (12)
PORT C pin 1          MOTOR_EN_B (16)
PORT C pin 2          DIRECTION (18)
PORT C pin 3          STEP (20)
PORT C pin 4          HEAD (32)
PORT B pin 4          TRACK0 (26)
PORT B pin 5          WRITE_PROT (28) (unused)
PORT B pin 6          CHANGE_RDY (34) (unused)

ASIX Sigma2 pin  Floppy drive signal
---------------  -------------------
GND              Ground
Pin 1            INDEX (with pull-up to 5V on Teensy, e.g. 3K3)
Pin 2            RDATA (with pull-up to 5V on Teensy, e.g. 3K3)

Note: When connecting to the floppy drive's ground signal, be aware that at
least some floppy drives do not connect to pin 1 of the 34-pin connector at
all; use pin 3 or greater. Some floppy drives have open-collector outputs and
hence need pullups on the logic analyzer inputs; others drive signals in a
push-pull fashion and wouldn't need pull-ups. The Teensy has built-in pull-ups
so external pull-ups aren't needed for the input signals connected to the
Teensy.

Files in this repository
========================================

teensy-usb-gpio/teensy-usb-gpio.ino:

Configures the Teensy as a USB serial device. Allows a connected PC read/write
access to the pins on the floppy drive. Compile using the Arduino IDE with
Teensy plugin.

teensy-floppy-music/teensy-floppy-music.ino:

Plays music on the floppy drive. Standalone code that runs on the Teensy.
Compile using the Arduino IDE with
Teensy plugin.

capture-data.sh:

Executes capture-data.py with paths set up correctly. Will need modification to
run in your own environment.

capture-data.py:

Controls the floppy drive via the Teensy. Uses sigrok-cli to capture the raw
data from the floppy drive. Each separate track/head is captured to a separate
.vcd file. Note that Sigma2 support in sigrok requires a very recent version of
libsigrok; you may need to compile your own copy of libsigrok, libsigrokdecode,
sigrok-cli, and pulseview.

decoders/floppy_flux/:

Sigrok decoder to convert raw floppy drive capture to raw MFM bits.

decoders/floppy_ibm_pc/:

Sigrok decoder to convert raw MFM bits to extracted sectors.

generate-image.sh:

Executes generate-image.py with paths set up correctly. Will need modification
to run in your own environment.

generate-image.py:

Uses the decoders mentioned above to parse each captured track's data, extract
all the sectors, and create an overall floppy disk image file. The resultant
file will be exactly as if you had run: dd if=/dev/floppyN of=image.bin.

Installing decoders
========================================

The sigrok decoders have been sent to the sigrok mailing list, with the intent
that they'll be included in a future version of libsigrokdecode.

You may copy the decoder directories to, or symlink them from,
/usr/share/libsigrokdecode/decoders/, or wherever you installed a custom
version of sigrok. For example:

cd /usr/share/libsigrokdecode/decoders/
ln -s /home/swarren/git_wa/floppy-interfacing/decoders/floppy_flux
ln -s /home/swarren/git_wa/floppy-interfacing/decoders/floppy_ibm_pc

Using decoders from pulseview
========================================

- Open a .vcd file, such as data/track-t00-h0.vcd.
- Add the "Floppy Flux" decoder, and ensure its FLUX input maps to the raw flux
  data read from the floppy.
- Stack the "Floppy (IBM PC)" decoder.
- View the decoded bytes!

Testing an extracted floppy image
========================================

Once you have created image.bin, assuming it's a bootable disk, you can test it
by running: qemu-system-x86_64 -fda data/image.bin.

If the floppy contains a filesystem, you can mount it by running:

sudo losetup -f data/image.bin
losetup # search for which loop device maps your image
mount -o ro /dev/loop15 /mnt/tmp
ls -lFaR /mnt/tmp

Resources
========================================

Floppy drive connector pinout:
http://old.pinouts.ru/HD/InternalDisk_pinout.shtml

Arduino IDE:
https://www.arduino.cc/

Teensy plugin for the Arduino IDE:
https://www.pjrc.com/teensy/teensyduino.html

Sigrok:
https://sigrok.org/

ASIX Sigma2 logic analyzer:
https://www.asix.net/dbg_sigma.htm
https://sigrok.org/wiki/ASIX_SIGMA_/_SIGMA2

The inspiration for this project:
https://hackaday.com/2019/02/19/flux-engine-reads-floppies/
https://github.com/davidgiven/fluxengine
https://www.youtube.com/results?search_query=floppotron

Video of the music playing application working:
https://www.youtube.com/watch?v=6ZiQmYZQK00
