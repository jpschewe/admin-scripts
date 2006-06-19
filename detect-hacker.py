#!/usr/bin/python

# Usage detect-hacker.py --logfile /var/log/messages --duration 60 --threshold 6

from optparse import OptionParser
import sys
import re
import time
import fpformat
import os

debug = False

# change this to match where your iptables is
iptables = "/usr/sbin/iptables"

# parse the command line
parser = OptionParser()
parser.add_option("-l", "--logfile", dest="logfile", help="logfile (required)")
parser.add_option("-d", "--duration", dest="duration", type="int", help="Number of minutes back to look for failed logins (default 60)")
parser.add_option("-t", "--threshold", dest="threshold", type="int", help="Number of failed logins to be banned (default 6)")
(options, args) = parser.parse_args()

if options.logfile == None:
  print "A logfile must be specified"
  parser.print_help()
  sys.exit()

duration = 60
if not options.duration == None:
  duration = options.duration

threshold = 6
if not options.threshold == None:
  thresold = options.threshold

# keep track of user accounts that count for failed logins
system_accounts = []
passwd_file = open('/etc/passwd')

line = passwd_file.readline()
while not line == '':
  line_match = re.search('^(?P<user>[^:]+):[^:]*:[^:]*:[^:]*:[^:]*:(?P<home>[^:]*)', line)
  if line_match:
    if not re.search('/home', line_match.group('home')):
      system_accounts.append(line_match.group('user'))
  line = passwd_file.readline()
passwd_file.close()

# keep track of failed logins
failed_logins = {}

# calculate date to check after -> now() - (duration + duration/2) minutes (overlap to catch corner cases)
#checkdate = time.time() - (duration * 60 + (duration * 60 / 2))
checkdate = time.time() - (duration * 60)
if debug:
  print "checkdate: " + time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(checkdate)) + " -> " + fpformat.fix(checkdate, 0)
  
# open logfile
logfile = open(options.logfile)

done = False
while not done:
  line = logfile.readline()

  if line == '':
    # hit EOF
    done = True
  else:
    line_match = re.search('(?P<date>[A-Z][a-z][a-z]\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2}).*sshd\[\d+\].*Failed password for (?:(?P<invalid>invalid|illegal) user )?(?P<user>\S+) from (?:::ffff:)?(?P<ip>\S+) port', line)
    if not line_match == None:
      # look forward until find a log entry after checkdate
      year = time.localtime().tm_year
         
      logentry_date_str = time.strptime(line_match.group('date'), '%b %d %H:%M:%S');
      logentry_date = time.mktime( (year, logentry_date_str.tm_mon, logentry_date_str.tm_mday, logentry_date_str.tm_hour, logentry_date_str.tm_min, logentry_date_str.tm_sec, logentry_date_str.tm_wday, -1, -1) )

      # adjust for end of year
      if(time.localtime().tm_mon < time.localtime(logentry_date).tm_mon):
        year = year - 1
        logentry_date = time.mktime( (year, logentry_date_str.tm_mon, logentry_date_str.tm_mday, logentry_date_str.tm_hour, logentry_date_str.tm_min, logentry_date_str.tm_sec, logentry_date_str.tm_wday, -1, -1) )
        
      
      if logentry_date >= checkdate:
        if debug:
          print "logentry_date: " + time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(logentry_date)) + " -> " + fpformat.fix(logentry_date, 0)
        # check if invalid or a system account
        if line_match.group('invalid') or line_match.group('user') in system_accounts:
          # increment counter for ip
          ip = line_match.group('ip')
          if debug:
            print line
          if failed_logins.has_key(ip):
            failed_logins[ip] = failed_logins[ip] + 1
          else:
            failed_logins[ip] = 1
        
logfile.close()


# walk over counters and any counter over threshold gets banned
for ip, count in failed_logins.iteritems():
  if count > threshold:
    time_str = time.strftime('%m/%d/%Y %H:%M:%S')
    msg = "# Automatically blocked " + ip + " on " + time_str + " for " + fpformat.fix(count, 0) + " failed login attempts"
    if not debug:
      hackers = open('/etc/hackers', 'a')
      hackers.write(msg + "\n");
      hackers.write(ip + "\n");
      hackers.close()
    print msg
    if not debug:
      os.system(iptables + " -I INPUT -s " + ip + " -j DROP")
