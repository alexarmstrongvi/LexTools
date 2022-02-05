#!/bin/bash/env python

################################################################################
# Environment checks
def rucio_is_setup() :
    print("Checking that rucio is setup")
    default = ""
    rucio_home = os.getenv('RUCIO_HOME', default)
    if rucio_home == default :
        print("ERROR rucio is not setup, please set it up before running this script")
        return False
    else :
        print(" > rucio found: %s"%rucio_home)
        return True

def grid_proxy_setup() :
    print("Checking for valid grid proxy")
    def print_fail_msg():
        print("ERROR grid proxy is not setup, please set one up before running this script")
        print("Run : voms-proxy-init -voms atlas -valid 96:00")
        return False

    proxy = os.getenv('X509_USER_PROXY')
    if not proxy: print_fail_msg()
    for line in get_cmd_output('voms-proxy-info'):
        if 'timeleft' in line: break
    else:
        print_fail_msg()
        return False
    hours_left = int(line.strip().split(':')[1])
    if hours_left == 0:
        print_fail_msg()
    else:
        print("grid proxy found (%d hour(s) left): %s"%(hours_left, proxy))
        return True

################################################################################
# Analysis specific
def get_susynt_event_id(event):
    """
    Get a unique event name for susyNt input
    args:
        event (SusyNt::Event) - event object
    return
        str: unique event name
    """
    Event = event.event
    run_num = Event.run
    event_num = Event.eventNumber
    lumi_block = Event.lb

    unique_ID = "run%s_evt%s_lb%s"%(run_num, event_num, lumi_block)
    return unique_ID

def get_dsid_from_sample(sample):
    """ Extract DSID from sample name"""
    sample = sample.strip()
    search_str = r'[1-9][0-9]{5}(?=\.)'
    dsid = strip_string_to_substring(sample,search_str)
    if not dsid:
        dsid = strip_string_to_substring(sample,'[1-9][0-9]{5}')
    return dsid

def get_dsid_sample_map(sample_list):
    """
    Get map of DSIDs to full sample name
    given a list of full sample names
    """
    dsid_sample_map = {}
    for sample in sample_list:
        dsid = get_dsid_from_sample(sample)
        if not dsid:
            continue
        if dsid in dsid_sample_map:
            print('WARNING :: DSID %s is duplicated. Overwriting'%dsid)
            #for ii in itertools.count(start=1):
            #    dsid_new_name = "%s-%s"%(dsid, ii)
            #    if dsid_new_name in dsid_sample_map: continue
            #    dsid = dsid_new_name
            #    break
        dsid_sample_map[dsid] = sample
    return dsid_sample_map

def trim_sample_name(sample):
    dsid = get_dsid_from_sample(sample)
    if not dsid:
        print('WARNING (trim_sample_name) :: '
              'Input sample name has no DSID')
        return ''
    pos = sample.find(dsid)
    sample = sample[pos:]
    # sample names are just DSIDs
    if len(sample) == 6:
        return sample
    # unexpected format with spaces
    if sample.find(' ') != -1:
        return sample

    sample = sample.split('.')[:-1]
    sample = '.'.join(sample)
    return sample

def get_sample_group(sample):
    searches = {}
    # Match pattern order
    # Elements in the innermost lists are OR'd
    # The list elements in main list are AND'd
    # Data
    searches['data15'] = [['data15']]
    searches['data16'] = [['data16']]
    # Higgs
    searches['H Inclusive'] = [ ['H125'],['_inc'] ]
    searches['Htt'] = [ ['H125'],['tautau','2tau'] ]
    searches['HWW'] = [ ['H125'],['WW'] ]
    searches['Hee'] = [ ['H125'],['ee'] ]
    searches['Hmumu'] = [ ['H125'],['mumu'] ]
    searches['ttH'] = [['H125'],['ttH']]
    # Drell-Yan
    searches['Drell-Yan -> ee'] = [['DYee']]
    searches['Drell-Yan -> mumu'] = [['DYmumu']]
    searches['Drell-Yan -> tautau'] = [['DYtautau']]
    # Z -> tautau + jets
    searches['Ztt'] = [['Ztautau','Ztt']]
    # Z -> ee + jets
    searches['Zee'] = [['Zee']]
    # Z -> mumu + jets
    searches['Zmumu'] = [['Zmumu','Zmm']]
    # Z -> vv + jets
    searches['Znunu'] = [['Znunu']]
    # W + jets
    searches['Wjets'] = [['Wplus','Wminus','W(e|mu|tau)nu']]
    # V + gamma
    searches['Wgamma'] = [['enu', 'munu', 'taunu'],['gamma']]
    searches['Zgamma'] = [['ee', 'mumu','tautau','nunu'],['gamma']]
    # ttbar
    searches['ttbar'] = [['ttbar','ttW']]
    # single top
    searches['Single top'] = [['!Wt'],['top','antitop','atop']]
    # Wt
    searches['Vt'] = [['Wt','tW','tZ','Zt'],['top','antitop','atop','noAllHad']]
    # Diboson
    searches['Diboson'] = [['!H125'],['!ttbar'],['WW','ZZ','WZ','ZW','[lv]{4}','[WZ][pqlv]*[WZ]']]
    # Signal: LFV Higgs
    searches['LFV Higgs'] = [['H125'],['taue','etau','mutau','taumu','emu','mue']]

    matched_category = []
    for category, search in searches.iteritems():
        match_results = []
        for must_match in search:
            for possible_match in must_match:
                if possible_match[0] == '!':
                    found = not re.search(r'%s'%(possible_match[1:]),sample)
                else:
                    found = re.search(r'%s'%(possible_match),sample)
                # if found, skip to next must_match
                if found:
                    match_results.append(True)
                    break
            else:
                # if not found, skip to next search
                match_results.append(False)
                break
            # if match with all must_match, store category
        if all(match_results):
            matched_category.append(category)
    if len(matched_category) == 0:
        return 'Unknown'
    elif len(matched_category) == 1:
        return matched_category[0]
    else:
        comb_str = 'Double Matched: '
        for i, category in enumerate(matched_category):
            if i:
                comb_str += ', '
            comb_str += category
        return comb_str


