#!/usr/bin/env python

from optparse import OptionParser
import re
import sys

class DroppedMessage:
  def __init__(self):
    self.email_from = ""
    self.filename = ""
    self.date = ""

class BlockedMail:
  def __init__(self):
    self.email = ""
    self.virus = []
    self.spam = []
    self.other = []
    self.reason = ""


def main():
  parser = OptionParser()
  parser.add_option("-l", "--logfile", dest="logfile", help="logfile (required)")
  parser.add_option("-d", "--duration", dest="duration", type="int", help="Number of hours back to look for blocked messages (default 24)")
  (options, args) = parser.parse_args()

  if options.logfile == None:
    print "A logfile must be specified"
    parser.print_help()
    sys.exit()

  duration = 24
  if not options.duration == None:
    duration = options.duration

  blocked_mail = {}

  # open logfile
  logfile = open(options.logfile)

  done = False
  while not done:
    line = logfile.readline()

    if line == '':
      # hit EOF
      done = True
    else:
      line_match = re.search('(?P<date>[A-Z][a-z][a-z]\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2}).*amavis\[\d+\].*Blocked (?P<reason>\w+).* <(?P<from>[^<>]+)> -> <(?P<to>[^<>]+)>, quarantine: (?P<filename>.*), Message-ID:', line)
      if not line_match == None:
        #print line
        #print "date:", line_match.group("date"), "reason:", line_match.group("reason"), "from:", line_match.group("from"), "to:", line_match.group("to"), "filename:", line_match.group("filename")
        dropped_message = DroppedMessage()
        dropped_message.email_from = line_match.group("from")
        dropped_message.filename = line_match.group("filename")
        dropped_message.date = line_match.group("date")
        dropped_message.reason = line_match.group("reason")

        lc_to = line_match.group("to").lower()
        if not blocked_mail.has_key(lc_to):
          blocked_mail[lc_to] = BlockedMail()
          blocked_mail[lc_to].email = lc_to

        if line_match.group("reason").upper() == "SPAM":
          blocked_mail[lc_to].spam.append(dropped_message)
        elif line_match.group("reason").upper() == "VIRUS":
          blocked_mail[lc_to].virus.append(dropped_message)
        else:
          blocked_mail[lc_to].other.append(dropped_message)
      #else:
      #  print "not match", line

  # print out a summary
  for k, blocked_mail in blocked_mail.iteritems():
    print "Blocked mail for", blocked_mail.email
    print "Mails blocked for viruses" 
    for message in blocked_mail.virus:
      print "\t", message.date, message.email_from, message.filename
    print "Mails blocked for spam" 
    for message in blocked_mail.spam:
      print "\t", message.date, message.email_from, message.filename
    print "Mails blocked for other reasons" 
    for message in blocked_mail.other:
      print "\t", message.date, message.email_from, message.filename, message.reason
      
  
if __name__ == "__main__":
    main()
