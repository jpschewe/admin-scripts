#!/usr/bin/env python3

import warnings
with warnings.catch_warnings():
    from optparse import OptionParser
    import sys
    from datetime import datetime
    import re
    import time
    import math
    import gzip
    from pathlib import Path
    import csv

DATE_FORMAT = '%Y%m%d'
DATETIME_FORMAT='%Y-%m-%d %H:%M:%S'

class Stats:
    '''
    Keep track of some statistics
    '''
    def __init__(self):
        self.sum = 0
        self.count = 0
        self.sumSquares = 0

    def addData(self, value):
        self.sum = self.sum + value
        self.count = self.count + 1
        self.sumSquares = self.sumSquares + (value * value)

    def average(self):
        if self.count == 0:
            return 0
        else:
            return self.sum / self.count

    def stddev(self):
        if self.count < 2:
            return 0
        else:
            average = self.average()
            return math.sqrt(1 / (self.count - 1) * (self.sumSquares - (self.count * average * average)))

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
        #print("Adding mail login to %s for %s" % (self.username, site))
        self.numMailLogins = self.numMailLogins + 1
        if site in self.mailSites:
            self.mailSites[site] = int(self.mailSites[site]) + 1
        else:
            self.mailSites[site] = 1

    def getNumMailSites(self):
        return len(self.mailSites)

    def getNumMailLogins(self):
        return self.numMailLogins

    def getMailSites(self):
        return self.mailSites.keys();

    def addSshLogin(self, site):
        #print("Adding ssh login to %s for %s" % (self.username, site))
        self.numSshLogins = self.numSshLogins + 1
        if site in self.sshSites:
            self.sshSites[site] = int(self.sshSites[site]) + 1
        else:
            self.sshSites[site] = 1

    def getNumSshSites(self):
        return len(self.sshSites)

    def getNumSshLogins(self):
        return self.numSshLogins

    def getSshSites(self):
        return self.sshSites.keys();

intervals = dict()
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

def getKnownUsers():
    return intervals.keys()

def openFile(filename):
    '''
    If the file ends with ".gz", then open with gzip module, otherwise open directly
    '''
    # encoding option to handle odd characters
    # https://stackoverflow.com/questions/19699367/for-line-in-results-in-unicodedecodeerror-utf-8-codec-cant-decode-byte
    if filename.endswith('.gz'):
        return gzip.open(filename, 'rt', encoding = "ISO-8859-1")
    else:
        return open(filename, encoding = "ISO-8859-1")
    
def processMailLog(intervalStart, intervalEnd, mailLog):
    for line in openFile(mailLog):
        match = re.match(r'(?P<date>[A-Z][a-z][a-z]\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2}).*postfix/smtpd.*: client=\S+\[(?P<ip>[^\]]+)\],.*sasl_username=(?P<user>[a-zA-Z0-9_\-.%+]+)', line)
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
    for line in openFile(mailLog):
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

def outsideProfile(average, stddev, intervalAverage):
    '''
    Check if the data is outside profile.
    '''
    if intervalAverage > 0 and average == 0:
        return True
    elif average > 0 and intervalAverage > average and intervalAverage - average > (3 * stddev):
        return True
    else:
        return False
    
