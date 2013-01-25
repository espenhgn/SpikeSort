import os

import matplotlib
matplotlib.use("TkAgg")
matplotlib.interactive(True)

from spike_beans import components, base
from spike_sort.io import neo_filters

####################################
# Adjust these fields for your needs

sp_win = [-0.6, 0.8]

path = '/media/Data/File_axon_1.abf'

io = neo_filters.NeoSource(path)

base.register("SignalSource", io)
base.register("SpikeMarkerSource",
                      components.SpikeDetector(contact=0, 
                                               thresh='auto',
                                               type='max',
                                               sp_win=sp_win,
                                               resample=1,
                                               align=True))
base.register("SpikeSource", components.SpikeExtractor(sp_win=sp_win))

browser = components.SpikeBrowser()

browser.show()
