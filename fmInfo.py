#!/usr/bin/env python
# v.12
########################
#
# Variables that aren't functions live here, such as:
# Credentials for the data api on your FM server(s)
# path to export files to
# Self-test server info/cred
#
# 
########################
import os

userName = 'data_api'
myPassword = 'Qu4rk5B4r?'
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
stUserName = 'testUser'
stPassword = 'myPassword'
stQuery =  {'_c1': '1'}
