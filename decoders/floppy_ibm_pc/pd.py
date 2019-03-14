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

from abc import ABCMeta, abstractmethod
import sigrokdecode as srd

def calc_crc16(data):
    poly = 0x1021
    crc = 0xffff
    for d in data:
        d <<= 9
        for _ in range(8):
            crc <<= 1
            if (crc ^ d) & 0x10000:
                crc ^= poly
            d <<= 1
    return crc & 0xffff

class SyncDetector(object):
    def __init__(self):
        self.ss_es_hist = []
        self.bit_hist = 0

    def decode(self, ss, es, data):
        self.bit_hist <<= 1
        self.bit_hist |= data
        self.bit_hist &= 0xffff
        self.ss_es_hist.append((ss, es))
        self.ss_es_hist = self.ss_es_hist[-16:]
        return self.bit_hist == 0x4489

class ByteChunker(object):
    def __init__(self, decoder, prev_bit):
        self.d = decoder

        self.phase = 0
        self.prev_two_bits = prev_bit
        self.prev_ss_es = []
        self.bit_hist = prev_bit
        self.bit_hist_len = 0
        self.ss_es_hist = []

    def decode(self, ss, es, data):
        self.phase ^= 1

        if not self.phase:
            prev_data = (self.prev_two_bits >> 1) & 1
            prev_clk = self.prev_two_bits & 1
            expected_clk = 1 if ((prev_data == 0) and (data == 0)) else 0
            if prev_clk != expected_clk:
                self.d.put(*self.prev_ss_es, self.d.out_ann, [0, ["Err"]])
        self.prev_two_bits <<= 1
        self.prev_two_bits |= data
        self.prev_two_bits &= 3
        self.prev_ss_es = (ss, es)

        if self.phase:
            return

        self.bit_hist <<= 1
        self.bit_hist |= data
        self.bit_hist &= 0xff
        self.bit_hist_len += 1
        self.ss_es_hist.append((ss, es))
        self.ss_es_hist = self.ss_es_hist[-8:]
        if self.bit_hist_len < 8:
            return

        self.bit_hist_len = 0
        self.d.on_byte(self.bit_hist)

class StateAddressMark(object):
    def __init__(self, decoder):
        self.d = decoder

    def on_byte(self, ss, es, data):
        self.d.put(ss, es, self.d.out_ann, [1, ["%02X" % data]])
        if data == 0xFB:
            if self.d.id_size_decoded is None:
                self.d.put(ss, es, self.d.out_ann, [3, ['Data without ID']])
                return None
            self.d.put(ss, es, self.d.out_ann, [2, ['Data address mark']])
            return StateData(self.d)
        elif data == 0xFE:
            self.d.put(ss, es, self.d.out_ann, [2, ['ID address mark']])
            return StateIdTrack(self.d)
        else:
            self.d.put(ss, es, self.d.out_ann, [2, ['Error']])
            return None

class StateByteSequence(metaclass=ABCMeta):
    def __init__(self, decoder, seq_len, seq_name, next_state_class):
        self.d = decoder
        self.seq_len = seq_len
        self.seq_name = seq_name
        self.next_state_class = next_state_class
        self.count = 0
        self.data = []

    def on_byte(self, ss, es, data):
        if self.count == 0:
            self.ss = ss
        self.data.append(data)
        self.count += 1
        if self.count < self.seq_len:
            return self
        self.d.put(self.ss, es, self.d.out_ann, [2, [self.seq_name]])
        self.on_sequence(self.ss, es, self.data)
        if not self.next_state_class:
            return None
        return self.next_state_class(self.d)

    @abstractmethod
    def on_sequence(self, ss, es, data):
        pass

class StateIdTrack(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 1, 'ID Track', StateIdSide)

    def on_sequence(self, ss, es, data):
        self.d.id_track = data[0]

class StateIdSide(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 1, 'ID Side', StateIdSector)

    def on_sequence(self, ss, es, data):
        self.d.id_side = data[0]

class StateIdSector(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 1, 'ID Sector', StateIdSize)

    def on_sequence(self, ss, es, data):
        self.d.id_sector = data[0]

