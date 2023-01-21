#!/usr/bin/env python

# fmPy v2.0a1
########################
#
# This is a major-ish update to fmPy based on what I'm learning as I go along.
# main changes:
#
# 1. arranging the various actions into functions so you an call these from your own Python code
# 2. using the __main__ thingy because it's best practice
#
# --------------
#
# fmPy is a set of functions and example code to leverage the FileMaker (Claris) Data API
#
# At present the function expect a parameter passed as "payloadData", a URLencoded JSON array with the following:
#  NOTE!! This has changes from fmPy 1.5 and below! We now pass 2 arrays within payloadData, "fmWhere" and "fmWhat"
#  This makes it a bit easier to understand
#  fmWhere is the serverName, databaseName, layoutName and action
#  fmWhat is the data for the relevant action
#  don't worry! the old format array is still supported (see main())
#
#   fmWhere:
#   action (see actions below)
#   serverName -> FQDN or IP of your server, however it needs to be. Ex: https://myserver.example.com
#   databaseName -> the solution name eg Inventory
#   layoutName -> Data API needs a layout.
#   OPTIONAL for GetRecord: keyField. If keyField is specified, the returned array will use the value of that field for each
#     record as the key, like this: {"keyFieldValue": {"FileName": "FileMaker18Mac.zip", "Description": "FileMaker 18 Mac Installer", "zf_Enabled": 1, "recordId": "1", "modId": "4"}}
#     OTHERWISE the array uses numbers from 0 for the key
#
#   fmWhat:
#   scriptName - required for runScript
#   beyond that you can include anything - generally speaking it's the fields you want to set or query or pass to the script on the FM side. This is passed right through.
# 
# 
#
# It has a number of actions "pre packaged" - these are:
#
# a. getRecord - returns a JSON array w/ fields and values for the given query - query passed in the 'data' array. You can specify 'keyField' in the fmWhere array and it will use this for the key for the results
#   returns a JSON array w/ results OR an error code
#
# b. createRecord - creates a record in the specified table and sets fields based on the 'data' array sent
#   returns "000 OK" if successful or the FileMaker error if not
#
# c. updateRecord - updates a record specified by a field:value pair with the data in 'data' - requires a primary key and value pair in fmWhat called "pk" and "uuid"
#   returns "000 OK" if successful or the FileMaker error if not
#
# c. runScript - runs a script with script name and parameters to be passed in 'data'
#
#
# d. saveFile - not strictly a FileMaker Data API "thing" but I found it useful - pass it a file as Base64 and it'll save to a path. Doesn't seem to like files > 3MB tho
# 
#
# Some non-data related functions to verify that things are working on the webserver:
# aa. version - returns the version specified in the "version" variable
# bb. test - returns some basic HTML text with the server name & OS
#
# This file needs a file called fmInfo.py from which it will get :
#   the credentials for the server
#   some custom functions
# All the user-specific stuff is in fmInfo.py so you hopefully shouldn't need to edit anything here
#
# The idea is to invoke this script on your web server by using Insert From URL.
# The result will be "OK" if successful or an error if not.
#
# See FMPython.fmp12 for example code
#
# It's always a good idea to make sure your Data API user (the one in fmInfo.py) has as few rights as possible
#
# This uses the python-fmrest package by David Hamann
#   https://github.com/davidhamann/python-fmrest
#
# The github repo for this is https://github.com/gibbsjoh/fmPy
#
########################

#####################################
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
import threading # used to check if we are running within a specific function
from threading import Thread

#################################
#  import the creds for server  #
#################################
import fmInfo

#####################################
#  set the data api timeout higher  #
#####################################
fmrest.utils.TIMEOUT = 300

##########################
#  Function Definitions  #
##########################

def parseParameters(form):
    payloadRaw = form.getvalue('payloadData')
    try:
        payloadClean = urllib.parse.unquote(payloadRaw) # replaces URL encloding such as '%20'
        formJSON = json.loads(payloadClean) # loads the data into a JSON array
        formError = 0
    except:
        formError = 1
    
    # when calling the old fmPy we used a different schema, so map new schema to old if needed
    if(formError == 0):
        try:
            fmWhat = formJSON['fmWhat']
            fmWhere = formJSON['fmWhere']
            dataSchema = 'new'
            action = fmWhere['action']
        except:
            #assemble 'fmWhere'
            action = formJSON['action']
            serverName = formJSON['serverName']
            databaseName = formJSON['databaseName']
            layoutName = formJSON['layoutName']
            fmWhere = {'action':action,'serverName':serverName,'databaseName':databaseName,'layoutName':layoutName}

            #assemble 'fmWhat'
            fmWhat = formJSON['data']
            dataSchema = 'old'
    else:
        action = "parameterMissing"
        fmWhat = {}
        fmWhere = {}
    return (action, fmWhat, fmWhere)