def analyzeData(username, intervalStart, intervalEnd, verbose):
    mailLogin = Stats()
    mailLoginInterval = Stats()
    mailSites = Stats()
    rawMailSites = set()
    mailSitesInterval = Stats()
    rawMailSitesInterval = set()
    sshLogin = Stats()
    sshLoginInterval = Stats()
    sshSites = Stats()
    rawSshSites = set()
    sshSitesInterval = Stats()
    rawSshSitesInterval = set()
    
    if verbose:
        print(username)
    for day, interval in getIntervals(username).items():
        if intervalStart <= day and day < intervalEnd:
            mailLoginInterval.addData(interval.getNumMailLogins())
            mailSitesInterval.addData(interval.getNumMailSites())
            rawMailSitesInterval = rawMailSitesInterval.union(interval.getMailSites())
            sshLoginInterval.addData(interval.getNumSshLogins())
            sshSitesInterval.addData(interval.getNumSshSites())
            rawSshSitesInterval = rawSshSitesInterval.union(interval.getSshSites())
        else:
            mailLogin.addData(interval.getNumMailLogins())
            mailSites.addData(interval.getNumMailSites())
            rawMailSites = rawMailSites.union(interval.getMailSites())
            sshLogin.addData(interval.getNumSshLogins())
            sshSites.addData(interval.getNumSshSites())
            rawSshSites = rawSshSites.union(interval.getSshSites())
            
    if verbose:
        print("Mail Login Average: %d interval average: %d" % (mailLogin.average(), mailLoginInterval.average()))
        print("Mail Site Average: %d interval average: %d" % (mailSites.average(), mailSitesInterval.average()))
        print("Mail Sites {0}".format(" ".join(rawMailSites)))
        print("Ssh Login Average: %d interval average: %d" % (sshLogin.average(), sshLoginInterval.average()))
        print("Ssh Site Average: %d interval average: %d" % (sshSites.average(), sshSitesInterval.average()))
        print("Ssh Sites {0}".format(" ".join(rawSshSites)))

    if outsideProfile(mailLogin.average(), mailLogin.stddev(), mailLoginInterval.average()):
        print("Number of mail logins is outside of profile for %s: %d normal: %d" % (username, mailLoginInterval.average(), mailLogin.average()))

    if outsideProfile(mailSites.average(), mailSites.stddev(), mailSitesInterval.average()):
        print("Number of mail sites is outside of profile for %s: %d normal: %d" % (username, mailSitesInterval.average(), mailSites.average()))
        print("\tSites {0}".format(" ".join(rawMailSitesInterval)))
        
    if outsideProfile(sshLogin.average(), sshLogin.stddev(), sshLoginInterval.average()):
        print("Number of ssh logins is outside of profile for %s: %d normal: %d" % (username, sshLoginInterval.average(), sshLogin.average()))
        
    if outsideProfile(sshSites.average(), sshSites.stddev(), sshSitesInterval.average()):
        print("Number of ssh sites is outside of profile for %s: %d normal: %d" % (username, sshSitesInterval.average(), sshSites.average()))
        print("\tSites {0}".format(" ".join(rawSshSitesInterval)))
        


def decode_dict(s):
    if s and len(s) > 0:
        return {x.split('_')[0]: x.split('_')[1] for x in s.split(';')}
    return dict()


def encode_dict(d):
    return ';'.join(['%s_%s' % (k, v) for k,v in d.items()])
     

def loadData(datafile):
    path = Path(datafile)
    if path.exists():
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['user']
                date = datetime.strptime(row['date'], DATETIME_FORMAT)
                interval = IntervalInfo(username, date)
                interval.numMailLogins = int(row['numMailLogins'])
                interval.mailSites = decode_dict(row['mailSites'])
                interval.numSshLogins = int(row['numSshLogins'])
                interval.sshSites = decode_dict(row['sshSites'])

                user_data = intervals.get(username, dict())
                user_data[date] = interval
                intervals[username] = user_data


def saveData(datafile):
    with open(datafile, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['user', 'date', 'numMailLogins', 'mailSites', 'numSshLogins', 'sshSites'])
        for user, user_data in intervals.items():
            for d, interval in user_data.items():
                mail_str = ';'.join(['%s_%s' % (k, v) for k,v in interval.mailSites.items()])
                ssh_str = ';'.join(['%s_%s' % (k,v) for k,v in interval.sshSites.items()])
                writer.writerow([user, datetime.strftime(d, DATETIME_FORMAT), interval.numMailLogins, mail_str, interval.numSshLogins, ssh_str])


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = OptionParser()
    parser.add_option("-b", "--interval-begin", dest="interval_begin", help="Begin of interval to analyze [YYYYmmdd] (required)")
    parser.add_option("-e", "--interval-end", dest="interval_end", help="End of interval to analyze [YYYYmmdd] (required)")
    parser.add_option("-d", "--data", dest="datafile", help="The datafile to store the data in and load from (required)")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true", help="Quiet output")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")

    (options, args) = parser.parse_args(argv)
    if not options.interval_begin:
        print("Interval begin must be specified")
        parser.print_help()
        sys.exit(1)
    if not options.interval_end:
        print("Interval end must be specified")
        parser.print_help()
        sys.exit(1)
    if not options.datafile:
        print("Datafile must be specified")
        parser.print_help()
        sys.exit(1)

    loadData(options.datafile)

    intervalStart = datetime.strptime(options.interval_begin, DATE_FORMAT)
    intervalEnd = datetime.strptime(options.interval_end, DATE_FORMAT)
    if not options.quiet:
        print("Processing over interval [%s, %s)" % (intervalStart, intervalEnd))

    if args:
        for log in args:
            processMailLog(intervalStart, intervalEnd, log)
            processSshLog(intervalStart, intervalEnd, log)

    if args:
        saveData(options.datafile)

    for username in getKnownUsers():
        analyzeData(username, intervalStart, intervalEnd, options.verbose)

if __name__ == "__main__":
    sys.exit(main())
    
