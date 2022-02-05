#!/bin/bash/env python
"""
Program: compare_sample_list.py
Author: Alex Armstrong <alarmstr@cern.ch>
Copyright: (C) Dec 21st, 2017; University of California, Irvine

Takes two txt files of sample containers and compares them,
writing out samples that are shared by and unique to the
input files. It also groups the samples into categories
"""
import os
import sys
from argparse import ArgumentParser
import pyTools as tools
from collections import defaultdict

def main():
    parser = ArgumentParser()
    parser.add_argument('file0',
                        help='first txt file with sample names')
    parser.add_argument('file1',
                        help='second txt file with sample names')
    parser.add_argument('-o', '--output',
                        default='',
                        help='output file name')
    parser.add_argument('--keep_file0',
                        action='store_true',
                        help='store only DSIDs unique to first input file')
    parser.add_argument('--keep_file1',
                        action='store_true',
                        help='store only DSIDs unique to second input file')
    parser.add_argument('--keep_shared',
                        action='store_true',
                        help='store only shared DSIDs')
    parser.add_argument('--plain',
                        action='store_true',
                        help='store only DSIDs without extra headers and labels')
    parser.add_argument('--trim',
                        action='store_true',
                        help='trim sample names')
    args = parser.parse_args()

    exit = False
    if not os.path.exists(args.file0):
        print 'No such file %s'%args.file0
        exit = True
    if not os.path.exists(args.file1):
        print 'No such file %s'%args.file1
        exit = True
    if exit: sys.exit()

    keep_shared = args.keep_shared
    keep_file0 = args.keep_file0
    keep_file1 = args.keep_file1

    #Get output name
    output_name = args.output
    name0 = args.file0.strip().split('/')[-1].split('.')[-2]
    name1 = args.file1.strip().split('/')[-1].split('.')[-2]
    if not output_name:
        output_name = 'SampleCompare_%s_and_%s.txt'%(name0, name1)
    if len(output_name.split('.')[-1]) != len('txt'):
        output_name += '.txt'
    # Get map of DSIDs to sample
    # and DSIDs to group
    sample_maps = []
    grouping_maps = []

    for file_name in [args.file0, args.file1]:
        txt_file = open(file_name,'r')
        sample_list = [x.strip() for x in txt_file.readlines() if x and not x.startswith('#')]
        sample_list = [x for x in sample_list if tools.get_dsid_from_sample(x)]
        if args.trim:
            sample_list = [tools.trim_sample_name(x) for x in sample_list]
        sample_list = [x for x in sample_list if x]
        dsid_sample_map = tools.get_dsid_sample_map(sample_list)
        sample_maps.append(dsid_sample_map)
        dsid_grouping_map = {}
        for dsid, sample in dsid_sample_map.iteritems():
            group = tools.get_sample_group(sample)
            dsid_grouping_map[dsid] = group
        grouping_maps.append(dsid_grouping_map)
        txt_file.close()

    # Get unique and shared DSIDs
    file0_dsids, file1_dsids = tools.get_unique_elements(sample_maps[0],sample_maps[1])
    shared_dsids = tools.get_shared_elements(sample_maps[0],sample_maps[1])

    # Group samples
    shared_dsids_grouped = defaultdict(list)
    for dsid in shared_dsids:
       group = grouping_maps[0][dsid]
       sample = sample_maps[0][dsid]
       if len(sample) == 6:
           group = grouping_maps[1][dsid]
           sample = sample_maps[1][dsid]
       shared_dsids_grouped[group].append(sample)
    file0_dsids_grouped = defaultdict(list)
    for dsid in file0_dsids:
       group = grouping_maps[0][dsid]
       sample = sample_maps[0][dsid]
       file0_dsids_grouped[group].append(sample)
    file1_dsids_grouped = defaultdict(list)
    for dsid in file1_dsids:
       group = grouping_maps[1][dsid]
       sample = sample_maps[1][dsid]
       file1_dsids_grouped[group].append(sample)

    # Write output
    ofile = open(output_name,'w')
    if not args.plain:
        ofile.write('='*80+'\n')
        ofile.write('Sample List Comparison\n')
        ofile.write('='*80+'\n')

    # Write the number of samples in shared and unique files
    # as well as the break down of each into sample groups
    if not args.plain:
        total_dsids = len(shared_dsids) + len(file0_dsids) + len(file1_dsids)
        ofile.write('Total files: %d\n'%total_dsids)
        ofile.write('\tShared files: %d\n'%len(shared_dsids))
        for group, sample_list in sorted(shared_dsids_grouped.iteritems()):
            ofile.write('\t\t%*s: %d\n'%(-20,group,len(sample_list)))
        ofile.write('\t%s files: %d\n'%(name0,len(file0_dsids)))

        for group, sample_list in sorted(file0_dsids_grouped.iteritems()):
            ofile.write('\t\t%*s: %d\n'%(-20,group,len(sample_list)))
        ofile.write('\t%s files: %d\n'%(name1,len(file1_dsids)))
        
        for group, sample_list in sorted(file1_dsids_grouped.iteritems()):
            ofile.write('\t\t%*s: %d\n'%(-20,group,len(sample_list)))
    
    # Write out sample names under groups
    if keep_shared or not (keep_file0 or keep_file1):
        if not args.plain: 
            ofile.write('\n\n++++++++++++++++ Shared DSIDs ++++++++++++++++\n')
        for group, sample_list in sorted(shared_dsids_grouped.iteritems()):
            if not args.plain: ofile.write('\n\t===== %s =====\n'%group)
            for sample in sorted(sample_list):
                if not args.plain:
                    ofile.write('\t\t%s\n'%sample)
                else:
                    ofile.write('%s\n'%sample)

        
    if keep_file0 or not (keep_shared or keep_file1):
        if not args.plain:
            ofile.write('\n\n++++++++++++++++ %s DSIDs ++++++++++++++++\n'%name0)
        for group, sample_list in sorted(file0_dsids_grouped.iteritems()):
            if not args.plain: ofile.write('\n\t===== %s =====\n'%group)
            for sample in sorted(sample_list):
                if not args.plain:
                    ofile.write('\t\t%s\n'%sample)
                else:
                    ofile.write('%s\n'%sample)
        
    if keep_file1 or not (keep_shared or keep_file0):
        if not args.plain: 
            ofile.write('\n\n++++++++++++++++ %s DSIDs ++++++++++++++++\n'%name1)
        for group, sample_list in sorted(file1_dsids_grouped.iteritems()):
            if not args.plain: ofile.write('\n\t===== %s =====\n'%group)
            for sample in sorted(sample_list):
                if not args.plain:
                    ofile.write('\t\t%s\n'%sample)
                else:
                    ofile.write('%s\n'%sample)
                ofile.write('\t\t%s\n'%sample)

    print 'Output written to %s'%output_name
    ofile.close()



if __name__ == '__main__':
    # Do not execute main() when script is imported as a module
    main()