def fmConnect(fmWhere):
    # connect to FileMaker API
    fms = fmrest.Server(fmWhere['serverName'],
                user = fmInfo.userName,
                password = fmInfo.myPassword,
                database = fmWhere['databaseName'],
                layout = fmWhere['layoutName'],
                verify_ssl = False
        )
    fms.login()
    return fms

def getRecord(fmWhere,fmWhat,fms):
    try:
        calledFromCSV = fmWhere['calledFromCSV']
    except:
        calledFromCSV = None
        returnArray = {}
    #see if there's a key field in the fmWhere
    try:
        keyField = fmWhere['keyField']
    except:
        keyField = None
    try:
        fmResultRaw = fmWhere['fmResultRaw']
    except:
        fmResultRaw = 0
    #set up query
    find_query = [fmWhat]
    try:
        fmResult = fms.find(query=find_query,limit=40000)
        success = 1
    except FileMakerError as findError:
        fmResult = findError
        success = 0
    if(success == 1):
        if(fmResultRaw == 1):
            fmResult = {'data':fmResult}
        else:
            dataArray = []
            #thisData = {}
            i = 0
            for r in fmResult:
                thisRecord = fmResult[i]
                if keyField is not None:
                    keyFieldValue = thisRecord[keyField]
                else:
                    keyFieldValue = i
                f = {}
                keys = thisRecord.keys()
                for key in keys:
                    # get the value for the field
                    value = thisRecord[key]
                    f[key] = value
                if calledFromCSV is None:
                    #legacy method 
                    returnArray[keyFieldValue] = f
                else:
                    #new method that returns list under 'data'
                    dataArray.append(f)
                
                i = i + 1
   
            #returnArray = {'data':dataArray}
            if calledFromCSV is not None:
                returnArray = {'data':dataArray}
            fmResult = json.dumps(returnArray)

    return fmResult

def getRecordToCSV(fmWhere,fmWhat,fms):
    #saves the record to a CSV file 
    #add calledFromCSV to fmWhere
    fmWhere['calledFromCSV'] = 1
    theData = getRecord(fmWhere,fmWhat,fms)

    thisPlatform = platform.system()
    tableName = fmWhere['layoutName']
    if thisPlatform == 'Windows':
        localPath = os.getcwd()
        jsonFilePath = ('c:\\temp\\'+tableName+'.json')
        #csvFilePath = ('c:\\Program Files\\FileMaker\\FileMaker Server\\HTTPServer\\conf\\testing\\fmpy2\\'+tableName+'.csv')
        csvFilePath = (localPath +'\\files\\'+tableName+'.csv')
        downloadLink = ('https://wbv-fmr-p0004.systems.private/files/'+tableName+'.csv')
    elif thisPlatform == 'Linux':
        csvFilePath = ('/app/website/html/'+tableName+'.csv')
        jsonFilePath = ('/app/website/html/'+tableName+'.json')
        downloadLink = ('https://fmr-wb-p1.systems.private/files/'+tableName+'.csv')

    #open text file
    text_file = open(jsonFilePath, "w")
    #write string to file
    text_file.write(str(theData))
    #close file        #csvFilePath = ('c:\\Program Files\\FileMaker\\FileMaker Server\\HTTPServer\\conf\\testing\\fmpy2\\'+tableName+'.csv')

    text_file.close()

    # save as a csv
    try:
        theCSV = pandas.read_json(jsonFilePath,orient='split')
        csvResult1 = "Read OK"
    except:
        csvResult1 = "Read Error"
    
    try:
        theCSV.to_csv(csvFilePath, index = None)
        csvResult2 = "Write OK"
    except:
        csvResult2 = 'Write Error'

    # delete the JSON file for security
    deleteMe = os.remove(jsonFilePath)
    
    csvResultError = (csvResult1+' '+csvResult2)
    csvResultOK = downloadLink
    
    if 'Error' in csvResultError:
        return csvResultError
    else:
        return csvResultOK

