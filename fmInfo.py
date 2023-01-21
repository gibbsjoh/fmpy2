#!/usr/bin/env python
# v.12
########################
#
# This is where we keep and functions for fmPy.py and the credentials for the server
#
# 
########################
import os

userName = 'userName'
myPassword = 'somePassword'
eventLogUser = 'someOtherUsrerName'

# any custom functions here

# paths for saving csv files in Windows or Linux
localPath = os.getcwd()
windowsPath = (localPath +'\\files\\')
linuxPath = ('/var/www/html/')