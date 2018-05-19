#!/usr/bin/env python
"""
================================================================================

get_fax_link_samples.py

Creates txt file of fax links for all files in each of the provided datasets

In cases where there are duplicates files on multiple sites, an attempt is made
to automatically select a prefered site by picking sites that have the most
files for the sample in question. In these cases, it is probably better to manually 
input the preferred site using the --rse_sites option where the order of sites 
provided is treated as the preference for sites. 

Examples:
    Simple use cases:

    >> get_fax_link_samples.py -f file_with_DIDs.txt
    >> get_fax_link_samples.py -i DID1 DID2 ...

    Using the options:

    - Getting links for a specific site and checking for missing samples
    >> get_fax_link_samples.py -i DID -s MWT2_UC_SCRATCHDISK SLACXRD_SCRATCHDISK

    - Output fax-link files into a specific directory
    >> get_fax_link_samples.py -i DID -d /other/dir/for/output/

    - Check if any of the datasets have missing links. This increases run time
      but is useful if you use the -rse_site option
    >> get_fax_link_samples.py -f file_with_DIDs.txt -s MWT2_UC_SCRATCHDISK --missing

Author:
    Alex Armstrong <alarmstr@cern.ch>
License:
    Copyright: (C) <May 19th, 2018>; University of California, Irvine
================================================================================
"""

import sys, os, traceback, argparse
import time
import subprocess
from itertools import combinations
from collections import Counter


EXPECTED_REPLICA_INFO = ['SCOPE', 'NAME', 'FILESIZE', 'ADLER32', 'RSE: REPLICA']
REPLICA_INFO = ['scope', 'name', 'filesize', 'adler32', 'rse', 'link']
MISSING_FILE_INFO = ['SCOPE', 'NAME']
SAMPLE_NOT_FOUND_ERROR = 'ERROR\tData identifier not found'

################################################################################
# MAIN
def main():
    """ Main Function """
    global args

    print "===== Checking environment setup ===="
    check_environment()
    print ""

    print "===== Getting Sample Links ====="
    # Get DIDs from inputs
    if args.ifile_name:
        did_list = get_did_list_from_file(args.ifile_name)
    if args.input_samples:
        did_list = args.input_samples

    # Get DID fax links and write to output file
    n_dids = len(did_list)
    for ii, did in enumerate(did_list):
        print "[%d/%d] Getting links for %s"%(ii+1, n_dids, did)

        links = get_did_links(did, args.rse_sites)
        # skip if no information found for DID
        if not links: continue

        ofile_name = get_ofile_name(did)

        with open(ofile_name,'w') as ofile:
            for link in links: ofile.write("%s\n"%link)

    # Finalize
    if args.output_dir == './':
        print "\nOutputs stored in current directory"
    else:
        print "\nOutputs stored at %s"%os.path.abspath(args.output_dir)
    print "===== COMPLETED ====="

################################################################################
# HELPFUL OBJECTS
class FileReplicaInfo:
    """ Class for storing and comparing file replica information """
    def __init__(self, scope, name, filesize, adler32, rse, link):
        self.scope = scope
        self.name = name
        self.filesize = filesize
        self.adler32 = adler32
        self.rse = rse
        self.link = link
        self.rank = -1

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return (self.scope == other.scope
            and self.name == other.name
            and self.filesize == other.filesize
            and self.adler32 == other.adler32
            and self.rse == other.rse
            and self.link == other.link)


    def determine_rank(self, rse_sites):
        """ Ranking of the file for comparison with file replicas
        Rank is determined by the order of rse_site provided as input
        """
        try:
            self.rank = rse_sites.index(self.rse)
        except ValueError:
            print "WARNING (FileReplicaInfo::determine_rank) :: ",
            print "RSE not found in rse list: %s -> "%self.rse, rse_sites
            self.rank = len(rse_sites)

################################################################################
# HELPER FUNCTIONS
def get_did_list_from_file(file_name):
    """ Grabs DIDs from input file and returns as list

    args:
        file_name (str) - file name

    returns:
        (list) - list of DID strings
    """
    with open(file_name, 'r') as ifile:
        did_list = [l.strip() for l in ifile if l.strip() and not l.startswith('#')]

    return did_list