def createRecord(fmWhere,fmWhat,fms):
    try:
        recordCreate = fms.create_record(fmWhat)
        fmResult = recordCreate
    except FileMakerError as createError:
        fmResult = createError
    return fmResult

def updateRecord(fmWhere,fmWhat,fms):
    uuid = fmWhat['uuid']
    pk = fmWhat['pk']
    keys = fmWhat.keys()
    # #remove the uuid and pk values from the JSON
    # o = json.loads(fmWhat)
    # del o['pk']
    # del o['uuid']
    # output_string = json.dumps(o)

    find_query = [{ pk : uuid}]
    try:
        foundset = fms.find(query=find_query)
        success = 1
    except FileMakerError as findError:
        fmResult = findError
    if success == 1:
        record = foundset[0]
        for key in keys:
            if key != 'pk' and key != 'uuid':
                value = fmPayload[key]
                record[key] = value
        try:
            fms.edit(record)
            fmResult = '000 OK'
        except FileMakerError as updateError:
            fmResult = updateError

def createRecordMulti(fmWhere,fmWhat,fms):
    #as createRecord but allows for multiple records to be created. fmWhat should have numbered keys starting at 0, with
    # data formatted in the same way within each
    # like this:
    keys = fmWhat.keys()
    i = 0
    for key in keys:
        iString = str(i)
        addArray = fmWhat[iString]
        try:
            fmResult = fms.create_record(addArray)
        except FileMakerError as createError:
            fmResult = createError
        i = i + 1
    return (i)


def runScript(fmWhere,fmWhat,fms):
    scriptName = fmWhat['fmScript']
    try:
        fmScriptParameter = fmWhat['fmScriptParameter']
        fmScriptParameter = json.dumps(fmScriptParameter)
    except:
        fmScriptParameter = ''
    uuid = fmWhat['uuid']
    pk = fmWhat['pk']
    find_query = [{ pk : uuid}]
    try:
        foundSet = fms.find(query=find_query,scripts={'after': [scriptName, fmScriptParameter]})
        fmResult = fms.last_script_result
    except FileMakerError as runScriptError:
        fmResult = runScriptError,fmScriptParameter
    return fmResult


def saveFile(fmWhere,fmWhat):
    return "foo"

def version(fmWhere,fmWhat):
    return "fmPy v2.0a1"

def parameterMissing(fmWhere,fmWhat):
    return "No parameter supplied, or it isn't loadable as JSON."

def test(fmWhere,fmWhat):
    fmWhereString = json.dumps(fmWhere)
    fmWhatString = json.dumps(fmWhat)
    returnString = 'fmWhere<br>'+fmWhereString+'<br><br>fmWhat<br>'+fmWhatString
    return returnString

def gpar(fmWhere,fmWhat,fms):
    print('RIP Coolio 29/09/2022<BR><IMG SRC=https://wbv-fmr-p0004.systems.private/img/coolio.jpg />')

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


exit()


# initialise error var
fmError = 'OK'

# set timeout higher
fmrest.utils.TIMEOUT = 300

#initialise f array
f = {'foo':'bar'}

# This seems needed for the FMRest stuff
requests.packages.urllib3.disable_warnings()

# The encoded array is sent as part of the URL, so get it into the script


# if (payloadRaw[0] == "{"):
#     #not encoded
#     notJSON = 1
#     payloadData = payloadRaw
# else:
#     notJSON = 0
#     p = base64.b64decode(payloadRaw)
#     payloadData = p.decode('utf-8')

# debugging
#print(payloadData)
#exit()

# what are we doing?
action = formJSON['action']
# where are we doing it?
serverName = formJSON['serverName']
databaseName = formJSON['databaseName']
layoutName = formJSON['layoutName']

# Get our user creds
#   If you have different users for different files, change the userName variable to maybe userNameSolutionName
if databaseName == 'FMEventLog':
    userName = fmInfo.eventLogUser
else:
    userName = fmInfo.userName
myPassword = fmInfo.myPassword

# Connnect to the FileMaker server
fms = fmrest.Server(serverName,
                user = userName,
                password = myPassword,
                database = databaseName,
                layout = layoutName,
                verify_ssl = False
        )
fms.login()

# What are we doing? Get the data element of the JSON array
fmPayload = formJSON['data']

# Get the keys (our fieldnames for FileMaker)
keys = fmPayload.keys()

