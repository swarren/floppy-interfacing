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

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'floppy_flux'
    name = 'Floppy Flux'
    longname = 'Floppy magnetic flux transitions'
    desc = 'Floppy disk magnetic flux transitions to MFM'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['mfm_raw']
    channels = (
        {'id': 'flux', 'name': 'FLUX', 'desc': 'Flux pulses'},
    )
    options = (
        {'id': 'frequency', 'desc': 'Bit frequency', 'default': 1000000},
    )
    annotations = (
        ('bits', 'Raw bits'),
        ('labels', 'Labels'),
    )
    annotation_rows = (
        ('bits', 'Raw bits', (0, )),
        ('labels', 'Labels', (1, )),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.samples_per_tick = int(self.samplerate / float(self.options['frequency']))

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def decode(self):
        self.wait({0: 'f'})
        prev_edge = self.samplenum
        while True:
            self.wait({0: 'f'})
            this_edge = self.samplenum
            periods = int(round((this_edge - prev_edge) / self.samples_per_tick))
            start = prev_edge
            for period in range(periods):
                end = min(start + self.samples_per_tick, this_edge)
                self.put(start, end, self.out_ann, [1, ['period', ]])
                val = 1 if (period == 0) else 0
                self.put(start, end, self.out_ann, [0, [str(val), ]])
                self.put(start, end, self.out_python, val)
                start = end
            prev_edge = this_edge
