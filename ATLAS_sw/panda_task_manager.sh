#!/bin/bash 

echo "Getting status" 
#pattern="user.*n0306[a-z]/"; export GRID_USER_NAME="Alex Armstrong iii"
pattern="group.perf-muons.muTrigNt.n010*"; export GRID_USER_NAME="perf-muons"
pandamon -d 2 | grep -v "aborted" > panda_status_tasks.txt
echo "Sorting"
cat panda_status_tasks.txt | grep "done.*100%" | grep -o $pattern  > complete_tasks.txt
sed -i.tmp 's/\//_nt/g' complete_tasks.txt
rm *.tmp
cat panda_status_tasks.txt | grep -v "done.*100%"  > incomplete_tasks.txt
cat panda_status_tasks.txt | grep "failed" | grep -o user.*    > failed_tasks.txt
cat panda_status_tasks.txt | grep "broken" | grep -o user.*    > broken_tasks.txt

echo -e "\nFiles with number of samples:"
wc -l complete_tasks.txt
wc -l incomplete_tasks.txt
wc -l failed_tasks.txt
wc -l broken_tasks.txt

