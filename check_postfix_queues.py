#!/usr/bin/env python

import os
import sys
import time
import datetime

expanduser = os.path.expanduser
expandvars = os.path.expandvars

def expand( name ): # handle $HOME/pathname or ~user/pathname
  return expandvars( expanduser( name ))

if os.name in ( 'posix', 'dos' ):
  DO_NOT_INCLUDE = ( '.', '..' ) # don't include these for dos & posix
else:
  print "Unknown OS,", os.name, "exiting"
  sys.exit(1);

def find( *paths ):
  list = []
  for pathname in paths:
    os.path.walk( expand(pathname), append, list )
  return list

def append( list, dirname, filelist ):
  for filename in filelist:
    if filename not in DO_NOT_INCLUDE:
      filename = os.path.join( dirname, filename )
      if not os.path.islink( filename ):
        list.append( filename )

def get_queue_lengths():
  """
  Compute the length of each queue and return them as a tuple (active, deferred, hold)
  """
  hold_files = []
  os.path.walk(expand("/var/spool/postfix/hold"), append, hold_files)
  num_hold = len(hold_files)

  active_files = []
  os.path.walk(expand("/var/spool/postfix/active"), append, active_files)
  num_active = len(active_files)

  deferred_files = []
  os.path.walk(expand("/var/spool/postfix/deferred"), append, deferred_files)
  num_deferred = len(deferred_files)

  return (num_active, num_deferred, num_hold)

if __name__ == "__main__":
  threshold = 100
  release = 20
  sleep = 1

  print "Queue lengths active: %d deferred: %d hold: %d" % get_queue_lengths()
  
  #while True:
  #  hold_files = []
  #  os.path.walk(expand("/var/spool/postfix/hold"), append, hold_files)
  #  num_hold = len(hold_files)
  #
  #  active_files = []
  #  os.path.walk(expand("/var/spool/postfix/active"), append, active_files)
  #  num_active = len(active_files)
  #
  #  deferred_files = []
  #  os.path.walk(expand("/var/spool/postfix/deferred"), append, deferred_files)
  #  num_deferred = len(deferred_files)
  #
  #  print datetime.datetime.now(), "hold", num_hold, "active", num_active, "deferred", num_deferred
  #  if num_hold > 0:
  #    if num_active + num_deferred < threshold:
  #      process_files = hold_files[0:min(release, num_hold)]
  #      #print "Process more mail", process_files
  #      for file in process_files:
  #        cmd = "postsuper -H " + os.path.basename(file)
  #        os.system(cmd)
  #        print cmd
  #      os.system("postqueue -f")
  #    print "Waiting for awhile to process -- sleeping", sleep, "minutes"
  #    time.sleep(60 * sleep)
  #  else:
  #    print "No more hold files"
  #    sys.exit(0);
