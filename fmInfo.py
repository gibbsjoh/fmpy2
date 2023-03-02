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
myPassword = 'dance200'
eventLogUser = 'someOtherUsrerName'

# any custom functions here

# paths for saving csv files in Windows or Linux
localPath = os.getcwd()
windowsPath = (localPath +'\\files\\')
linuxPath = ('/var/www/html/')

# 21/01/23 - adding selftest function
# the variables below define the connection and query to use 
stServer = 'https://fmserver.smthng.pw'
stDatabase = 'DAPITest'
stLayout = 'DAPITest'
stUserName = 'admin'
stPassword = 'dance200'
stQuery =  {'_c1': '1'}