def get_did_links(did, rse_sites):
    """ Get the fax links for a dataset

    If 'rse_sites' is provided then only those sites are looked at for links.
    The order of sites in the RSE list is used to pick one file if replicas
    exist on multiple sites.

    args:
        did (str) - dataset identifier
        rse_sites (list) - list of grid site names to search

    returns:
        (list) - list of fax links, potentially for multiple sites
    """
    rucio_cmd = 'rucio list-file-replicas %s'%did
    rucio_cmd += ' --protocols root'


    output = []
    if not rse_sites:
        rucio_output = get_cmd_output(rucio_cmd)
        output = strip_rucio_file_replica_output(rucio_output, EXPECTED_REPLICA_INFO)
    else:
        output = get_rse_specified_output(rucio_cmd, rse_sites)

    replica_files = [parse_rucio_file_replica_info(x) for x in output]
    replica_files = remove_duplicates(replica_files, rse_sites)
    

    # Check for missing files if the sample was found
    sample_exists = all(SAMPLE_NOT_FOUND_ERROR not in x for x in rucio_output)
    if args.missing and sample_exists:
        # Determine rse sites to consider when looking for missing files 
        if args.rse_sites:
            rse_sites = args.rse_sites
        else:
            rse_sites = list(set([x.rse for x in replica_files]))

        # Printout out indicating if files are missing
        check_for_missing_files(rucio_cmd, rse_sites)
    
    # Format link information
    links = [x.link for x in replica_files]

    return links

def get_ofile_name(did):
    """ Determine output file name """

    # Remove scope if it is there
    did_no_scope = did.split(':')[-1]

    # add output directory
    output_dir = os.path.abspath(args.output_dir)
    ofile_name = '%s/%s.txt'%(output_dir, did_no_scope)

    # modify output file name until nothing is being overwritten
    # unless the 'overwite' options is set
    while os.path.exists(ofile_name) and not args.overwrite:
        file_name_short = ofile_name.split('/')[-1]
        print "WARNING :: Output file already exists:", file_name_short
        ofile_name = ofile_name.replace('.txt','_new.txt')
        file_name_short = ofile_name.split('/')[-1]
        print "WARNING :: Storing as", file_name_short

    return ofile_name

#######################################
def check_for_missing_files(rucio_cmd, rse_sites):
    """ Find files for which links cannot be found on specific sites

    args:
        rucio_cmd (str) : rucio command formated for the desired dataset
        rse_sites (list) - list of grid site names to search 

    returns:
        (list) - list of file names not found on any grid site
    """
    
    # format rucio command
    rucio_missing_cmd = rucio_cmd + ' --missing'

    # Get rucio command output for missing files check
    output = set()
    for rse in rse_sites:
        rucio_rse_cmd = rucio_missing_cmd + ' --rse %s'%rse
        rucio_output = get_cmd_output(rucio_rse_cmd)
        rucio_output = strip_rucio_file_replica_output(rucio_output, MISSING_FILE_INFO)

        # Only count as missing the files missing from all sites
        if not output:
            output = set(rucio_output)
        else:
            output = output & set(rucio_output)

    # Extract the file names from the rucio output
    missing_links = [parse_rucio_missing_file_replica_info(x) for x in output]

    # Indicate if any files are missing
    if missing_links:
        n_missing = len(missing_links)
        n_total = len(output)
        print "INFO :: Unable to find %d/%d files"%(n_missing, n_total)
    elif rucio_output:
        print "INFO :: No missing links"

def strip_rucio_file_replica_output(output, expected_headers):
    """ Remove unwanted headers and trailers from rucio command output

    args:
        output (list) - rucio command output with each line of the output stored
            as an element in a list
        expected_headers (list) - expected header categories in rucio output

    returns:
        (list) - 'output' with unwanted elements removed. Returns empty list
            if output is not as expected
    """

    # Check if sample was not found by rucio
    if any(SAMPLE_NOT_FOUND_ERROR in line for line in output):
        print "WARNING :: Sample not found on rucio"
        return []
    # Check if rucio command failed for some other reason
    elif any('usage: rucio' in line for line in output):
        print "ERROR :: Rucio call failed\n",output[-1].strip()
        return []

    # Check if header categories are as expected
    header = output[1]
    parsed_header = [s.strip() for s in header.split('|') if s.strip()]
    if parsed_header != expected_headers:
        print "ERROR (strip_rucio_file_replica_output) :: ",
        print "Unrecognized output format %s, "%str(parsed_header)
        print 'Expected %s'%str(expected_headers)

    # Remove unwanted header lines and trailing line
    return output[3:-1]

