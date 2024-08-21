#!/usr/bin/env python
# v2.5
########################
#
# fmpy functions live here
#
# 
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
    if payloadRaw == 'selftest':
        action = 'selftest'
        fmWhat = fmInfo.stQuery
        fmWhere = {'action':action,'serverName':fmInfo.stServer,'databaseName':fmInfo.stDatabase,'layoutName':fmInfo.stLayout}

    else:
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

def selftest(fmWhere,fmWhat,fms):
    resultLine1 = ('Selftest....<br><br>Testing connectivity to:<br>'+fmWhere['serverName']+'<br>'+fmWhere['databaseName']+' -> '+ fmWhere['layoutName'])
    print(resultLine1)
    print('<br><b>Note: Only the first 2 records are displayed</b><br>')
    find_query = [fmWhat]
    try:
        fmResult = fms.find(query=find_query,limit=2)
        returnArray = {'data':fmResult}
        i = 0
        success = 1
        #serverResponse = json.dumps(returnArray)
        resultLine2 = ('<br><br>Test successful, server returned:<br>')
        print(resultLine2)
        for r in fmResult:
            thisRecord = fmResult[i]
            keyFieldValue = i
            f = {}
            keys = thisRecord.keys()
            for key in keys:
                # get the value for the field
                value = thisRecord[key]
                print(key,':',value,'<br>')
            print('------<br>')
            i = i + 1

    except FileMakerError as findError:
        fmResult = str(findError)
        success = 0
        resultLine2 = '<br><br>Test failed. FM Server responded:<br>'
        print(resultLine2)
        print(fmResult)
    return "<br><br>Selftest Complete"

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
        keyField = "null"
    try:
        fmResultRaw = fmWhere['fmResultRaw']
        returnArray = {}
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
            #this SHOULD return the data in the same format as the "response" part of an Execute FileMaker Data API script step
            i = 0
            dataArray = []
            for r in fmResult:
                thisRecord = fmResult[i]
                f = {}
                keys = thisRecord.keys()
                for key in keys:
                    # get the value for the field
                    value = thisRecord[key]
                    f[key] = value
                
                wrapper = {'fieldData':f}
                dataArray.append(wrapper)
                
                i = i + 1

            returnArray = {'data':dataArray}
            fmResult = json.dumps(returnArray)
        else:
            dataArray = []
            returnArray = {}
            #thisData = {}
            i = 0
            for r in fmResult:
                thisRecord = fmResult[i]
                if keyField != 'null':
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
                value = fmWhat[key]
                record[key] = value
        try:
            fms.edit(record)
            fmResult = '000 OK'
        except FileMakerError as updateError:
            fmResult = updateError
    return fmResult

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
