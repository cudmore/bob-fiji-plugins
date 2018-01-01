# run this from OSX command line
# it will spawn fiji a number of times and run a plugin
# 
# start by running a multistack reg plugin for each spawned fiji instance

# to run a fiji plugin from command line
'''
/Users/cudmore/Fiji_20161212.app/Contents/MacOS/ImageJ-macosx --jython /Users/cudmore/Dropbox/bob_fiji_plugins/playground/testspawn_.py p1 p2 p3
'''

import threading
import os, math, glob
import time # debugging
import subprocess

fijiPath = '/Users/cudmore/Fiji_20161212.app/Contents/MacOS/ImageJ-macosx'
plugin = '/Users/cudmore/Dropbox/bob_fiji_plugins/playground/testspawn_.py'
args = 'p1 p2 p3'

cmd = fijiPath + ' --allow-multiple --jython ' + plugin + ' ' + args

print '=== calling subprocess.Popen'
print 'cmd;', cmd

p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)

print 'return:'
for line in p.stdout.readlines():
	print line,

print 'done commandline_test.py'
