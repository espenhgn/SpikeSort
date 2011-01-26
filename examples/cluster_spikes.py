#!/usr/bin/env python
#coding=utf-8

import numpy as np

import os, sys

sys.path.append("/Users/bartosz/SVN/personal/Libraries")

import spike_sort as sort
import spike_sort.io.bakerlab
import spike_sort.io.hdf5
import spike_sort.ui.manual_sort
from utils import create_new_dir

DATAPATH = "../data" 

if __name__ == "__main__":
    #main
    h5_fname = os.path.join(DATAPATH, "sample.h5")
    dataset = "/Gollum/s5gollum01/el3/cell3"
    out_dir = create_new_dir("Data/")
    sp_win = [-0.2, 0.8]

    spt_fname = "missed_rest"

    #spt = sort.io.bakerlab.read_spt(out_dir, spt_fname)
    sp = sort.io.hdf5.read_sp(h5_fname, dataset)
    #spt = sort.io.hdf5.read_spt(h5_fname, dataset)
    spt = sort.extract.detect_spikes(sp, 'auto')
    
    spt = sort.extract.align_spikes(sp, spt, sp_win, type="max", resample=10)
    sp_waves = sort.extract.extract_spikes(sp, spt, sp_win)

    features = sort.features.combine(
            (
            sort.features.fetSpIdx(sp_waves),
            sort.features.fetP2P(sp_waves),
            sort.features.fetPCs(sp_waves)),
            normalize=True)


    clust_idx = sort.ui.manual_sort.show(features, sp_waves, [1,2])

    clust, rest = sort.ui.manual_sort.cluster_spt(spt, clust_idx)

    if len(clust)>0:
        print "Exporting."
        sort.io.bakerlab.write_spt(clust, out_dir, spt_fname+"_clus")
        sort.io.bakerlab.write_spt(rest, out_dir, spt_fname+"_rest")

    else: 
        print "Exiting."
