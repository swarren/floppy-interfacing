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
Many floppy disk drives emit a negative pulse whenever there is a change in
magnetic flux under the disk head. Each time unit either contains or does not
contain a pulse (or flux transition). This yields a series of 1 and 0 bits.

This decoder extracts series of (FM-/MFM-encoded) bits from the series of flux
transitions.

Further decoders may interpret this bit series as FM or MFM encoded data, and
further derive the encoded data.
'''

from .pd import Decoder
