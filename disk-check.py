#!/usr/bin/env python3

import os
import subprocess
import re

high_water_mark = 0.95
# in bytes
minimum_disk_space = 5000000000

output = subprocess.getoutput('/bin/df -P  2>/dev/null')
ignored_mounts = [ '/kern', '/dev/pts', '/proc', '/media', '/archive' ]

lines = output.split('\n')

for line in lines:
    pieces = line.split()
    dev = pieces[0]
    mount = pieces[5]
    #print "Checking mount '%s' dev '%s'" % (mount, dev)
    if 'Mounted' != mount and mount not in ignored_mounts and not re.search(r':', dev) and not mount.startswith('/snap') :
        disk = os.statvfs(mount)
        capacity = disk.f_bsize * disk.f_blocks
        available = disk.f_bsize * disk.f_bavail
        used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
        percent_used = float(used)/float(capacity)
        
        if percent_used > high_water_mark and available < minimum_disk_space:
            print("Filesystem %s is close to full: %s%% avail: %sG" % (mount, percent_used * 100, available / 1024 / 1024 / 1024))
        #else:
        #    print("Filesystem %s percent used is %s" % (mount, percent_used * 100))
