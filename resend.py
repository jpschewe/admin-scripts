#!/usr/bin/env python

# resend mail from a unix mailbox to a specified user

from optparse import OptionParser
import mailbox, smtplib, sys, time, string, re

def main():
  # do the work  
  mb = mailbox.PortableUnixMailbox(file(options.mailbox))
  server = smtplib.SMTP(smtp_server)
  #server.set_debuglevel(1)
  msg = mb.next()
  while msg is not None:
     document = msg.fp.read()
     headers = msg.__str__( )
     # remove Delivered-To headers
     new_headers = ""
     for line in headers.splitlines(True):
       if not line.startswith("Delivered-To"):
         new_headers += line
         
     fullmsg = new_headers + '\x0a' + document
     print "Sending mail from", msg.getaddr('From')[1]
     server.sendmail(msg.getaddr('From')[1], options.email, fullmsg)
     print fullmsg
     msg = mb.next()

     # should check queue size here
     time.sleep(1)
  server.quit()

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-m", "--mailbox", dest="mailbox", help="mailbox (required)")
  parser.add_option("-e", "--email", dest="email", help="destination email address (required)")
  parser.add_option("-s", "--smtp", dest="smtp", help="smtp server (default: localhost)")
  (options, args) = parser.parse_args()

  # check options
  if options.mailbox == None:
    print "A mailbox must be specified"
    parser.print_help()
    sys.exit()

  if options.email == None:
    print "An email address must be specified"
    parser.print_help()
    sys.exit()

  if options.smtp == None:
    smtp_server = "localhost"
  else:
    smtp_server = options.smtp

  main()
