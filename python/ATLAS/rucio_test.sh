#!/bin/bash

# More info at https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/RucioClientsHowTo

# Setup rucio
# RUCIO_HOME is an environment variable that
# should be defined if rucio is setup
if [ -z "$RUCIO_HOME" ]; then
    echo -e "\nSetting up rucio"
    lsetup rucio
else
    echo -e "\nRucio is already setup"
fi

file="rucio_test_output.txt"
if [ -f $file ]; then
    echo -e "\tRemoving previous file: $file"
    rm $file
fi
touch rucio_test_output.txt
echo "RUCIO COMMANDS" >> $file
echo -e "\n\n==============================\n" >> $file

function print_cmd {
    echo -e ">> $1 \n" >> $file
    echo -e "\tRunning $1"
    eval "$1" >> $file
    echo -e "\n==============================\n" >> $file
}

print_cmd "rucio whoami"
# This shows you what accounts you can store samples on and how much space they have
print_cmd "rucio list-account-limits $RUCIO_ACCOUNT"
# This shows you how much space you have left to use on sites available to you
print_cmd "rucio list-account-usage $RUCIO_ACCOUNT"

# Info on RSE expressions at https://rucio.readthedocs.io/rse_expressions.html
print_cmd "rucio list-rses --expression 'type=LOCALGROUPDISK&cloud=US'"
# All available attributes can be seen with the following command.
# Run on various sites to see different attributes.
print_cmd "rucio list-rse-attributes MWT2_UC_LOCALGROUPDISK"

echo -e "\n\tOutput stored at $file"
