#!/usr/bin/env python
"""
================================================================================
Check if two root files containing hists and/or flat ttrees are identical
Examples
    ./rootFilesAreIdentical.py file1.root file2.root

Author:
    Alex Armstrong <alarmstr@cern.ch>
================================================================================
"""

import sys, os, traceback, argparse
import time
import subprocess
import logging
import ROOT as r
from tabulate import tabulate
from collections import OrderedDict

# User Argument defaults and help information
_help_ifile1_path = '1st input file for comparison'
_help_ifile2_path = '2nd input file for comparison'
_df_debug_level = "WARNING"
_help_debug_level = "logger message level [default: %s]" % _df_debug_level

log = logging.getLogger(__name__)

################################################################################
def main ():
    """ Main Function """

    global args
    check_environment()
    check_inputs(args)

    ifile1 = r.TFile(args.ifile1_path, "READ")
    ifile2 = r.TFile(args.ifile2_path, "READ")

    log.info("Comparing ROOT files %s and %s" % (ifile1.GetName(), ifile2.GetName()) )
    
    ############################################################################
    keys1 = get_set_of_root_keys(ifile1)
    keys2 = get_set_of_root_keys(ifile2)
    if keys1 != keys2:
        log.info("ROOT files do not contain the same keys") 
        log_name_diff(keys1, keys2)
        ifile1.Close()
        ifile2.Close()
        os._exit(3)
    else:
        keys = keys1

    ############################################################################
    pass_checks = False
    for key in keys:
        log.debug("Comparing key = %s" % key)
        obj1 = ifile1.Get(key)
        obj2 = ifile2.Get(key)
        
        ########################################################################
        if both_of_type(obj1, obj2, r.TH1):
            hist_name, hist1, hist2 = key, obj1, obj2
            
            ####################################################################
            if not histograms_are_identicial(hist1, hist2):
                log.info("The TH1 %s is different between files" % (hist_name))
                log_hist_diff(hist1, hist2, ifile1.GetName(), ifile2.GetName())
                break
        
        elif both_of_type(obj1, obj2, r.TTree):
            tree_name, tree1, tree2 = key, obj1, obj2
            
            ####################################################################
            n_entries1 = tree1.GetEntries()
            n_entries2 = tree2.GetEntries()
            if n_entries1 != n_entries2:
                log.info("Differing number of entries for TTree %s" % (tree_name))
                log.debug("In %s, there are %d entries" % (ifile1.GetName(), n_entries1))
                log.debug("In %s, there are %d entries" % (ifile2.GetName(), n_entries1))
                break
            else:
                n_entries = n_entries1

            ####################################################################
            branches1 = get_set_of_ttree_branch_names(tree1)
            branches2 = get_set_of_ttree_branch_names(tree2)
            if branches1 != branches2:
                log.info("Differing branches found for TTree %s" % (tree_name))
                log_name_diff(branches1, branches2, ifile1.GetName(), ifile2.GetName())
                break
            else:
                branches = branches1

            ####################################################################
            if not ttree_is_flat(tree1):
                log.info("%s from %s is not a flat tree" % (tree_name, ifile1.GetName()))
                break
            elif not ttree_is_flat(tree2):
                log.info("%s from %s is not a flat tree" % (tree_name, ifile2.GetName()))
                break

            ####################################################################
            if not ttrees_are_identicial(tree1, tree2, branches, n_entries):
                log.info("The TTree %s is different between files" % (tree_name))
                break
        
        else:
            log.warning("Unrecognized or differing object types for key = %s" % (key) )
            log.warning("In %s, this is of type %s" % (ifile1.GetName(), type(obj1)))
            log.warning("In %s, this is of type %s" % (ifile2.GetName(), type(obj1)))
            break

    else:
        pass_checks = True

    ############################################################################
    if pass_checks:
        log.info("ROOT files are identical")
    elif not pass_checks:
        log.info("ROOT files are not identical")
        os._exit(3)

