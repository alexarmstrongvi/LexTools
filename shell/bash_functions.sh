#!/bin/bash

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