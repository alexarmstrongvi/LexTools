#!/usr/bin/env python
"""
================================================================================

Creates txt files of fax links to all files in each of the provided datasets

Examples:
    Simple use cases:

    >> get_fax_link_samples.py -f file_with_DIDs.txt
    >> get_fax_link_samples.py -i DID1 DID2 ...

    Using the options:

    - Getting links for a specific site
    >> get_fax_link_samples.py -i DID1 -s MWT2_UC_SCRATCHDISK

    - Output fax-link files into a specific directory
    >> get_fax_link_samples.py -f file_with_DIDs.txt -d /other/dir/for/output/

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
from collections import namedtuple, Counter


EXPECTED_REPLICA_INFO = ['SCOPE', 'NAME', 'FILESIZE', 'ADLER32', 'RSE: REPLICA']
REPLICA_INFO = ['scope', 'name', 'filesize', 'adler32', 'rse', 'link']
MISSING_FILE_INFO = ['SCOPE', 'NAME']

################################################################################
def main ():
    """ Main Function """

    global args
    check_environment()

    # Get DIDs from inputs
    if args.ifile_name:
        did_list = get_did_list_from_file(args.ifile_name)
    if args.input_samples:
        did_list = args.input_samples

    print "TESTING :: did_list = ", did_list
    sys.exit() #TESTING

    # Get DID fax links and write to output file
    n_dids = len(did_list)
    for ii, did in enumerate(did_list):
        print "INFO :: [%d/%d] Getting links for %s"%(ii, n_dids, did)
        links = get_did_links(did, args.rse_sites)

        # Note if any files are missing
        if args.missing
            missing_links = get_missing_links(did, args.rse_sites)
            # TODO: Add colors to output
            if missing_links:
                n_missing = len(missing_links)
                n_total = len(missing_links) + len(links)
                print "WARNING :: \tunable to find %d/%d files"%(n_missing, n_total)
            else:
                print "INFO :: \tNo missing links"

        ofile_name = get_ofile_name(did)

        with ofile as open(ofile_name,'w'):
            for link in links:
                ofile.write("%s\n"%link)

    # Finalize
    if args.output_dir = './':
        print "FINISHED :: Outputs stored in current directory"
    else:
        print "FINISHED :: Outputs stored at %s"args.output_dir


################################################################################
# HELPFUL OBJECTS
class FileReplicaInfo:
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


        def determine_rank(rse_sites):
            # Rank is determined by the order of rse_site provided by the user
            try:
                self.rank = rse_sites.index(self.rse)
            except ValueError:
                print "WARNING (FileReplicaInfo::determine_rank) :: ",
                print "RSE not found in rse list: %s -> "%self.rse, rse_sites
                self.rank = len(rse_sites)

MissingFileInfo = namedtuple("MissingFileInfo",MISSING_FILE_INFO)

################################################################################
# HELPER FUNCTIONS

get_did_links(did, rse_sites):
    """
    """
    rucio_cmd = 'rucio list-file-replicas %s'%did
    rucio_cmd += ' -protocols root'

    output = []
    if not rse_sites:
        rucio_output = get_cmd_output(rucio_cmd)
        output = strip_rucio_file_replica_output(rucio_output)
    else:
        output = get_rse_specified_output(rucio_cmd, rse_sites)

    replica_files = [parse_rucio_file_replica_info(x) for x in output]
    replica_files = remove_duplicates(replica_files, rse_sites)
    links = [x.link for x in replica_files]
    return links

remove_duplicates(replica_files, rse_sites = []):
    """
    """
    if not rse_sites:
        # Get list of all rse sites ordered by number of files at that site
        rse_count = Counter([x.rse for x in replica_files])
        rse_sites = [x[0] for x in rse_count.most_common()]

    for file in replica_files:
        file.determine_rank(rse_sites)
        if file.rank < 0:
            "TESTING :: Rank not being set properly"

    replica_files_no_duplicates = []
    for file1 in replica_files:
        for file 2 in replica_files:
            if file1 == file2 or file1.name != file2.name: continue
            # larger rank value -> lower rank
            if file1.rank > file2.rank: break
            elif file1.rank == file2.rank:
                print "TESTING :: File ranks are the same. Shouldn't happen"
        else:
            # Store if no files are found with a higher rank
            replica_files_no_duplicates.append(file1)

    return replica_files_no_duplicates

get_rse_specified_output(rucio_cmd, rse_sites, missing=False):
    for rse in rse_sites:
        if len(rse_sites) > 1:
            print "INFO :: \tLooking at RSE: %s"%rse
        rucio_rse_cmd = rucio_cmd + ' -rse %s'%rse
        rucio_output = get_cmd_output(rucio_cmd) + '\n'
        output += strip_rucio_file_replica_output(rucio_output)

get_did_list_from_file(file_name):
    """
    Grabs DIDs from input file and returns as list
    args:
        file_name (str) - file name
    returns:
        (list) - list of DID strings
    """
    with ifile as open(file_name, 'r'):
        did_list = [l for l in ifile if line and not line.startswith('#')]

    return did_list

get_ofile_name(did):
    # Remove scope if it is there
    did_no_scope = did.split(':')[-1]

    # format output directory
    if not args.output_dir.endswith("/"):
        output_dir = "%s/"%args.output_dir
    else:
        output_dir = args.output_dir

    ofile_name = '%s%s.txt'%(output_dir, did)
    return ofile_name

strip_rucio_file_replica_output(output_str):
    # Check for expected format
    header = output_str[1]
    parsed_header = [s.strip() for s in header.split('|') if s.strip()]
    if parsed_header != REPLICA_INFO:
        print "ERROR (strip_rucio_file_replica_output) :: ",
        print "Unrecognized output format"

    # Remove header lines (first 3 lines) and trailing line
    return output_str[3:-1]

strip_rucio_file_replica_missing_output(output_str):
    # Check for expected format
    header = output_str[1]
    parsed_header = [s.strip() for s in header.split('|') if s.strip()]
    if parsed_header != MISSING_FILE_INFO:
        print "ERROR (strip_rucio_file_replica_missing_output) :: ",
        print "Unrecognized output format"

    # Remove header lines (first 3 lines) and trailing line
    return output_str[3:-1]

parse_rucio_file_replica_info(output_str):
    parsed_info = [s.strip() for s in output_str.split('|') if s.strip()]

    # Check for expected format
    assert len(EXPECTED_REPLICA_INFO) == len(parsed_info),
    'ERROR (parse_rucio_file_replica_info) :: Unrecognized format'

    # Seperate RSE and link found in last entry
    rse = parsed_info[-1].split(' ')[0][:-1]
    link = parsed_info[-1].split(' ')[1]
    parsed_info[-1] = rse
    parsed_info.append(link)
    assert len(REPLICA_INFO) == len(parsed_info)
    return FileReplicaInfo(*parsed_info)

get_missing_links(did, rse_sites):
    # TODO
    return []


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

    if args.input_samples: #TESTING
        print "TESTING :: args.input_sampels = ", args.input_samples
        sys.exit()

    if not os.path.isdir(args.output_dir):
        print "ERROR :: unable to find output directory:", args.output_dir
        sys.exit()

def rucio_is_setup() :
    print "Checking that rucio is setup"
    default = ""
    rucio_home = os.getenv('RUCIO_HOME', default)
    if rucio_home == default :
        print "ERROR rucio is not setup, please set it up before running this script"
        return False
    else :
        print " > rucio found: %s"%rucio_home
        return True

def grid_proxy_setup() :
    print "Checking for valid grid proxy"
    def print_fail_msg():
        print "ERROR grid proxy is not setup, please set one up before running this script"
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
        print "grid proxy found (%d hour(s) left): %s"%(hours_left, proxy)
        return True

def get_cmd_output(cmd, print_output=False):
    """ Return output from shell command """
    tmp_file_dump = 'tmp_shell_command_dump.txt'
    if print_output:
        shell_cmd = '%s |& tee %s'%(cmd, tmp_file_dump)
    else:
        shell_cmd = '%s &> %s'%(cmd, tmp_file_dump)

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
                            help='Input file name of samples to process')
        parser.add_argument('-i', '--input_samples',
                            nargs='+',
                            help='DID list of samples to process')
        parser.add_argument('-s', '--rse_sites',
                            nargs='+',
                            help='RSE sites to check. Order by preference')
        parser.add_argument('-m', '--missing',
                            action='store_true',
                            help='Check if any files are missing')
        parser.add_argument('-d', '--output_dir',
                            default='./',
                            help='directory for output sample files')
        parser.add_argument('--dry_run')
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
