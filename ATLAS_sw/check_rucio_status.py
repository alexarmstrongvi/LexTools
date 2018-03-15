#!/usr/bin/env python
"""
===============================================================================
Determines whether samples exist on rucio and, if so,
gathers some diagnositic information
Examples
    python check_rucio_status.py file_with_full_sample_names.txt
Licence:
    Copyright: (C) <Mar 15, 2018>; University of California, Irvine 
===============================================================================

"""

import sys, os, traceback, argparse
import time
import subprocess
import python_tools as tools

################################################################################
def main ():
    """ Main Function """ 
    print '\n\n ====== Running check_rucio_status.py ======\n'
    
    # Initial setup and checks
    global args
    if os.path.exists(args.output):
        print "Output file already exists: ", args.output
        print "\tConsider deleting first or changing output name"
        sys.exit()
    check_environment()
    
    # Extract sample names
    samples = []
    scope_flag = False
    with open(args.samples_file, 'r') as ifile:
        for line in ifile:
            line = line.strip()
            if not accept_line(line): continue
            # Add scope if missing
            if ':' not in line:
                scope_flag = True
                line = line.split('.')[0]+":"+line
            samples.append(line)
    if scope_flag:
        print "WARNING :: Some samples do not contain scope."
        print "\t Attempting to add scope automatically."
    if len(samples) != len(set(samples)):
        print "WARNING :: Input file likely contains duplicates"
    if args.dryrun:
        print "Samples to be processed:"
        for sample in samples:
            print '\t'+sample 
        sys.exit()

    # Create output file
    ofile = open(args.output,'w')
    
    # Identify samples existing on the Grid
    header = '===== Information for samples =====\n'
    ofile.write(header) 
    ofile.write('\tSample name\n')
    ofile.write('\t- File information\n')
    ofile.write('\t- Replica information -> site (files found / files expected)\n')
    ofile.write(len(header)*'='+'\n')

    missing_samples = set()
    nsamples = len(samples)
    print "Checking if samples exist"
    for ii, sample in enumerate(samples):
        print "\t[%d/%d] %s"%(ii, nsamples, sample)
        if not rucio_file_exists(sample):
            print "\t\t SAMPLE NOT FOUND"
            missing_samples.add(sample)
            continue
        
        ofile.write('SAMPLE: %s\n'%sample)
        ofile.write(write_file_info(sample))
        ofile.write(write_replica_info(sample))

    # Write out files that were not found by rucio ls
    header = '\n\n===== Files not found on rucio =====\n'
    ofile.write(header)
    for sample in missing_samples:
        ofile.write('%s\n'%sample)
    ofile.write(len(header)*'='+'\n')

    # Clean up
    ofile.close()
    print "Output written to %s\n"%args.output

################################################################################
# FUNCTIONS
def check_environment():
    """ Check if the shell environment is setup as expected """
    tools.rucio_is_setup()
    tools.grid_proxy_setup()

def accept_line(line, search_exp=None):
    """ Check if line grabbed from a file should be used """  
    if not line:
        return False
    if line.startswith('#'):
        return False
    if search_exp and search_exp not in line:
        return False
    if not tools.get_dsid_from_sample(line):
        return False
    return True

def rucio_file_exists(sample):
    """ Check if `rucio ls` returns the sample"""

    # Check if sample name contains wildcards
    if '*' in sample or '?' in sample:
        print "Attempting wildcard search with sample: ", sample
        print "\tUse exact file name"
        sys.exit()

    # Get rucio ls output
    rucio_cmd = 'rucio ls ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)

    # Check rucio ls output
    return True if any(sample in x for x in rucio_output) else False

def write_file_info(sample):
    """ Add file information from rucio list-files"""

    # Get rucio list-files output
    rucio_cmd = 'rucio list-files ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)

    info_to_write = '\t\t'
    for line in rucio_output:
        if 'Total' not in line: continue
        info = line.strip()[len('Total '):]
        info_to_write += "%s, "%info 
    
    # remove trailing comma and add newline
    info_to_write = info_to_write[:-2] + '\n'    
    
    return info_to_write

def write_replica_info(sample):
    """ Add dataset replica information from rucio list-dataset-replicas"""

    # Get rucio list-files output
    rucio_cmd = 'rucio list-dataset-replicas ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)

    info_to_write = '\t\t'
    lines_to_skip = [0, 1, 2, 3, 4, len(rucio_output)-1]
    for line_num, line in enumerate(rucio_output):
        line = line.strip()
        if line_num in lines_to_skip: continue
        RSE_site = line.split()[1]
        files_found = line.split()[3]
        files_expected = line.split()[5]
        info_to_write += "%s (%s/%s), "%(RSE_site, files_found, files_expected) 

    # remove trailing comma and add newline
    info_to_write = info_to_write[:-2] + '\n'    
    return info_to_write
################################################################################
if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('samples_file', 
                            help='File containing full sample names')
        parser.add_argument('-o', '--output', 
                            default='sample_rucio_status.txt', 
                            help='Name of output file for diagnostic info')
        parser.add_argument('--dryrun', 
                            action='store_true', default=False, 
                            help='Only printout the samples that will be processed')
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
