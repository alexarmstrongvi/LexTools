#!/usr/bin/env python
"""
================================================================================
Downloads datasets from a list and stores summary information
Examples
    ./download_rucio_datasets.py file.txt

Author: 
    Alex Armstrong <alarmstr@cern.ch>
TODO: Licence:
    Copyright: (C) April 22, 2018; University of California, Irvine 
================================================================================
"""

import sys, os, traceback, argparse
import time
import re
import pyToolsBasic as tools

################################################################################
def main ():
    """ Main Function """
    
    global args

    # Sanity check
    if not os.path.exists(args.input_datasets):
        print "ERROR :: Input file not found:", args.input_datasets
        sys.exit()
    if os.path.exists(args.output) and not args.append:
        print "ERROR :: Output file already exists:", args.output
        print "\tDelete it, change output name, or use '--append' option"
        sys.exit()
    if not os.path.exists(args.output) and args.append:
        print "ERROR :: Cannot append. Output file doesn't exist:", args.output
        sys.exit()
    if not os.path.isdir(args.sample_dir):
        print "ERROR :: Cannot found sample directory", args.sample_dir
        sys.exit()
    check_environment()
    print "All checks cleared"

    # Initilize
    print "\n===== BEGIN ====="
    not_found_dids = []
    successful_sites = set()
    bad_sites = set()
    incomplete_dids = []
    local_dids = []
    no_progress_dids = []
    failed_dids = []
    successful_downloads = 0
    
    if not args.dry_run:
        write_or_append = 'a' if args.append else 'w'
        ofile = open(args.output, write_or_append)
        ofile.write("#"*80+"\n")
        ofile.write("RUCIO OUTPUT")

    # Download each dataset
    ifile = open(args.input_datasets,'r')
    n_datasets = 0
    for dataset in ifile:
        if not dataset.strip() or dataset.startswith("#"): continue
        n_datasets += 1
    ifile.seek(0)
    print "Downloading datasets:"
    count = 0
    for dataset in ifile:
        dataset = dataset.strip()
        if not dataset or dataset.startswith("#"): continue
        count += 1

        # Run rucio command
        rucio_cmd = 'rucio get %s --ndownloader 5 --dir %s'%(dataset, args.sample_dir)
        progress_str = "[%d/%d] %s"%(count,n_datasets, dataset)
        print progress_str
        if args.dry_run: continue
        ofile.write("\n%s\n"%progress_str)
        ofile.write("Running >> %s\n"%rucio_cmd)
         
        rucio_output = tools.get_cmd_output(rucio_cmd, print_output=True)
        
        # Write output and extract relevant information
        total = n_downloaded = n_local = n_failed = 0
        for line in rucio_output:
            line = tools.strip_ansi_escape(line)
            
            if 'Failed to get did info' in line:
                not_found_dids.append(dataset)
                break
            elif 'successfully downloaded from' in line:
                successful_sites.add(line.split()[-1].strip())
            elif 'is blacklisted for reading' in line:
                bad_sites.add(line.split(':')[-1].split()[0].strip())
            elif 'Total files' in line:
                total = int(line.split()[-1].strip())
            elif 'Downloaded files' in line:
                n_downloaded = int(line.split()[-1].strip())
            elif 'Files already found locally' in line:
                n_local = int(line.split()[-1].strip())
            elif 'Files that cannot be downloaded' in line:
                n_failed = int(line.split()[-1].strip())

            if not args.save_all and "INFO" in line: continue
            ofile.write("\t%s\n"%line.strip())
        
        # Determine status of download
        if not total: continue
        elif total == n_local: local_dids.append(dataset)
        elif total == n_failed: failed_dids.append(dataset)
        elif total == n_local + n_downloaded: successful_downloads += 1
        elif total == n_local + n_failed: no_progress_dids.append(dataset)
        elif n_downloaded and n_failed: incomplete_dids.append(dataset)
        else:
            print "Unexpected info from rucio (2)"
            print "%d != %d + %d + %d"%(total, n_downloaded, n_local, n_failed)
    
    ifile.close()
    if args.dry_run:
        print "End of dry run"
        return

    # Print summary information
    summary_str = "\n\n"+"#"*80+"\n"
    summary_str += "Dataset Download Summary\n"
    summary_str += " - %d total datasets\n"%(n_datasets)
    summary_str += " - %d (%6.2f%%) downloads successful\n"%(
        successful_downloads, successful_downloads/float(n_datasets)*100)
    summary_str += " - %d (%6.2f%%) downloads incomplete\n"%(
        len(incomplete_dids),len(incomplete_dids)/float(n_datasets)*100)
    summary_str += " - %d (%6.2f%%) downloads already local\n"%(
        len(local_dids),len(local_dids)/float(n_datasets)*100)
    summary_str += " - %d (%6.2f%%) downloads added nothing new\n"%(
        len(no_progress_dids),len(no_progress_dids)/float(n_datasets)*100)
    summary_str += " - %d (%6.2f%%) downloads with no success\n"%(
        len(failed_dids),len(failed_dids)/float(n_datasets)*100)
    summary_str += " - %d (%6.2f%%) datasets not found\n"%(
        len(not_found_dids),len(not_found_dids)/float(n_datasets)*100)
    
    if successful_sites: summary_str += "\nSites with successful downloads:\n"
    for rse in successful_sites: summary_str += " >> %s\n"%rse
    if bad_sites: summary_str += "\nSites with failed downloads:\n"
    for rse in bad_sites: summary_str += " >> %s\n"%rse
    
    if not_found_dids: summary_str += "\nDIDs not found on rucio:\n"
    for did in not_found_dids: summary_str += " >> %s\n"%did
    if incomplete_dids: summary_str += "\nIncomplete download DIDs:\n"
    for did in incomplete_dids: summary_str += " >> %s\n"%did
    if local_dids: summary_str += "\nDIDs already stored locally:\n"
    for did in local_dids: summary_str += " >> %s\n"%did
    if no_progress_dids: summary_str += "\nDIDs adding nothing new to :\n"
    for did in no_progress_dids: summary_str += " >> %s\n"%did
    if failed_dids: summary_str += "\nDIDs with no success:\n"
    for did in failed_dids: summary_str += " >> %s\n"%did
    #ofile.seek(0)
    ofile.write(summary_str)
    ofile.close()

    print "Output written to", args.output
    print "Samples downloaded to", args.sample_dir
    print "===== COMPLETED ====="

