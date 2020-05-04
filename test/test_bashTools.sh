#!/usr/bin/env bash
RUN_DIR="$PWD"

source bashTools.sh

function oneTimeSetUp() {
    # setup for testUsefulFunctions
    true_var=true
    false_var=false
    non_empty_var="string"
    test_file="tmp_file.txt"
    test_dir="tmp_dir"

    rm -rf $test_dir
    mkdir $test_dir
    cd $test_dir
    echo "Hello World" > $test_file
    cd ..
    echo "Area setup of $test_dir"
    ls -R $test_dir
}

function testUsefulFunctions() {
    assertTrue \
        'Failed is_dir True test' \
        $(is_dir $test_dir; echo $?)
    assertTrue \
        'Failed is_not_dir True test' \
        $(is_not_dir "not_a_dir"; echo $?)
    cd $test_dir
    assertTrue \
        'Failed is_file True test' \
        $(is_file $test_file; echo $?)
    assertTrue \
        'Failed is_not_file True test' \
        $(is_not_file "not_a_file"; echo $?)
    cd ..
    assertTrue \
        'Failed is_empty True test' \
        $(is_empty $empty_var; echo $?)
    assertTrue \
        'Failed is_not_empty True test' \
        $(is_not_empty $non_empty_var; echo $?)
    assertTrue \
        'Failed is_true True test' \
        $(is_true true; echo $?)
    assertTrue \
        'Failed is_false True test' \
        $(is_false false; echo $?)

    assertFalse \
         'Failed is_dir False test' \
         $(is_dir "not_a_dir"; echo $?)
    assertFalse \
         'Failed is_not_dir False test' \
         $(is_not_dir $test_dir; echo $?)
    cd $test_dir
    assertFalse \
         'Failed is_file False test' \
         $(is_file "not_a_file"; echo $?)
    assertFalse \
         'Failed is_not_file False test' \
         $(is_not_file $test_file; echo $?)
    cd ..
    assertFalse \
         'Failed is_empty False test' \
         $(is_empty $non_empty_var; echo $?)
    assertFalse \
         'Failed is_not_empty False test' \
         $(is_not_empty $empty_var; echo $?)
    assertFalse \
         'Failed is_true False test' \
         $(is_true false; echo $?)
    assertFalse \
         'Failed is_false False test' \
         $(is_false true; echo $?)

    echo
    redf "Red Text"
    greenf "Green Text"
    tan "Tan Text"
    bluef "Blue Text"
    purplef "Purple Text"
    greyf "Grey Text"
    whitef "White Text"

    e_header "Header Text"
    e_arrow "Arrow Text"
    e_success "Success Text"
    e_error "Error Text"
    e_warning "Warning Text"
    e_underline "Underline Text"
    e_bold "Bold Text"
    e_note "Note Text"

    if seek_confirmation "Yes or no?"; then e_success "Yes"; else e_error "No"; fi

    return 0
}

function oneTimeTearDown() {
    rm -rf $test_dir
}
. shunit2
