#!/usr/bin/env python

from optparse import OptionParser
import os.path
import sys
import re

if not os.path.isfile(".subscriptions"):
  print "Cannot find .subscriptions in the current directory, you should be in some users home directory"
  sys.exit(1)

if not os.path.isdir("Maildir"):
  os.mkdir("Maildir")
subscriptions_in = file(".subscriptions")
subscriptions_out = file("Maildir/subscriptions", "w")

for mbox_folder in subscriptions_in:
  mbox_folder = mbox_folder.rstrip("\n")
  if os.path.isfile(mbox_folder):
    print "Processing %s" % (mbox_folder)
    maildir_folder = mbox_folder
    maildir_folder = re.sub(r"\.", "_", maildir_folder)
    maildir_folder = re.sub(r"/", ".", maildir_folder)
    print "maildir folder %s" % (maildir_folder)
    os.system("mb2md.py -i \"%s\" -o \"Maildir/.%s\"" % (mbox_folder, maildir_folder))
    subscriptions_out.write("%s\n" % (maildir_folder))
  else:
    print "%s doesn't exist, skipping" % (mbox_folder)
    
  
subscriptions_in.close()
subscriptions_out.close()

print "Don't forget to do /var/spool/mail/ and move the old stuff away as well as edit procmailrc"