################################################################################
# FUNCTIONS
def check_inputs(args):
    """ Check the input arguments are as expected """

    for f in [args.ifile1_path, args.ifile2_path]:
        if not os.path.exists(f):
            log.error("ERROR :: Cannot find input file: %s" % f) 
            os._exit(3)

def check_environment():
    """ Check if the shell environment is setup as expected """
    python_ver = sys.version_info[0] + 0.1*sys.version_info[1]
    assert python_ver >= 2.7, ("Running old version of python\n", sys.version)

def get_set_of_root_keys(root_file):
    return set([k.GetName() for k in root_file.GetListOfKeys()])

def get_set_of_ttree_branch_names(ttree):
    return set([b.GetName() for b in ttree.GetListOfBranches()])

def both_of_type(x, y, t):
    return isinstance(x, t) and isinstance(y, t)

def histograms_are_identicial(h1, h2):
    return hist_to_str(h1) == hist_to_str(h2)

def hist_to_str(hist, tablefmt='psql'):
    hist_dict_bins = hist_to_dict(hist, add_overflow=True, bin_range_keys=False)
    hist_dict_range = hist_to_dict(hist, add_overflow=True, bin_range_keys=True)
    if not hist_dict_bins or not hist_dict_range: return ""

    if isinstance(hist, r.TH3):
        h_string = ""
        for z_bin, z_range in zip(hist_dict_bins, hist_dict_range):
            headers = [""]
            table = []
            h_string += "(%s) %s\n" % (z_bin, z_range)
            # Fill headers and row lables
            if not table:
                for y_bin, y_range in zip(hist_dict_bins[z_bin], hist_dict_range[z_range]):
                    table.append(["(%s) %s" % (y_bin, y_range)])
                    for x_bin, x_range in zip(hist_dict_bins[z_bin][y_bin], hist_dict_range[z_range][y_range]):
                        header = "(%s) %s" % (x_bin, x_range)
                        if header not in headers: headers.append(header)

            # Fill table with values
            for row, (y_bin, y_range) in enumerate(zip(hist_dict_bins[z_bin], hist_dict_range[z_range])):
                for x_bin, x_range in zip(hist_dict_bins[z_bin][y_bin], hist_dict_range[z_range][y_range]):
                    table[row].append(hist_dict_bins[z_bin][y_bin][x_bin])
            h_string += tabulate(table, headers=headers, tablefmt='psql')        
            h_string += '\n\n'
    elif isinstance(hist, r.TH2):
        headers = [""]
        table = []
        for x_bin, x_range in zip(hist_dict_bins, hist_dict_range):
            headers.append("(%s) %s" % (x_bin, x_range))
            if not table:
                # Fill first column of table with y-labels
                for y_bin, y_range in zip(hist_dict_bins[x_bin], hist_dict_range[x_range]):
                    table.append(["(%s) %s" % (y_bin, y_range)])
            for row, (y_bin, y_range) in enumerate(zip(hist_dict_bins[x_bin], hist_dict_range[x_range])):
                table[row].append(hist_dict_bins[x_bin][y_bin])
        h_string = tabulate(table, headers=headers, tablefmt=tablefmt)        
    elif isinstance(hist, r.TH1):
        headers = []
        row = []
        for x_bin, x_range in zip(hist_dict_bins, hist_dict_range):
            headers.append("(%s) %s" % (x_bin, x_range))
            row.append(hist_dict_bins[x_bin])
        h_string = tabulate([row], headers=headers, tablefmt=tablefmt)        
    return h_string