def get_rse_specified_output(rucio_cmd, rse_sites):
    """ Get rucio command output for each rse site and combine the results

    args:
        rucio_cmd (str) : rucio command formated for the desired dataset
        rse_sites (list) - list of grid site names to search

    returns:
        (list) - rucio command output for each file on each requested site

    """
    output = []
    for rse in rse_sites:
        rucio_rse_cmd = rucio_cmd + ' --rse %s'%rse
        rucio_output = get_cmd_output(rucio_rse_cmd)
        output += strip_rucio_file_replica_output(rucio_output, EXPECTED_REPLICA_INFO)

    return output

def parse_rucio_file_replica_info(output_str):
    """ Extract and reformat information from rucio output on a file replica

    args:
        output_str (str) : single line of rucio output containing file replica info

    returns:
        (FileReplicaInfo) : class that handles file information
    """

    # Format desired information into list
    parsed_info = [s.strip() for s in output_str.split('|') if s.strip()]

    # Check for expected format
    assert len(EXPECTED_REPLICA_INFO) == len(parsed_info), (
    'ERROR (parse_rucio_file_replica_info) :: Unrecognized format')

    # Seperate RSE and link found in last entry
    rse = parsed_info[-1].split(' ')[0][:-1]
    link = parsed_info[-1].split(' ')[1]
    parsed_info[-1] = rse
    parsed_info.append(link)

    # Check for desired format
    assert len(REPLICA_INFO) == len(parsed_info)

    # Initialize and return class for handling data
    return FileReplicaInfo(*parsed_info)

def remove_duplicates(replica_files, rse_sites = []):
    """ Remove undesired links for files on multiple grid sites

    The preferred links to keep can be determined by input with 'rse_sites' or
    is determined automatically by preferring sites that have more files on
    them.

    args:
         replica_files (list of FileReplicaInfo)
         rse_sites (list) - order of preference for sites in case of duplicates.
            If empty, then order of preference is determined automatically.

    returns:
        (list) - 'replica_files' with unewanted entries removed
    """

    # Determine how many files are on each site
    rse_count = Counter([x.rse for x in replica_files])

    # Get list of all rse sites ordered by number of files at that site if
    # preference not already provided
    if not rse_sites:
        rse_sites = [x[0] for x in rse_count.most_common()]

    # Set the rank of each file to allow for comparison
    for file1 in replica_files:
        file1.determine_rank(rse_sites)

    # Create list of desired files
    replica_files_no_duplicates = []
    for file1 in replica_files:
        for file2 in replica_files:
            if file1 == file2 or file1.name != file2.name: continue
            # larger rank value -> lower rank
            if file1.rank > file2.rank: break
            elif file1.rank == file2.rank:
                print "TESTING :: File ranks are the same. Shouldn't happen"
        else:
            # Store if no files are found with a higher rank
            replica_files_no_duplicates.append(file1)

    # Indicate if samples were removed and which ones were kept
    if len(replica_files_no_duplicates) != len(replica_files):
        # Check if all sites occur equally frequently
        if len(set([x[1] for x in rse_count.most_common()])) == 1:
            print "INFO :: All dataset files replicated",
            print "on multiple sites: %s."%str(rse_sites),
            print "All links will be for", rse_sites[0]
        else:
            print "INFO :: Some dataset files are replicated on multiple sites:",
            print "Order of preference is", rse_sites

    return replica_files_no_duplicates

########################################
def strip_rucio_file_replica_missing_output(output):
    """ Remove unwanted headers and trailers from rucio command output

    args:
        output (list) - rucio command output with each line of the output stored
            as an element in a list

    returns:
        (list) - 'output' with unwanted elements removed. Returns empty list
            if output is not as expected
    """

    # Check for expected format
    header = output[1]
    parsed_header = [s.strip() for s in header.split('|') if s.strip()]
    if parsed_header != MISSING_FILE_INFO:
        print "ERROR (strip_rucio_file_replica_missing_output) :: ",
        print "Unrecognized output format"
        return []

    # Remove unwanted header lines and trailing line
    return output[3:-1]

