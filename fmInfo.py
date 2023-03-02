#!/usr/bin/env python
# v.12
########################
#
# This is where we keep and functions for fmPy.py and the credentials for the server
#
# 
########################
import os

userName = 'admin'
myPassword = 'password'
eventLogUser = 'someOtherUsrerName'

# any custom functions here

# paths for saving csv files in Windows or Linux
localPath = os.getcwd()
windowsPath = (localPath +'\\files\\')
linuxPath = ('/var/www/html/')

# 21/01/23 - adding selftest function
# the variables below define the connection and query to use 
stServer = 'https://myfm.server.com
stDatabase = 'DAPITest'
stLayout = 'DAPITest'
stUserName = 'admin'
stPassword = 'password'
stQuery =  {'_c1': '1'}