def hist_to_dict(hist, add_overflow=False, bin_range_keys=False):
    # Returns a dict of the form dict[xbin][ybin] = bin value
    # Options to include overflow and underflow bins or use
    # bin range (e.g. "1.30 - 2.41"). Precision is currently hard coded 
    if isinstance(hist, r.TH3):
        h_dict = OrderedDict()
        xaxis = hist.GetXaxis()
        yaxis = hist.GetYaxis()
        zaxis = hist.GetZaxis()
        nxbins = xaxis.GetNbins()+1
        nybins = yaxis.GetNbins()+1
        nzbins = zaxis.GetNbins()+1
        for xbin in range(0, nxbins + 1):
            for ybin in range(0, nybins + 1):
                for zbin in range(0, nzbins + 1):
                    if bin_range_keys:
                        xbin_low = xaxis.GetBinLowEdge(xbin)
                        xbin_high = xaxis.GetBinUpEdge(xbin)
                        ybin_low = yaxis.GetBinLowEdge(ybin)
                        ybin_high = yaxis.GetBinUpEdge(ybin)
                        zbin_low = zaxis.GetBinLowEdge(zbin)
                        zbin_high = zaxis.GetBinUpEdge(zbin)
                        if xbin == nxbins:
                            xkey = "> %.5f" % xbin_low 
                        elif xbin == 0:
                            xkey = "< %.5f" % xbin_high 
                        else:
                            xkey = "%.5f-%.5f" % (xbin_low, xbin_high) 
                        if ybin == nybins:
                            ykey = "> %.5f" % ybin_low 
                        elif ybin == 0:
                            ykey = "< %.5f" % ybin_high 
                        else:
                            ykey = "%.5f-%.5f" % (ybin_low, ybin_high) 
                        if zbin == nzbins:
                            zkey = "> %.5f" % zbin_low 
                        elif zbin == 0:
                            zkey = "< %.5f" % zbin_high 
                        else:
                            zkey = "%.5f-%.5f" % (zbin_low, zbin_high) 
                    else:
                        xkey = str(xbin)
                        ykey = str(ybin)
                        zkey = str(zbin)
                    bin_value = hist.GetBinContent(xbin, ybin, zbin)
                    underflow = (xbin == 0) or (ybin == 0) or (zbin == 0)
                    overflow = (xbin == nxbins) or (ybin == nybins) or (zbin == nzbins)
                    if (underflow or overflow) and not add_overflow: continue
                    if zkey not in h_dict: h_dict[zkey] = OrderedDict()
                    if ykey not in h_dict[zkey]: h_dict[zkey][ykey] = OrderedDict()
                    h_dict[zkey][ykey][xkey] = bin_value
    elif isinstance(hist, r.TH2):
        h_dict = OrderedDict()
        xaxis = hist.GetXaxis()
        yaxis = hist.GetYaxis()
        nxbins = xaxis.GetNbins()+1
        nybins = yaxis.GetNbins()+1
        for xbin in range(0, nxbins + 1):
            for ybin in range(0, nybins + 1):
                if bin_range_keys:
                    xbin_low = xaxis.GetBinLowEdge(xbin)
                    xbin_high = xaxis.GetBinUpEdge(xbin)
                    ybin_low = yaxis.GetBinLowEdge(ybin)
                    ybin_high = yaxis.GetBinUpEdge(ybin)
                    if xbin == nxbins:
                        xkey = "> %.5f" % xbin_low 
                    elif xbin == 0:
                        xkey = "< %.5f" % xbin_high 
                    else:
                        xkey = "%.5f-%.5f" % (xbin_low, xbin_high) 
                    if ybin == nybins:
                        ykey = "> %.5f" % ybin_low 
                    elif ybin == 0:
                        ykey = "< %.5f" % ybin_high 
                    else:
                        ykey = "%.5f-%.5f" % (ybin_low, ybin_high) 
                else:
                    xkey = str(xbin)
                    ykey = str(ybin)
                bin_value = hist.GetBinContent(xbin, ybin)
                underflow = (xbin == 0) or (ybin == 0)
                overflow = (xbin == nxbins) or (ybin == nybins)
                if (underflow or overflow) and not add_overflow: continue
                if xkey not in h_dict: h_dict[xkey] = OrderedDict()
                h_dict[xkey][ykey] = bin_value
    elif isinstance(hist, r.TH1):
        h_dict = OrderedDict()
        xaxis = hist.GetXaxis()
        nxbins = xaxis.GetNbins()+1
        for xbin in range(0, nxbins + 1):
            underflow = (xbin == 0)
            overflow = (xbin == nxbins)
            if bin_range_keys:
                xbin_low = xaxis.GetBinLowEdge(xbin)
                xbin_high = xaxis.GetBinUpEdge(xbin)
                if overflow:
                    key = "> %.5f" % xbin_low 
                elif underflow:
                    key = "< %.5f" % xbin_high 
                else:
                    key = "%.5f-%.5f" % (xbin_low, xbin_high)
            else:
                key = str(xbin)
            bin_value = hist.GetBinContent(xbin)
            if (underflow or overflow) and not add_overflow: continue
            h_dict[key] = bin_value
    else:
        log.warning("Histogram type not recognized: %s" % type(hist))
    return h_dict