def parse_rucio_missing_file_replica_info(output_str):
    """ Extract and reformat information from rucio output on a missing file

    args:
        output_str (str) : single line of rucio output containing missing file info

    returns:
        (str) : file name
    """
    # Format desired information into list
    parsed_info = [s.strip() for s in output_str.split('|') if s.strip()]

    # Check for expected format
    assert len(MISSING_FILE_INFO) == len(parsed_info), (
    'ERROR (parse_rucio_missing_file_replica_info) :: Unrecognized format')

    # Grab the file name
    file_name = parsed_info[1]

    return file_name

################################################################################
# ADMINISTRATIVE FUNCTIONS
def check_args(args, parser):
    """ Check the input arguments are as expected """
    if not (args.ifile_name or args.input_samples):
        print "ERROR :: an input file or list of samples is required"
        parser.print_help(sys.stderr)
        sys.exit()

    if args.ifile_name and not os.path.exists(args.ifile_name):
        print "ERROR :: Cannot find input file:", args.ifile_name
        sys.exit()

    if not os.path.isdir(args.output_dir):
        print "ERROR :: unable to find output directory:", args.output_dir
        sys.exit()

def rucio_is_setup() :
    print "Checking that rucio is setup"
    default = ""
    rucio_home = os.getenv('RUCIO_HOME', default)
    if rucio_home == default :
        print "ERROR :: rucio is not setup, please set it up before running this script"
        return False
    else :
        print "INFO :: rucio found: %s"%rucio_home
        return True

def grid_proxy_setup() :
    print "Checking for valid grid proxy"
    def print_fail_msg():
        print "ERROR :: grid proxy is not setup, please set one up before running this script"
        print "Run : voms-proxy-init -voms atlas -valid 96:00"
        return False

    proxy = os.getenv('X509_USER_PROXY')
    if not proxy: print_fail_msg()
    for line in get_cmd_output('voms-proxy-info'):
        if 'timeleft' in line: break
    else:
        print_fail_msg()
    hours_left = int(line.strip().split(':')[1])
    if hours_left == 0:
        print_fail_msg()
    else:
        print "INFO :: grid proxy found (%d hour(s) left): %s"%(hours_left, proxy)
        return True

def get_cmd_output(cmd, print_cmd=False, print_output=False):
    """ Return output from shell command """
    tmp_file_dump = 'tmp_shell_command_dump.txt'
    if print_output:
        shell_cmd = '%s |& tee %s'%(cmd, tmp_file_dump)
    else:
        shell_cmd = '%s &> %s'%(cmd, tmp_file_dump)

    if print_cmd: 
        print shell_cmd

    subprocess.call(shell_cmd, shell=True)
    output = []
    with open(tmp_file_dump,'r') as f:
        output = f.readlines()
    shell_cmd = 'rm %s'%tmp_file_dump
    subprocess.call(shell_cmd, shell=True)
    return output

def check_environment():
    """ Check if the shell environment is setup as expected """
    grid_proxy_setup()
    rucio_is_setup()

################################################################################
# Run main when not imported
if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('-f', '--ifile_name',
                            help='Name of file containing DIDs. Blank and commented lines are skipped')
        parser.add_argument('-i', '--input_samples',
                            nargs='+',
                            help='DID list of samples to process')
        parser.add_argument('-s', '--rse_sites',
                            nargs='+',
                            help='RSE sites to check. Order by preference in case of duplicates')
        parser.add_argument('-m', '--missing',
                            action='store_true',
                            help='Check files are missing. Useful with the rse_sites option')
        parser.add_argument('-d', '--output_dir',
                            default='./',
                            help='directory for output sample files')
        parser.add_argument('--overwrite',
                            action='store_true',
                            help='allow overwriting of files with same name as output files')
        parser.add_argument('-v', '--verbose',
                            action='store_true', default=False,
                            help='verbose output')
        args = parser.parse_args()
        check_args(args, parser)
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