class StateIdSize(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 1, 'ID Size', StateIdCRC)

    def on_sequence(self, ss, es, data):
        if data[0] > 6:
            self.d.put(ss, es, self.d.out_ann, [3, ['Invalid']])
            self.next_state_class = None
            return
        self.d.id_size = data[0]
        self.d.id_size_decoded = 128 * (2 ** self.d.id_size)
        self.d.put(ss, es, self.d.out_ann, [3, [str(self.d.id_size_decoded)]])

class StateIdCRC(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 2, 'ID CRC', None)

    def on_sequence(self, ss, es, data):
        found_crc = (data[0] << 8) | data[1]
        # FIXME: We should really capture the sync/address-mark bytes rather than assuming them
        calc_crc = calc_crc16([
            0xa1, 0xa1, 0xa1, 0xfe,
            self.d.id_track,
            self.d.id_side,
            self.d.id_sector,
            self.d.id_size])
        if found_crc == calc_crc:
            self.d.put(ss, es, self.d.out_ann, [3, ['OK']])
        else:
            self.d.put(ss, es, self.d.out_ann, [3, ['Err (%x)' % calc_crc]])

class StateData(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, decoder.id_size_decoded, 'Data', StateDataCRC)

    def on_sequence(self, ss, es, data):
        self.d.sector_data = data

class StateDataCRC(StateByteSequence):
    def __init__(self, decoder):
        super().__init__(decoder, 2, 'Data CRC', None)

    def on_sequence(self, ss, es, data):
        found_crc = (data[0] << 8) | data[1]
        # FIXME: We should really capture the sync/address-mark bytes rather than assuming them
        calc_crc = calc_crc16([0xa1, 0xa1, 0xa1, 0xfb] + self.d.sector_data)
        if found_crc == calc_crc:
            self.d.put(ss, es, self.d.out_ann, [3, ['OK']])
        else:
            self.d.put(ss, es, self.d.out_ann, [3, ['Err (%x)' % calc_crc]])
        chs_data = (self.d.id_track, self.d.id_side, self.d.id_sector, bytes(self.d.sector_data), found_crc, calc_crc)
        chs_data_repr = (repr(chs_data) + "\n").encode('UTF-8')
        self.d.put(ss, es, self.d.out_python, chs_data)
        self.d.put(ss, es, self.d.out_binary, [0, chs_data_repr])

class Decoder(srd.Decoder):
    api_version = 3
    id = 'floppy_ibm_pc'
    name = 'Floppy (IBM PC)'
    longname = 'IBM PC Floppy disk MFM'
    desc = 'IBM PC Floppy disk MFM'
    license = 'gplv2+'
    inputs = ['mfm_raw']
    outputs = ['floppy_sectors']
    annotations = (
        ('mfm_err', 'MFM encoding errors'),
        ('bytes', 'Raw bytes'),
        ('labels', 'Labels'),
        ('labels2', 'Labels 2'),
    )
    annotation_rows = (
        ('mfm_err', 'MFM encoding errors', (0, )),
        ('bytes', 'Raw bytes', (1, )),
        ('labels', 'Labels', (2, )),
        ('labels2', 'Labels 2', (3, )),
    )
    binary = (
        ('sectors', 'Sector data'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.sync_detector = SyncDetector()
        self.state = None
        self.id_size_decoded = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def decode(self, ss, es, data):
        if self.sync_detector.decode(ss, es, data):
            self.put(
                self.sync_detector.ss_es_hist[-6][0],
                self.sync_detector.ss_es_hist[-6][1],
                self.out_ann,
                [0, ["Err"]])
            self.put(
                self.sync_detector.ss_es_hist[1][0],
                self.sync_detector.ss_es_hist[-1][1],
                self.out_ann,
                [1, ["~A1"]])
            self.put(
                self.sync_detector.ss_es_hist[1][0],
                self.sync_detector.ss_es_hist[-1][1],
                self.out_ann,
                [2, ['A1 sync']])
            self.chunker = ByteChunker(self, 1)
            self.state = StateAddressMark(self)
        elif self.state:
            self.chunker.decode(ss, es, data)

    def on_byte(self, data):
        ss = self.chunker.ss_es_hist[0][0]
        es = self.chunker.ss_es_hist[-1][1]
        self.put(ss, es, self.out_ann, [1, ["%02x" % data]])
        self.state = self.state.on_byte(ss, es, data)
