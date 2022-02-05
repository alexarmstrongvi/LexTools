#!/usr/bin/env pytho

import argparse
import sys, os
import urllib2
import json

SCOPE = 'mc15_13TeV'
DID = 'mc15_13TeV.364513.Sherpa_222_NNPDF30NNLO_tautaugamma_pty_70_140.merge.AOD.e5982_s2726_r7772_r7676'
URL = 'https://rucio.cern.ch/dids/%s/%s'%(SCOPE, DID)
HEADERS = {
    'Accept': 'application/json',
    'Content-Type':'application/json',
    'User-Agent':'User-Agent: curl/7.43.0'
}

def get_request(did, user):
    pars = {
        'DID' : did,
        'username' : user,
    }
    url = URL + urllib.urlencode(pars)
    return urllib2.Request(URL, headers=HEADERS)
    

def get_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    userenv = 'RUCIO_ACCOUNT' if 'RUCIO_ACCOUNT' in os.environ else 'USER'
    parser.add_argument('-u','--user', default='alarmstr')
    parser.add_argument('-d','--did')
    
    args = parser.parse_args()
    return args

def run():
    args = get_args()

    req = get_request(args.did, args.user)
    reply = urllib2.urlopen(req).read().decode('utf-8')
    datasets = json.loads(reply)
    print datasets


if __name__ == '__main__':
    run()