################################################################################
# FUNCTIONS
def check_environment():
    """ Check if the shell environment is setup as expected """
    if not tools.grid_proxy_setup(): sys.exit()
    if not tools.rucio_is_setup(): sys.exit()


################################################################################
# Run main when not imported
if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('input_datasets', 
                            help='text file with datasets to download')
        parser.add_argument('-o', '--output', 
                            default='info_rucio_dwnld.txt', 
                            help='output file name')
        parser.add_argument('-d', '--sample_dir', 
                            default='./', 
                            help='directory for storing downloaded samples')
        parser.add_argument('--append',
                            action='store_true', default=False,
                            help='append output to output file')
        parser.add_argument('--save_all',
                            action='store_true', default=False,
                            help='store output from download threads')
        parser.add_argument('--dry_run',
                            action='store_true', default=False,
                            help='run without actually downloading samples')
        parser.add_argument('-v', '--verbose', 
                            action='store_true', default=False, 
                            help='verbose output')
        args = parser.parse_args()
        if args.verbose: 
            print '>'*40
            print 'Running {}...'.format(os.path.basename(__file__))
            print time.asctime()
        main()
        if args.verbose: 
            print time.asctime()
            time = (time.time() - start_time)
            print 'TOTAL TIME: %fs'%time,
            print ''
            print '<'*40
    except KeyboardInterrupt, e: # Ctrl-C
        print 'Program ended by keyboard interruption'
        raise e
    except SystemExit, e: # sys.exit()
        print 'Program ended by system exit'
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)