def ttree_is_flat(t):
    branch_names = get_set_of_ttree_branch_names(t)
    for bn in branch_names:
        exec("br_type = type(t.%s)" % bn)
        if br_type != int and br_type != float:
            log.warning("Branch %s of ttree %s is of non-primitive type %s" % (bn, t.GetName(), br_type))
            return False
    return True

def ttrees_are_identicial(t1, t2, branch_names, n_entries):
    #for ii, (entry1, entry2) in enumerate(zip(t1, t2)):
    for ii, entry1 in enumerate(t1):
        for jj, entry2 in enumerate(t2):
            if jj < ii: continue
            if jj > ii: break 
            for bn in branch_names:
                exec("v1 = entry1.%s" % bn)
                exec("v2 = entry2.%s" % bn)
                if not close_enough(v1, v2, 1e-06):
                    # precision of log msg should similar to close_enough function
                    log.debug("Branch %s differs for row %d: %.7f vs %.7f" % (bn, ii, v1, v2))
                    return False
                else:
                    log.debug("Branch %s is the same for row %d: %.7f vs %.7f" % (bn, ii, v1, v2))
    return True

def close_enough(a, b, rel_tol=1e-12, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def log_name_diff(name_set1, name_set2, label1 = "input 1", label2 = "input 2"):
    log.debug("Names unique to %s:" % label1 )
    log.debug(">> " + ", ".join(name_set1 - name_set2))
    log.debug("Names unique to %s:" % label2 )
    log.debug(">> " + ", ".join(name_set2 - name_set1))

def log_hist_diff(h1, h2, label1 = "input 1", label2 = "input 2"):
    log.debug("Histogram from %s:" % label1 )
    log.debug("\n" + hist_to_str(h1))
    log.debug("Histogram from %s:" % label2 )
    log.debug("\n" + hist_to_str(h2))

################################################################################

def get_args():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('ifile1_path',
                        help=_help_ifile1_path)
    parser.add_argument('ifile2_path',
                        help=_help_ifile2_path)
    parser.add_argument('-d', '--debug-level',
                        help=_help_debug_level,
                        default=_df_debug_level)
    args = parser.parse_args()
    return args

################################################################################
# Run main when not imported
if __name__ == '__main__':
    try:
        start_time = time.time()
        # TODO: Add ability to check standard input so things can be piped
        args = get_args()
        logging.basicConfig(
                format='%(levelname)10s :: %(message)s',
                stream=sys.stdout,
                level=args.debug_level)
        log.debug('>'*40)
        log.debug('Running {}...'.format(os.path.basename(__file__)))
        main()
        time = (time.time() - start_time)
        log.debug('TOTAL TIME: %fs'%time,)
        log.debug('')
        log.debug('<'*40)
    except KeyboardInterrupt, e: # Ctrl-C
        log.exception('Program ended by keyboard interruption')
        raise e
    except SystemExit, e: # sys.exit()
        pass
    except Exception, e:
        log.critical('ERROR, UNEXPECTED EXCEPTION')
        log.exception(str(e))
        traceback.print_exc()
        os._exit(1)

