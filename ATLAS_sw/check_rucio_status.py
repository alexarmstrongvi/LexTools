#!/usr/bin/env python
"""
===============================================================================
Determines whether samples exist on rucio and, if so,
gathers some diagnositic information
Examples
    check_rucio_status file_with_full_sample_names.txt
Notes:
    - You must have rucio and a grid proxy setup
    - Ignores blank lines or those that begin with #
    - Will not process wildcards in names
    - Will use beginning of name to add scope if not specified

Author:
    Alex Armstrong (alarmstr@cern.ch)
Licence:
    Copyright: (C) <Mar 15, 2018>; University of California, Irvine 
===============================================================================

"""

import sys, os, traceback
import argparse
import time
import subprocess
from math import log10
import re
import pyTools as tools
from collections import defaultdict

################################################################################
# User defined global

# format {r-tag : (mu, cavern bkgd)}
# Encountered but unkown r-tags are indicated with empty strings
R_TAGS  = {'r7409'  : (200, ''), #https://its.cern.ch/jira/browse/ATLMCPROD-2394?jql=text%20~%20%22r7409%22
           'r8974'  : (0, 0),
           'r9361'  : (40, 25), # https://its.cern.ch/jira/browse/ATLMCPROD-3906?jql=text%20~%20%22r9361%22 
           'r9380'  : (200, 150), # https://its.cern.ch/jira/browse/ATLMCPROD-3906?jql=text%20~%20%22r9380%22
           'r9381'  : (200, 0),
           'r9421'  : (0, 0),
           'r9531'  : (0, 0),
           'r9537'  : (200, 25),
           'r9561'  : (40, 5), 
           'r9630'  : (200, 0),
           'r9683'  : (140, 18),
           'r9684'  : (80, 10),
           'r9899'  : (200, 25),
           'r10024' : (200, 0),
           'r10173' : ('', ''),
           'r10280' : (140, 18),
           'r10370' : (140, 25),
           'r10371' : (140, 12),
           'r10372' : (140, 5),
           'r10373' : ('', '')}

# Base link to AMI tag info
# Get full link by appending underscore seperated list of tags
AMI_TAG_INFO_LINK = "https://ami.in2p3.fr/app?subapp=tagsShow&userdata="
MUTRIGNT_TAGS = ['e','s','r','f','m']

