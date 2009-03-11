#!/usr/bin/env python

import os
import commands

high_water_mark = 0.95

output = commands.getoutput('df -P')
lines = output.split('\n')

points = map(lambda line: " ".join(line.split()[5:]), lines)
    
for mount in points:
    #print "Checking mount '%s'" % (mount)
    if 'Mounted on' != mount:
        disk = os.statvfs(mount)
        capacity = disk.f_bsize * disk.f_blocks
        available = disk.f_bsize * disk.f_bavail
        used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
        percent_used = float(used)/float(capacity)
        
        if percent_used > high_water_mark:
            print("Filesystem %s is close to full: %s%%" % (mount, percent_used * 100))
        #else:
        #    print("Filesystem %s percent used is %s" % (mount, percent_used * 100))
