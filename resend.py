#!/usr/bin/env python

# resend mail from a unix mailbox to a specified user

from optparse import OptionParser
import mailbox, smtplib, sys, time, string, re
import check_postfix_queues

# max number of messages
threshold = 100

def main(mb, smtp_server):
  # do the work  
  count = 0
  errors = 0
  msg = mb.next()
  count = count + 1
  while msg is not None:
     document = msg.fp.read()
     headers = msg.__str__( )
     # remove Delivered-To headers
     new_headers = ""
     for line in headers.splitlines(True):
       if not line.startswith("Delivered-To"):
         new_headers += line
         
     fullmsg = new_headers + '\x0a' + document

     try:
       print "%d Sending mail From: %s on date: %s" % (count, msg.getaddr('From')[1], msg['Date'])
       server = smtplib.SMTP(smtp_server)
       server.set_debuglevel(False)
       server.sendmail(msg.getaddr('From')[1], options.email, fullmsg)
       server.quit()
       # for debugging
       #print fullmsg
     except:
       print "Error sending message %d" % (count)
       print "Exception: ", sys.exc_info()[0]
       errors = errors + 1

     # check queue size before continuing
     if "localhost" == smtp_server:
       (num_active, num_deferred, num_hold) = check_postfix_queues.get_queue_lengths()
       sleep_time = 1
       print "Active: %d Deferred: %d" % (num_active, num_deferred)
       while num_active + num_deferred > threshold:
         time.sleep(sleep_time)
         (num_active, num_deferred, num_hold) = check_postfix_queues.get_queue_lengths()
         print "Active: %d Deferred: %d" % (num_active, num_deferred)
         sleep_time = sleep_time + 1
     else:
       time.sleep(5)

     # go to next message
     msg = mb.next()
     count = count + 1

       
  print "Attempted to send %d messages, received %d errors" % (count, errors)

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-m", "--mailbox", dest="mailbox", help="mailbox (this or maildir is required)")
  parser.add_option("-d", "--maildir", dest="maildir", help="mailbox (this or mailbox is required)")
  parser.add_option("-e", "--email", dest="email", help="destination email address (required)")
  parser.add_option("-s", "--smtp", dest="smtp", help="smtp server (default: localhost)")
  (options, args) = parser.parse_args()

  # check options
  if options.email == None:
    print "An email address must be specified"
    parser.print_help()
    sys.exit()

  if options.smtp == None:
    smtp_server = "localhost"
  else:
    smtp_server = options.smtp

  if options.mailbox:
    mb = mailbox.PortableUnixMailbox(file(options.mailbox))
  elif options.maildir:
    mb = mailbox.Maildir(file(options.maildir))
  else:
    print "A mailbox must be specified via mailbox or maildir"
    parser.print_help()
    sys.exit()
    
  
  main(mb, smtp_server)