################################################################################
def main ():
    """ Main Function """ 
    print '\n====== Running check_rucio_status ======\n'
    
    print "Importing pandas...",
    import pandas as pd
    print "Done"

    # Initial setup and checks
    global args
    if os.path.exists(args.output):
        print "Output file already exists: ", args.output
        print "\tConsider deleting first or changing output name"
        sys.exit()
    assert args.units in ['TB','GB','MB','KB','B']
    check_environment()
    
    # Extract sample names
    samples = []
    if args.mutrignt:
        columns = ['DID', 'Group', 'nEvents', 'nFiles', 'Size(%s)'%args.units, 'AMI Tag Info Link', '<mu>', 'CavernBkgd', ]
    else:
        columns = ['DID', 'nEvents', 'nFiles', 'Size(%s)'%args.units]
    df_samples = pd.DataFrame(columns=columns)
    df_samples.name = 'MuTrigNt Sample List'

    scope_flag = False
    with open(args.samples_file, 'r') as ifile:
        for line in ifile:
            line = line.strip()
            if not accept_line(line): continue
            # Add scope if missing
            if ':' not in line:
                scope_flag = True
                line = add_scope(line)
            samples.append(line)
            df_samples = df_samples.append({'DID' : line}, ignore_index=True)
    df_samples = df_samples.set_index("DID")
        
    # Checks
    if scope_flag:
        print "WARNING :: Some samples do not contain scope."
        print "\t Attempting to add scope automatically."
    if len(samples) != len(set(samples)):
        print "WARNING :: Input file likely contains duplicates"
    if args.dryrun:
        print "Samples to be processed:"
        nsamples = len(samples) 
        for ii, sample in enumerate(samples):
            print "\t[%d/%d] %s"%(ii+1, nsamples, sample)
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
    print "Getting sample information"
    for ii, sample in enumerate(samples):
        print "\t[%d/%d] %s"%(ii+1, nsamples, sample)
        if not rucio_file_exists(sample):
            print "\t\t SAMPLE NOT FOUND"
            missing_samples.add(sample)
            df_samples = df_samples.drop(sample)
            continue
        cols_to_fill = ['nFiles', 'Size(%s)'%args.units, 'nEvents']
        df_samples.loc[sample, cols_to_fill] = get_file_info(sample) 
        RSE_info = get_rse_info(sample)
        for ii, (rse, info) in enumerate(sorted(RSE_info.iteritems())):
            df_key = 'RSE %d'%ii if ii else 'RSE'
            if df_key not in df_samples.columns:
                df_samples[df_key] = ''
            info_str = str(info).replace(',',';')
            df_samples.loc[sample][df_key] = "%s %s"%(rse,info_str) 

        if args.mutrignt:
            mutrig_info = get_mutrignt_info(sample) 
            df_samples.loc[sample]['AMI Tag Info Link','<mu>','CavernBkgd'] = mutrig_info 
            df_samples.loc[sample]['Group'] = get_mutrig_did_group(sample)
            
        ofile.write('SAMPLE: %s\n'%sample)
        ofile.write(write_file_info(sample))
        ofile.write(write_replica_info(sample))

    df_samples = df_samples.sort_index()
    if 'txt' in args.output:
        csv_output = args.output.replace('txt','csv')
    else:
        csv_output = args.output + '.csv'
    sep = '|' if args.markdown else ','
    df_samples.to_csv(csv_output, sep=sep)

    # Write out files that were not found by rucio ls
    header = '\n\n===== Files not found on rucio =====\n'
    ofile.write(header)
    for sample in missing_samples:
        ofile.write('%s\n'%sample)
    ofile.write(len(header)*'='+'\n')

    # Clean up
    ofile.close()
    print "Output written to %s(.csv)"%args.output
    print '\n====== Finished running check_rucio_status ======\n'

################################################################################
# FUNCTIONS
def check_environment():
    """ Check if the shell environment is setup as expected """
    assert tools.rucio_is_setup()
    assert tools.grid_proxy_setup()

def accept_line(line, search_exp=None):
    """ Check if line grabbed from a file should be used """  
    if not line or line.startswith('#'):
        return False
    if search_exp and search_exp not in line:
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

def add_scope(sample_name):
    if sample_name.startswith('user'):
        return 'user.'+sample_name.split('.')[1]+":"+sample_name
    if sample_name.startswith('group'):
        return 'group.'+sample_name.split('.')[1]+":"+sample_name
    else:
        return sample_name.split('.')[0]+":"+sample_name

def get_mutrignt_info(did):
    """ 
    Get the scope, pile up, cavern background for sample 
    
    args:
        did (str) : Dataset Identifier (i.e. scope:name)
    returns:
        (int) : average pileup 
        (int) : cavern background
        (str) : hyperlink for AMI Tag info, formatted for google sheets
        Return values are empty strings if not rTag not known 
    """
    # Skip data files or files without DSIDs
    dsid = tools.get_dsid_from_sample(did)
    if not dsid: mu, cavern_bkgd = '-', '-'

    is_data = did[did.find(dsid)-2:did.find(dsid)] == '00'
    if is_data: mu, cavern_bkgd = '-', '-'
    else:
        # Get pileup and cavern background 
        for r_tag, (mu, cavern_bkgd) in R_TAGS.iteritems():
            if r_tag in did: break
        else:
            print "No known r-tags found in sample:", did
            mu, cavern_bkgd = '', ''

    # Get AMI link for all tags
    tags_to_check = "".join(MUTRIGNT_TAGS)
    tags = [x for x in did.split('.') if re.search("[%s][0-9]{2}"%(tags_to_check),x)] 
    if not tags:
        sheets_formula = '-'
    else:
        tags = [x for x in tags[0].split("_") if re.search("[%s][0-9]{2}"%(tags_to_check),x)]
        tag_str = "_".join(tags)
        ami_link = "%s%s"%(AMI_TAG_INFO_LINK, tag_str)
        sheets_formula = "=HYPERLINK(\"%s\", \"AMI Tag Info Link\")"%ami_link

    return sheets_formula, mu, cavern_bkgd

