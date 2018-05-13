#!/bin/bash
# Replicate input file list onto multiple RSE sites

# Sites found to be reliable and FAX-accessible
SITES=""
SITES="$SITES SLACXRD_SCRATCHDISK"
#SITES="$SITES MWT2_UC_SCRATCHDISK"
#SITES="$SITES AGLT2_SCRATCHDISK"
#SITES="MWT2_UC_LOCALGROUPDISK"
#SITES="SLACXRD_LOCALGROUPDISK"
#SITES="cloud=US&type=LOCALGROUPDISK"

usr="$USER"
#usr="perf-muons"
while IFS='' read -r dataset || [[ -n "$dataset" ]]; do
    # Skip blank lines or lines starting with #
    if [ -z "$dataset" ] || [[ ${dataset:0:1} == "#" ]]; then 
        continue
    fi
    
    # Replicate dataset to each site in SITES
    for site in $SITES; do
        cmd="rucio add-rule $dataset 1 $site --grouping ALL"
        echo "$cmd"
        $cmd
    done
done < "$1"
