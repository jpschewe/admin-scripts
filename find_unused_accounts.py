#!/usr/bin/env python

import re
from datetime import *
from finger import finger
import sys

MONTH2NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

def get_last_login(finger_result):
    # figure out which date format is being used
    match = re.search("Last login (?P<day>\w+)\s+(?P<month>\w+)\s+(?P<date>\d+)\s+(?P<hour>\d+):(?P<minute>\d+)\s+(?P<year>\d+)\s+\(\w+\)\s+on", finger_result)
    if match:
        year = int(match.group('year'))
    else:
        year = datetime.now().year
        match = re.search("Last login (?P<day>\w+)\s+(?P<month>\w+)\s+(?P<date>\d+)\s+(?P<hour>\d+):(?P<minute>\d+)\s+\(\w+\)\s+on", finger_result)

    if match:
        # parse out the date
        month = MONTH2NUM[match.group('month')]
        date = int(match.group('date'))
        hour = int(match.group('hour'))
        minute = int(match.group('minute'))
        return datetime(year, month, date, hour, minute)
    elif re.search("Never logged in", finger_result):
        return None
    elif re.search("On since", finger_result):
        return datetime.now()
    else:
        print "Something went wrong with", finger_result
        sys.exit(1)
        return

def get_last_read_mail(finger_result):
    # figure out which date format is being used
    match = re.search("((Unread since)|(Mail last read)) (?P<day>\w+)\s+(?P<month>\w+)\s+(?P<date>\d+)\s+(?P<hour>\d+):(?P<minute>\d+)\s+(?P<year>\d+)\s+\(\w+\)\s+", finger_result)
    if match:
        guess = False
        year = int(match.group('year'))
    else:
        guess = True
        print "Guessing the year"
        year = datetime.now().year
        match = re.search("((Unread since)|(Mail last read)) (?P<day>\w+)\s+(?P<month>\w+)\s+(?P<date>\d+)\s+(?P<hour>\d+):(?P<minute>\d+)\s+\(\w+\)\s+", finger_result)

    if match:
        # parse out the date
        month = MONTH2NUM[match.group('month')]
        date = int(match.group('date'))
        hour = int(match.group('hour'))
        minute = int(match.group('minute'))
        last_login = datetime(year, month, date, hour, minute)
        if last_login > datetime.now():
            print "guessed year wrong "
            # guessed the year wrong, use last year
            year -= 1
            last_login = datetime(year, month, date, hour, minute)
        if guess:
            sys.exit(1)
        return last_login
    elif re.search("Mail forwarded to", finger_result):
        # forwarded email counts as now
        return datetime.now()
    elif re.search("No mail", finger_result):
        # no mail counts as now
        return datetime.now()
    else:
        print "Something went wrong with", finger_result
        sys.exit(1)
        return

def main():
    compare_diff = timedelta(60)
    pass_file = open('/etc/passwd', 'r')
    print "user;last_mail;diff_mail;last_login;diff_login"
    for line in pass_file.readlines():
        fields = line.split(':')
        if re.match('/home', fields[5]):
            user = fields[0]
            finger_result = finger('', user)
            last_login = get_last_login(finger_result)
            if last_login:
                login_diff = datetime.now() - last_login
            else:
                login_diff = "Infinite"
                
            last_read_mail = get_last_read_mail(finger_result)
            mail_diff = datetime.now() - last_read_mail

            
            #print "user;" , last_read_mail.isoformat() , ";" , mail_diff , ";" , last_login , ";" , login_diff
            print "%s;%s;%s;%s;%s" % (user, last_read_mail, mail_diff, last_login, login_diff)
            
            #if mail_diff > compare_diff:
            #    print "Been 2 months since mail last read"

if __name__ == "__main__":
    main()
