#!/usr/bin/env python

# fmPy v2.2
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

import fmpy-functions


##########################
#  main() Definition    #
##########################
def main():
    #set the HTML header stuff
    print("Content-type: text/html\n\n")
    form = cgi.FieldStorage()

    #parse the form from URL
    theWholeMegillah = parseParameters(form)
    action =  theWholeMegillah[0]

    # change here to appent fmpy-functions to action
    action = 'fmpy-functions.' + action

    fmWhat = theWholeMegillah[1]
    fmWhere = theWholeMegillah[2]

    #connect to FMS (could even roll this into functions...)
    fms = fmConnect(fmWhere)

    # ok now we call the function
    selectedFunction = globals()[action]
    result = selectedFunction(fmWhere,fmWhat,fms)

    print(result)

    #FMS logout for cleanliness
    fms.logout()


##################################################################################
# If you want to just use fmPy on it's own, here's the code block to call main() #
##################################################################################
if __name__ == "__main__":
    main()