def get_mutrig_did_group(did):
    """
    Determine the group of mutrignt DID
    
    params:
        didi (str) - dataset identifier

    returns:
        (str) - group name
    """
    group = []
    if re.search("Zmumu",did): group.append("Zmumu")
    if re.search("ParticleGenerator_nu|MB_",did): group.append("Minimum Bias")
    if re.search("Jpsi(?=.*r9630)",did): group.append("J/Psi")
    if re.search("Zprime",did): group.append("Zprime")
    if re.search("FRVZ|_2LJ_",did): group.append("Lepton Jets")
    if re.search("jetjet",did): group.append("Dijets")
    if re.search("mu[345][mp](?=.*)",did): group.append("Low pT")
    if re.search("physics_ZeroBias",did): group.append("Data - Zero Bias")
    if re.search("physics_Main",did): group.append("Data - Main")
    if re.search("express_express",did): group.append("Data - Express stream")
    if re.search("single_mu",did): group.append("Single muons")

    # Tie up loose ends
    if not group: group.append("Other")
    if len(group) > 1 : group = ['Multiple (%s)'%(','.join(group))]

    # Return group name
    return group[0]

def get_file_info(sample):
    """ 
    Get file information from rucio list-files
    
    params:
        sample (str): Dataset Identification (i.e. scope:name)
    returns:
        (int) : number of files
        (str) : size of all files (Terabytes)
        (int) : number of events in all files
        Return values are empty strings if not found in rucio output 
    """

    # Get rucio list-files output
    rucio_cmd = 'rucio list-files ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)
     
    n_files = size = n_events = ''
    for line in rucio_output:
        if 'Total' not in line: continue
        elif 'Total files' in line: 
            n_files =  int(line.strip().split()[-1]) 
        elif 'Total size' in line:
            size = float(line.strip().split()[-2]) 
            if size == 0: 
                size = '0'
                continue

            # Convert everything to same units
            units = line.strip().split()[-1].upper()
            if units=='TB': scale = 1
            elif units=='GB': scale = 1e-3
            elif units=='MB': scale = 1e-6
            elif units=='KB': scale = 1e-9
            elif units=='B': scale = 1e-12
            else:
                print "Unexpected units: (%s)->(%s) "%(line,units)
            size *= scale 

            # Convert to desired units
            if args.units=='TB': scale = 1
            elif args.units=='GB': scale = 1e+3
            elif args.units=='MB': scale = 1e+6
            elif args.units=='KB': scale = 1e+9
            elif args.units=='B': scale = 1e+12
            size *= scale

            # Include at least 3 significant figures 
            power = int(log10(abs(size)))
            if power <= -9: prec = 12
            elif power <= -6: prec = 9
            elif power <= -3: prec = 6
            elif power <= 2: prec = 3
            else: prec = 0

            size = str(round(size, prec))
        elif 'Total events' in line:
            n_events = int(line.strip().split()[-1])
        else:
            print "WARNING :: Unknown file info:", line
    
    return n_files, size, n_events