#now we do something with it!
if (action == "createRecord"): #create a new record w/ values we've passed it.
    #print(action)
    #The below isn't needed..
    # f = {}
    # for key in keys:
    #     # get the value for the field
    #     value = fmPayload[key]
    #     f[key] = value
    #     fmArray = f #json.dumps(f)
    
    try:
        record_id = fms.create_record(fmArray)
    except FileMakerError as createError:
        fmError = createError
    
elif (action == 'updateRecord'):
    #print(action)
    uuid = formJSON['uuid']
    pk = formJSON['pk']

    find_query = [{ pk : uuid}]
    try:
        foundset = fms.find(query=find_query)
    except FileMakerError as findError:
        fmError = findError
    record = foundset[0]
   
    for key in keys:
        value = fmPayload[key]
        record[key] = value
    
    try:
        fms.edit(record)
    except FileMakerError as updateError:
        fmError = updateError

elif(action=='getRecord'):
    #Set up the query
    find_query = [fmPayload]
    try:
        #Perform the find
        foundset = fms.find(query=find_query,limit=20000)
        returnArray = {}
        i = 0
        for r in foundset:
            thisRecord = foundset[i]
            f = {}
            keys = thisRecord.keys()
            for key in keys:
                # get the value for the field
                value = thisRecord[key]
                f[key] = value
                
            returnArray[i] = f
            i = i + 1
        
        returnArray = json.dumps(returnArray)

    except FileMakerError as findError:
        fmError = findError

elif(action=='getRecord2'):
    # this is the same as getRecord but uses a specific field as the key name.
    # used for the FM script part of Topaz or others so you get an erray where you can get the data for it by JSONGetElement(theScriptName)
    #Im sure somehow I can use this to be able to specify the field so could use a Topaz reference etc
    #Set up the query
    find_query = [fmPayload]
    try:
        #Perform the find
        foundset = fms.find(query=find_query,limit=20000)
        returnArray = {}
        i = 0
        for r in foundset:
            thisRecord = foundset[i]
            thisValueForKey = thisRecord.ScriptName
            f = {}
            keys = thisRecord.keys()
            for key in keys:
                # get the value for the field
                value = thisRecord[key]
                f[key] = value
                
            returnArray[thisValueForKey] = f
            i = i + 1
        
        returnArray = json.dumps(returnArray)

    except FileMakerError as findError:
        fmError = findError



elif(action=='runScript'):
    # new! 31/03/22 run a script (requires a data set to find, for now using the pk/uuid method)
    uuid = formJSON['uuid']
    pk = formJSON['pk']

    # the API can take a parameter, for my use case we pass it a JSON array
    # specify the script in the data array as 'fmScript'
    # the parameter array is the 'data' array we use for getRecord usually
    fmScript = fmPayload['fmScript']

    #bug fix here v1.51 12-04-2022 to ensure proper JSON passed to script
    paramJSON = json.dumps(fmPayload)
    # need some form of error capture here!

    find_query = [{ pk : uuid}]
    try:
        foundset = fms.find(query=find_query,scripts={'prerequest': [fmScript, paramJSON]})
        #1.51 added logic to catch the FMS script result.
        #the result is a touple with when it ran (eg after), the last FM error code, and what you passed with "exit script" in FM
        scriptResult = fms.last_script_result
        resultKeys = scriptResult.keys()

    except FileMakerError as findError:
        fmError = findError
    #record = foundset[0]

elif(action=='saveFile'):
    #new feature to test saving B64 encoded file to temp folder (no fm stuff for now!)
    fileB64 = fmPayload['FileB64']
    fileName = fmPayload['FileName']

    #decode
    fileDecoded = base64.b64decode(fileB64)
    #fileDecoded = p.decode('utf-8')

    #set path
    tempPath = r"c:\temp"
    os.chdir(tempPath)

    #write to path
    with open(fileName, 'wb') as output_file:
        output_file.write(fileDecoded)
    
    fmError = 'OK'
    saveFileMessage = "(000) OK"
    
# Be nice and close the DAPI connection
fms.logout()

# If an error occured, report back, otherwise result is OK
# You can check for this in FM by seeing if whatever field or var you used in Insert from URL is OK
if (fmError != 'OK'):
    #errorJSON = {'fmError':fmError}
    print(fmError)
elif(action=='getRecord' or action=='getRecord2'):
    print(returnArray)
elif(action=='runScript'):
    print('OK')
    print('FMS script result:',scriptResult)
elif(action=='saveFile'):
    print(saveFileMessage)
else:
    print('OK')
