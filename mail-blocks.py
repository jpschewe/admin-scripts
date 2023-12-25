#!/usr/bin/env python

from optparse import OptionParser
import re
import sys
import textwrap
from email.MIMEText import MIMEText
import smtplib
import os.path
import glob
import gzip
import os
import datetime

base_virus_dir='/var/lib/amavis/virusmails'

# keep track of user accounts that count for failed logins
system_accounts = []
user_accounts = []
passwd_file = open('/etc/passwd')

line = passwd_file.readline()
while not line == '':
  line_match = re.search('^(?P<user>[^:]+):[^:]*:[^:]*:[^:]*:[^:]*:(?P<home>[^:]*)', line)
  if line_match:
    if not re.search('/home', line_match.group('home')):
      system_accounts.append(line_match.group('user'))
    else:
      user_accounts.append(line_match.group('user'))
  line = passwd_file.readline()
passwd_file.close()


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


def find_blocked_mail(blocked_mail, earliest_timestamp, f):
  """
  @param f the file object to read
  @param blocked_mail hash of user to blocked mail, modified by this method
  @param earliest_timestamp ignore blocked email before this time 
  """

  for line in f:
    #line_match = re.search('(?P<date>[A-Z][a-z][a-z]\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*amavis\[\d+\].*Blocked (?P<reason>\w+).* <(?P<from>[^<>]+)> -> (?P<to><[^<>]+>)+, quarantine: (?P<filename>[^,]+), Message-ID:', line)
    line_match = re.match(r'(?P<date>[A-Z][a-z][a-z]\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*amavis\[\d+\].*Blocked (?P<reason>\w+).* <(?P<from>[^<>]+)> -> (?P<to>(<[^<>]+>,?)+), quarantine: (?P<filename>[^,]+),', line)
    if not line_match == None:
      #print("Matched")
      #print("to: " + line_match.group("to"))
      #print(line)
      #print("date:", line_match.group("date"), "reason:", line_match.group("reason"), "from:", line_match.group("from"), "to:", line_match.group("to"), "filename:", line_match.group("filename"))
      dropped_message = DroppedMessage()
      dropped_message.email_from = line_match.group("from")
      dropped_message.filename = line_match.group("filename")
      
      dropped_message.reason = line_match.group("reason")
      dropped_message.subject = get_subject(dropped_message.filename)

      dropped_message.date = datetime.datetime.strptime(line_match.group("date"), '%b %d %H:%M:%S').replace(year=datetime.date.today().year)
      
      if dropped_message.date > datetime.datetime.now():
        # handle beginning of the year
        dropped_message.date = dropped_message.date.replace(year=(dropped_message.date.year - 1))
        
      if dropped_message.date >= earliest_timestamp:
        for email in line_match.group("to").lower().split(','):
          match = re.match(r'<?(?P<user>[^@]+)@', email)
          if not match:
            continue
          user = match.group("user")
          #user = email.split('@')[0]
          #print("user #" + user + "#")
          if not re.match("[A-Z0-9._%-]+", user, re.IGNORECASE):
            #print("Invalid user found in to list", user, ", skipping")
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

  
if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-l", "--logfile-pattern", dest="logfile_pattern", help="logfile_pattern (required, uses glob matching)")
  parser.add_option("--hours", dest="hours", help="Number of hours to look back from now to find blocked mail. Defaults to 25", default=25)
  parser.add_option("-c", "--contact", dest="contact", help="contact for restoring mail (default: root)", default="root")
  parser.add_option("-d", "--debug", dest="debug", action="store_true", help="If set, don't send mail, only build the messages", default=False)
  (options, args) = parser.parse_args()

  if options.logfile_pattern == None:
    print("A logfile pattern must be specified")
    parser.print_help()
    sys.exit()
    
  blocked_mail = {}

  earliest_timestamp = datetime.datetime.now() - datetime.timedelta(hours=options.hours)
  
  for filename in glob.glob(options.logfile_pattern):
    modtime = os.stat(filename).st_mtime
    mod_timestamp = datetime.datetime.fromtimestamp(modtime)

    if mod_timestamp >= earliest_timestamp:
      if re.search(r'\.gz$', filename):
        with gzip.open(filename, 'rt') as f:
          find_blocked_mail(blocked_mail, earliest_timestamp, f)
      else:
        with open(filename, 'r') as f:
          find_blocked_mail(blocked_mail, earliest_timestamp, f)
      

  smtp = smtplib.SMTP()
  smtp.connect()
  
  # print out a summary
  summary_mail_body = ""
  for k, blocked_mail in blocked_mail.iteritems():
    if not blocked_mail.email in user_accounts:
      continue
    summary_mail_body += blocked_mail.email + "\n"
    mail_body = ""
    mail_body += "\n".join(textwrap.wrap("This is a digest of the mail blocked for your email account over the past 24 hours.  Each line contains the date the messages was recived, the email address it was sent from, then subject and the filename where the message is quarantined.  If you would like the message recovered, contact " + options.contact + " with the name line indicating which message to recover.  All blocked messages will be deleted after 30 days.  In most cases you can just ignore these messages, however this digest is sent out in case messages are incorrectly blocked."))
    mail_body += "\n\n"

    if len(blocked_mail.virus) > 0:
      line = "Mails blocked for viruses\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.virus:
        line = "  " + message.date.strftime("%c") + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\n"
        mail_body += line
        summary_mail_body += line
    if len(blocked_mail.spam) > 0:
      line = "Mails blocked as spam\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.spam:
        line = "  " + message.date.strftime("%c") + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\n"
        mail_body += line
        summary_mail_body += line
    if len(blocked_mail.other) > 0:
      line = "Mails blocked for other reasons\n"
      mail_body += line
      summary_mail_body += line
      for message in blocked_mail.other:
        line = "  " + message.date.strftime("%c") + " " + message.email_from + "\t" + message.subject + "\t" + message.filename + "\t" + message.reason + "\n"
        mail_body += line
        summary_mail_body += line

    # create a mail message
    msg = MIMEText(mail_body)
    msg['Subject'] = 'Digest of blocked email on mtu.net'
    msg['From'] = options.contact
    msg['To'] = blocked_mail.email

    if options.debug:
      print(msg)
    else:
      try:
        smtp.sendmail(options.contact, [blocked_mail.email], msg.as_string())
      except: 
        print("Error sending message to %s, will continue with next recipient" % (blocked_mail.email))
    
  #summary msg = MIMEText(summary_mail_body)
  #summary msg['Subject'] = 'Summary Digest of blocked email on mtu.net'
  #summary msg['From'] = options.contact
  #summary msg['To'] = options.contact
  #summary if options.debug:
  #summary   print(msg)
  #summary else:
  #summary   smtp.sendmail(options.contact, [options.contact], msg.as_string())
  
  smtp.close()
  
