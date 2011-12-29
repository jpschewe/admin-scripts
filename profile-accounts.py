#!/usr/bin/env python

import warnings
with warnings.catch_warnings():
    from optparse import OptionParser
    import sys
    from datetime import datetime
    import re
    import time
    import pickle
    import os.path

DATE_FORMAT = '%Y%m%d'
    
class IntervalInfo:
    '''
    Information about a user for a given day.
    '''
    def __init__(self, username, day):
        self.day = day
        self.username = username
        self.numMailLogins = 0
        self.mailSites = {}
        self.numSshLogins = 0
        self.sshSites = {}

    def addMailLogin(self, site):
        #print "Adding mail login to %s for %s" % (self.username, site)
        self.numMailLogins = self.numMailLogins + 1
        if site in self.mailSites:
            self.mailSites[site] = self.mailSites[site] + 1
        else:
            self.mailSites[site] = 1

    def getNumMailSites(self):
        return len(self.mailSites)

    def getNumMailLogins(self):
        return self.numMailLogins

    def addSshLogin(self, site):
        print "Adding ssh login to %s for %s" % (self.username, site)
        self.numSshLogins = self.numSshLogins + 1
        if site in self.sshSites:
            self.sshSites[site] = self.sshSites[site] + 1
        else:
            self.sshSites[site] = 1

    def getNumSshSites(self):
        return len(self.sshSites)

    def getNumSshLogins(self):
        return self.numSshLogins

intervals = {}
def getIntervals(username):
    '''
    day -> IntervalInfo
    '''
    if username not in intervals:
        intervals[username] = {}
    return intervals[username]
    
def getInterval(username, day):
    dayIntervals = getIntervals(username)
    if day not in dayIntervals:
        dayIntervals[day] = IntervalInfo(username, day)
    return dayIntervals[day]

def processMailLog(intervalStart, intervalEnd, mailLog):
    for line in file(mailLog):
        match = re.match(r'(?P<date>[A-Z][a-z][a-z]\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2}).*postfix/smtpd.*: client=\S+\[(?P<ip>[^\]]+)\],.*sasl_username=(?P<user>\S+)', line)
        if not match:
            continue
        
        # look forward until find a log entry after checkdate
        year = time.localtime().tm_year
        date_str = str(year) + " " + match.group('date')
        logentry_date_str = time.strptime(date_str, '%Y %b %d %H:%M:%S');
        logentry_date = datetime(year, logentry_date_str.tm_mon, logentry_date_str.tm_mday)

        # adjust for end of year
        if(time.localtime().tm_mon < logentry_date.month):
            year = year - 1
            logentry_date = datetime(year, logentry_date.month, logentry_date.day)

        if intervalStart <= logentry_date and logentry_date < intervalEnd:
            interval = getInterval(match.group('user'), logentry_date)
            interval.addMailLogin(match.group('ip'))

def processSshLog(intervalStart, intervalEnd, mailLog):
    for line in file(mailLog):
        match = re.match(r'(?P<date>[A-Z][a-z][a-z]\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2}).*sshd.*: Accepted.*for (?P<user>\S+) from (?P<ip>\S+)', line)
        if not match:
            continue
        
        # look forward until find a log entry after checkdate
        year = time.localtime().tm_year
        date_str = str(year) + " " + match.group('date')
        logentry_date_str = time.strptime(date_str, '%Y %b %d %H:%M:%S');
        logentry_date = datetime(year, logentry_date_str.tm_mon, logentry_date_str.tm_mday)

        # adjust for end of year
        if(time.localtime().tm_mon < logentry_date.month):
            year = year - 1
            logentry_date = datetime(year, logentry_date.month, logentry_date.day)

        if intervalStart <= logentry_date and logentry_date < intervalEnd:
            interval = getInterval(match.group('user'), logentry_date)
            interval.addSshLogin(match.group('ip'))

def loadData(datafile):
    if os.path.exists(datafile):
        print "Loading data"
        f = file(datafile)
        i = pickle.load(f)
        f.close()
        intervals.update(i)

def saveData(datafile):
    output = file(datafile, 'w')
    pickle.dump(intervals, output, 2)
    output.close()

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = OptionParser()
    parser.add_option("-s", "--ssh", dest="ssh_log", action="append", help="ssh logfile")
    parser.add_option("-m", "--mail", dest="mail_log", action="append", help="mail logfile")
    parser.add_option("-b", "--interval-begin", dest="interval_begin", help="Begin of interval to analyze [YYYYmmdd] (required)")
    parser.add_option("-e", "--interval-end", dest="interval_end", help="End of interval to analyze [YYYYmmdd] (required)")
    parser.add_option("-d", "--data", dest="datafile", help="The datafile to store the data in and load from (required)")

    (options, args) = parser.parse_args(argv)
    if not options.interval_begin:
        print "Interval begin must be specified"
        parser.print_help()
        sys.exit(1)
    if not options.interval_end:
        print "Interval end must be specified"
        parser.print_help()
        sys.exit(1)
    if not options.datafile:
        print "Datafile must be specified"
        parser.print_help()
        sys.exit(1)

    loadData(options.datafile)

    intervalStart = datetime.strptime(options.interval_begin, DATE_FORMAT)
    intervalEnd = datetime.strptime(options.interval_end, DATE_FORMAT)
    print "Processing over interval [%s, %s)" % (intervalStart, intervalEnd)

    if options.mail_log:
        for log in options.mail_log:
            processMailLog(intervalStart, intervalEnd, log)
            
    if options.ssh_log:
        for log in options.ssh_log:
            processSshLog(intervalStart, intervalEnd, log)

    saveData(options.datafile)
    
    # DEBUG
    for username in intervals.keys():
        print username
        dayIntervals = getIntervals(username)
        for day, interval in dayIntervals.iteritems():
            print "  %s numLogins: %d numSites: %d sshLogins: %d sshSites: %d" % (day, interval.getNumMailLogins(), interval.getNumMailSites(), interval.getNumSshLogins(), interval.getNumSshSites())
        
if __name__ == "__main__":
    sys.exit(main())
    
