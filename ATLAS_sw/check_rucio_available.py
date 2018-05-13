#!/usr/bin/env python
"""
================================================================================
TODO: Synopsis
Examples
    python <TODO:script name>
TODO: Description (for long scripts)

Author: 
    Alex Armstrong <alarmstr@cern.ch>
TODO: License:
    This script is in the public domain, free from copyrights or restrictions.
    Copyright: (C) <TODO:date>; University of California, Irvine 
================================================================================
"""

import sys, os, traceback, argparse
import time

################################################################################
def main ():
    """ Main Function """
    
    global args
    print "required user input = ", args.req_input
    print "optional user input = ", args.user_input
    print_hello_world()

################################################################################
# FUNCTIONS
def print_hello_world(param=''):
    """ 
    function synopsis 
    args:
        param (type) - description [default: '']
    returns:
        (type) - description
    """
    print "Hello World! " + param
    return True if param else False


################################################################################
# Run main when not imported
if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('req_input', 
                            help='required user input')
        parser.add_argument('-i', '--user_input', 
                            default='default value', 
                            help='optional user input')
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
