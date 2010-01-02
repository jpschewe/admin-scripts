#!/usr/bin/env python

from optparse import OptionParser
import re
import sys
import textwrap
from email.MIMEText import MIMEText
import smtplib
import os.path

base_virus_dir='/var/lib/amavis/virusmails'

class DroppedMessage:
  '''Information about a particular message that was dropped'''
  def __init__(self):
    self.email_from = ""
    self.filename = ""
    self.date = ""
    self.reason = ""
    self.subject = ""

class BlockedMail:
  '''Container for all blocked mail to an email address'''
  def __init__(self):
    self.email = ""
    self.virus = []
    self.spam = []
    self.other = []

def get_subject(filename):
  '''Get the subject from the message in filename'''
  f = open(os.path.join(base_virus_dir, filename))
  subject = None
  while subject == None:
    line = f.readline()
    if line == '':
      # hit EOF
      f.close()
      return "No Subject"
    subject_match = re.match(r'^Subject: (.*)$', line)
    if subject_match:
      subject = subject_match.group(1)
  f.close()
  return subject

def find_blocked_mail():
  # open logfile
  logfile = open(options.logfile)

  done = False
  while not done:
    line = logfile.readline()

    if line == '':
      # hit EOF
      done = True
    else:
      #line_match = re.search('(?P<date>[A-Z][a-z][a-z]\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*amavis\[\d+\].*Blocked (?P<reason>\w+).* <(?P<from>[^<>]+)> -> (?P<to><[^<>]+>)+, quarantine: (?P<filename>[^,]+), Message-ID:', line)
      line_match = re.match(r'(?P<date>[A-Z][a-z][a-z]\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*amavis\[\d+\].*Blocked (?P<reason>\w+).* <(?P<from>[^<>]+)> -> (?P<to>(<[^<>]+>,?)+), quarantine: (?P<filename>[^,]+), Message-ID:', line)
      if not line_match == None:
        #print "Matched"
        #print "to: " + line_match.group("to")
        #print line
        #print "date:", line_match.group("date"), "reason:", line_match.group("reason"), "from:", line_match.group("from"), "to:", line_match.group("to"), "filename:", line_match.group("filename")
        dropped_message = DroppedMessage()
        dropped_message.email_from = line_match.group("from")
        dropped_message.filename = line_match.group("filename")
        dropped_message.date = line_match.group("date")
        dropped_message.reason = line_match.group("reason")
        dropped_message.subject = get_subject(dropped_message.filename)

        for email in line_match.group("to").lower().split(','):
          match = re.match(r'<?(?P<user>[^@]+)@', email)
          if not match:
            continue
          user = match.group("user")
          #user = email.split('@')[0]
          #print "user #" + user + "#"
          if not re.match("[A-Z0-9._%-]+", user, re.IGNORECASE):
            #print "Invalid user found in to list", user, ", skipping"
            continue

          if not blocked_mail.has_key(user):
            blocked_mail[user] = BlockedMail()
            blocked_mail[user].email = user

          if line_match.group("reason").upper() == "SPAM":
            blocked_mail[user].spam.append(dropped_message)
          elif line_match.group("reason").upper() == "INFECTED":
            blocked_mail[user].virus.append(dropped_message)
          else:
            blocked_mail[user].other.append(dropped_message)
      else:
        print "No match " + line + "\n"
  logfile.close()

  
if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-l", "--logfile", dest="logfile", help="logfile (required)")
  parser.add_option("-c", "--contact", dest="contact", help="contact for restoring mail (default: root)", default="root")
  parser.add_option("-d", "--debug", dest="debug", action="store_true", help="If set, don't send mail, only build the messages", default=False)
  (options, args) = parser.parse_args()

  if options.logfile == None:
    print "A logfile must be specified"
    parser.print_help()
    sys.exit()
    
  blocked_mail = {}
    
  find_blocked_mail()

  smtp = smtplib.SMTP()
  smtp.connect()
  
  # print out a summary
  summary_mail_body = ""
  for k, blocked_mail in blocked_mail.iteritems():
    summary_mail_body += blocked_mail.email + "\n"
    mail_body = ""
    mail_body += "\n".join(textwrap.wrap("This is a digest of the mail blocked for your email account over the past 24 hours.  Each line contains the date the messages was recived, the email address it was sent from, then subject and the filename where the message is quarantined.  If you would like the message recovered, contact " + options.contact + " with the name line indicating which message to recover.  All blocked messages will be deleted after 30 days.  In most cases you can just ignore these messages, however this digest is sent out in case messages are incorrectly blocked."))
    mail_body += "\n\n"
    if len(blocked_mail.virus) > 0:
      line = "Mails blocked for viruses\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.virus:
        line = "  " + message.date + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\n"
        mail_body += line
        summary_mail_body += line
    if len(blocked_mail.spam) > 0:
      line = "Mails blocked as spam\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.spam:
        line = "  " + message.date + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\n"
        mail_body += line
        summary_mail_body += line
    if len(blocked_mail.other) > 0:
      line = "Mails blocked for other reasons\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.other:
        line = "  " + message.date + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\t" + message.reason + "\n"
        mail_body += line
        summary_mail_body += line

    # create a mail message
    msg = MIMEText(mail_body)
    msg['Subject'] = 'Digest of blocked email on mtu.net'
    msg['From'] = options.contact
    msg['To'] = blocked_mail.email

    if options.debug:
      print msg
    else:
      try:
        smtp.sendmail(options.contact, [blocked_mail.email], msg.as_string())
      except: 
        print "Error sending message to %s, will continue with next recipient" % (blocked_mail.email)
    
  msg = MIMEText(summary_mail_body)
  msg['Subject'] = 'Summary Digest of blocked email on mtu.net'
  msg['From'] = options.contact
  msg['To'] = options.contact
  if options.debug:
    print msg
  else:
    smtp.sendmail(options.contact, [options.contact], msg.as_string())
  
  smtp.close()
  
