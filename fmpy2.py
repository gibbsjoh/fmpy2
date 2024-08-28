#!/usr/bin/python3

# fmPy v2.21
########################
#
# Changes in 2.21:
#   1. moved the 'action' parameter outside of the payloadData JSON parameter, to enable a quick webserver test (will be rewritten later)
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

#################################
#  import html stuff if needed  #
#################################
try:
    import htmlSnippets
    extHTMLFile = 1
except:
    extHTMLFile = 1

testToggle = 0
thisVersion = '2.21'
testResultIfOK = 'PLACEHOLDER!'

##########################
#  main() Definition    #
##########################
def main():
    #set the HTML header stuff
    print("Content-type: text/html\n\n")
    form = cgi.FieldStorage()

    if 'action' not in form.keys() and 'payloadData' not in form.keys():
        action = 'noParameters'
    else:
        try:
            action = form.getvalue('action')

        except:
            theWholeMegillah = fpy.parseParameters(form)
            action =  theWholeMegillah[0]


    #parse the form from URL
    # ok now we call the function
    if (action == 'test'):
        theResult = htmlSnippets.htmlHeader + '<br>Self Test<br><br>Success! fmPy2 is installed where specified, and it can be run by the webserver.<br>Version: ' + thisVersion + '<br>' + htmlSnippets.htmlFooter
        print(theResult)
    elif (action == 'noParameters'):
        print('No parameters were passed. We have nothing to do!')
    else:
        try:
            fmWhat = theWholeMegillah[1]
            fmWhere = theWholeMegillah[2]
            #connect to FMS (could even roll this into functions...)
            fms = fpy.fmConnect(fmWhere)
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
