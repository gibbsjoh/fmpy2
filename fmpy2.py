#!/usr/bin/env python

# fmPy v2.1
########################
#
# This is a major-ish update to fmPy based on what I'm learning as I go along.
# main changes:
#
# 1. arranging the various actions into functions so you an call these from your own Python code
# 2. using the __main__ thingy because it's best practice


#############################################################
#  Dependencies for functions/main  #
#####################################
# Import needed modules plus fmInfo
import requests
import fmrest
from fmrest.exceptions import FileMakerError
import json
import cgi
import base64
import urllib.parse
import os

try:
    import pandas # for saving JSON to CSV
    isPanda = 1
except:
    isPanda = 0

import platform 


#################################
#  import the creds for server  #
#################################
import fmInfo

import fmpyfunctions as fpy

testToggle = 0

##########################
#  main() Definition    #
##########################
def main():
    #set the HTML header stuff
    print("Content-type: text/html\n\n")
    form = cgi.FieldStorage()

    #parse the form from URL
    theWholeMegillah = fpy.parseParameters(form)
    action =  theWholeMegillah[0]

    # change here to appent fmpy-functions to action
    #action = 'fmpyfunctions.' + action

    fmWhat = theWholeMegillah[1]
    fmWhere = theWholeMegillah[2]

    #connect to FMS (could even roll this into functions...)
    fms = fpy.fmConnect(fmWhere)

    # ok now we call the function
    if (testToggle == 1):
        result = fpy.updateRecord(fmWhere,fmWhat,fms)
    else:
        try:
            selectedFunction = getattr(fpy, action)
            result = selectedFunction(fmWhere,fmWhat,fms)
            print(result)
        except AttributeError:
            print ('ERROR - function not found')
        #selectedFunction = globals()['fmpyfunctions.'+action]

    #FMS logout for cleanliness
    fms.logout()


##################################################################################
# If you want to just use fmPy on it's own, here's the code block to call main() #
##################################################################################
if __name__ == "__main__":
    main()