def get_rse_info(sample):
    """ 
    get dataset rse information from rucio list-dataset-replicas
    
    params:
        sample (str): Dataset Identification (i.e. scope:name)
    returns:
        (dict) : map from RSE sites to information about samples on that site.
                 
                 Information includes available and total files per site and, 
                 if necessary, the ID tag appended to the DID for cases where
                 the sample is split across multiple sites

                 example: {'BNL-OSG2_MCTAPE' : ['id_tag1 (500/500)'; 'id_tag2 (298/298)']
                           'BNL-OSG2_DATADISK' : ['id_tag2 (500/500)']}
        
    """

    # Get rucio list-dataset-replicas output
    rucio_cmd = 'rucio list-dataset-replicas ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)

    # Check if sample is split
    n_samples = sum(1 for x in rucio_output if "DATASET" in x)
    is_split = n_samples > 1
    
    # Initialize tools for extraction
    reject_patterns = ['DATASET', 'RSE', '---','SCRATCHDISK'] # don't grab from these lines
    RSE_sites = {} 
    id_found_expected = defaultdict(lambda :[0,0])
    info = defaultdict(list)
    def prepare_rse_info(info_map):
        # Rearrange RSE information into desired format
        if not info_map: return
        for split_id, rse_info_list in info_map.iteritems():
            for info_list in rse_info_list:
                RSE, found, exp, flag = info_list
                id_found_expected[RSE][0] += found 
                id_found_expected[RSE][1] += exp 
        for RSE, (found, exp) in id_found_expected.iteritems():
            flag = "*" if found != exp else ''
            RSE_sites[RSE] = '(%d/%d)%s'%(found,exp,flag) 
        info.clear()
        
    # Extract informtion from rucio output
    for line in rucio_output:
        line = line.strip()
        
        # Get dataset info 
        if 'DATASET' in line:
            # Save previous dataset info if any
            prepare_rse_info(info)
            # Get tag added to DID when split
            split_id_start = line.find(sample)+len(sample)
            split_id = line[split_id_start:]

        # Get replica information
        if not line or any(x in line for x in reject_patterns): 
            continue
        RSE_site = line.split()[1]
        files_found = int(line.split()[3])
        files_expected = int(line.split()[5])
        flag = '*' if files_found < files_expected else ''
        rse_info = [RSE_site, files_found, files_expected, flag]
        info[split_id].append(rse_info)

    prepare_rse_info(info)
    return RSE_sites

def write_file_info(sample):
    """ Add file information from rucio list-files"""

    # Get rucio list-files output
    rucio_cmd = 'rucio list-files ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)

    info_to_write = '\t\tFILE STATS - '
    for line in rucio_output:
        if 'Total' not in line: continue
        info = line.strip()[len('Total '):]
        info_to_write += "%s, "%info 
    
    # remove trailing comma and add newline
    info_to_write = info_to_write[:-2] + '\n'    
    
    return info_to_write

def write_replica_info(sample):
    """ Add dataset replica information from rucio list-dataset-replicas"""

    # Get rucio list-dataset-replicas output
    rucio_cmd = 'rucio list-dataset-replicas ' + sample
    rucio_output = tools.get_cmd_output(rucio_cmd)


    # Check if sample is split
    n_samples = len([x for x in rucio_output if "DATASET" in x])
    is_split = True if n_samples > 1 else False
    prefix = '\t\tREPLICA - '
    info_to_write = prefix if not is_split else ''
    
    reject_patterns = ['DATASET', 'RSE', '-'] # don't grab from these lines
    for line in rucio_output:
        line = line.strip()

        # Add new line for each split sample 
        if is_split and 'DATASET' in line:
            info_to_write += '\n' if info_to_write else ''
            split_id_start = line.find(sample)+len(sample)
            split_id = line[split_id_start:]
            info_to_write += prefix + '(%s) '%split_id 
        
        # Get replica information
        if not line or any(x in line for x in ['DATASET', 'RSE', '---']): 
            continue
        RSE_site = line.split()[1]
        files_found = int(line.split()[3])
        files_expected = int(line.split()[5])
        flag = '*' if files_found < files_expected else ''
        info_to_write += "%s (%d/%d)%s, "%(RSE_site, files_found, 
                                           files_expected, flag) 

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
        parser.add_argument('-u', '--units', 
                            default='TB', 
                            help='Units for file size information in output: TB,GB,MB,KB,B')
        parser.add_argument('-o', '--output', 
                            default='sample_rucio_status.txt', 
                            help='Name of output file for diagnostic info')
        parser.add_argument('--mutrignt', 
                            action='store_true', default=False, 
                            help='Output tailored for muTrigNt inputs (AOD/ESD/muTrigNt)')
        parser.add_argument('--markdown', 
                            action='store_true', default=False, 
                            help='Use "|" as a seperator in the output csv file')
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
