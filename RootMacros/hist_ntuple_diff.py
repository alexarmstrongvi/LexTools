#!/bin/usr/env python
import os

old_file_name = '%s/old_sample.root' % (os.getcwd())
new_file_name = '%s/new_sample.root' % (os.getcwd())
ofile_name = "hist_diff.root"

import PlotTools.plot_utils as pu

import ROOT
def main():
    f_old = ROOT.TFile(old_file_name,"READ") 
    f_new = ROOT.TFile(new_file_name,"READ") 

    f_new_keys = set([k.GetName() for k in f_new.GetListOfKeys()])
    f_old_keys = set([k.GetName() for k in f_old.GetListOfKeys()])
    
    shared_keys = f_new_keys & f_old_keys
    only_new_keys = f_new_keys - f_old_keys
    only_old_keys = f_old_keys - f_new_keys
    if only_new_keys: print "INFO :: Unique new keys = ", only_new_keys
    if only_old_keys: print "INFO :: Unique old keys = ", only_old_keys
    ofile = ROOT.TFile(ofile_name,'recreate')
    print "\nComparing Histograms"
    print "Number of shared keys =", len(shared_keys)
    disagree_flag = False
    for key in shared_keys:
        new_hist = f_new.Get(key)
        old_hist = f_old.Get(key)
        if not isinstance(new_hist, ROOT.TH1F) or not isinstance(old_hist, ROOT.TH1F):
            continue
        if hists_are_diff(new_hist, old_hist):
            if False:
                output_hist = new_hist.Clone("%s_subtract"%key)
                output_hist.Add(old_hist, -1)
                output_hist.Write()
                output_hist = new_hist.Clone("%s_ratio"%key)
                output_hist.Divide(old_hist)
                output_hist.Write()
            elif True:
                c1 = ROOT.TCanvas("c_%s"%key,"",800,600)
                old_hist.SetLineColor(ROOT.kBlue)
                old_hist.Draw()
                new_hist.SetLineColor(ROOT.kRed)
                new_hist.Draw("SAME")
                c1.Write()

            print "Disagree: %s" % key
            disagree_flag = True
    if not disagree_flag:
        print "All keys agree"
    return 0

def hists_are_diff(hist1, hist2):
    return (pu.print_hist(hist1) != pu.print_hist(hist2))


if __name__ == '__main__':
    main()
