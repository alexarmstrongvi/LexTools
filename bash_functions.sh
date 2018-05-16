#!/bin/bash

################################################################################
# Variable checks
function is_true() {
    local bool=$1
    [ "$bool" == true ]
}

function is_false() {
    local bool=$1
    [ "$bool" == false ]
}

function is_empty() {
    local var=$1
    [[ -z $var ]]
}
function is_not_empty() {
    local var=$1
    [[ -n $var ]]
}
function is_file() {
    local file=$1
    [[ -f $file ]]
}
function is_not_file() {
    local file=$1
    [ ! -f $file ]
}
function is_dir() {
    local dir=$1
    [[ -d $dir ]]
}
function is_not_dir() {
    local dir=$1
    [[ ! -d $dir ]]
}

################################################################################
# Print styles
e_header() {
    printf "\n${bold}${purple}==========  %s  ==========${reset}\n" "$@"
}
e_arrow() {
    printf "➜ $@\n"
}
e_success() {
    printf "${green}✔ %s${reset}\n" "$@"
}
e_error() {
    printf "${red}✖ %s${reset}\n" "$@"
}
e_warning() {
    printf "${tan}➜ %s${reset}\n" "$@"
}
e_underline() {
    printf "${underline}${bold}%s${reset}\n" "$@"
}
e_bold() {
    printf "${bold}%s${reset}\n" "$@"
}
e_note() {
    printf "${underline}${bold}${blue}Note:${reset}  ${blue}%s${reset}\n" "$@"
}

################################################################################
# User input
seek_confirmation() {
  printf "\n${bold}$@${reset}"
  read -p " (y/n) " -n 1
  printf "\n"
}
# Test whether the result of an 'ask' is a confirmation
is_confirmed() {
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
  return 0
fi
return 1
}