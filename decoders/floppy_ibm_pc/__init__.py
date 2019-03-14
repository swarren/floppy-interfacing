##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Stephen Warren <s-sigrok@wwwdotorg.org>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

'''
IBM PC floppy disks store many sectors of 512 bytes, each located in a specific
track/cylinder, written by a certain head or side of the disk. Each sector is
encoded as a sequence of (address mark, sector data), where the address mark is
represented as the series of fields (sync bytes, address mark, cylinder number,
head number, sector number, sector size, CRC) and sector data is represented as
the series of fields (sync bytes, address mark, sector data, CRC). Finally, the
data is MFM encoded and written to the disk as a series of flux transitions. 

This decoder extracts and annotates all the data structures mentioned above, and
additionally provides Python output representating each sector's address and
data fields. This output is sent to both the Python object output stream for use
by further protocol decoders, and to the binary output stream (which provides a
textual representation of the Python data) to allow applications to stream data
out from sigrok-cli -B.
'''

from .pd import Decoder
