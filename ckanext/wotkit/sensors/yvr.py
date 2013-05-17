#-------------------------------------------------------------------------------
# Name:        cpu-load
# Purpose:     send CPU and other data feeds to Sense Tecnic
#
# Author:      rlea
#
# Created:     01/12/2008
# Copyright:   (c) rlea 2008
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import sys
import string
import time
import urllib

from urllib2 import Request, URLError
import datetime
import socket
socket.setdefaulttimeout(120)
import re
from bs4 import BeautifulSoup, NavigableString
import sensetecnic

#WoTKit Key for user Sensetecnic
key_id = "fda59827f78d94d1"
key_password = "21ec32b4c02ebb67"

YVRlat = 49.18722
YVRlon = -123.18528

months = {'january': 1,
          'jan': 1,
          'february': 2,
          'feb': 2,
          'march': 3,
          'mar': 3,
          'april': 4,
          'apr': 4,
          'may': 5,
          'june': 6,
          'jun': 6,
          'july': 7,
          'jul': 7,
          'august': 8,
          'aug': 8,
          'september': 9,
          'sept': 9,
          'october': 10,
          'oct': 10,
          'november': 11,
          'nov': 11,
          'december': 12,
          'dec': 12}

def getURL(URLString):
# takes a URL to open, returns an open file or a -1

    try:
        filename, msg = urllib.urlretrieve(URLString)
        f = open(filename, 'r')
    except URLError, e:
     if hasattr(e, 'reason'):
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
     elif hasattr(e, 'code'):
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
     return -1
    except IOError, e:
        print 'ioError Im afraid'
        return -1
    except socket.error:
        errno, errstr = sys.exc_info()[:2]
        if errno == socket.timeout:
            print "There was a timeout"
            return -1
        else:
            print "There was some other socket error"
            return -1
    else : #everything ok
        return f
# end def getURL()


def YVRarrv():

    maxArrived = 0
    timeList = []
    arrivalsList = []
    delta = 60
    
    # s = 'http://www.yvr.ca/flightinfo/fids/ifids/yvr_bottom.aspx?Lang=En&Type=ARR'
    s = 'http://www.yvr.ca/en/mobile/flight-information/arriving.aspx?search=mobile&'
    #http://www.yvr.ca/services/FlightInfoHandler.ashx?tabletype=ArrivingDeparting&f=arr&ftt=ArrivalsDepartures&language=en
   #http://www.yvr.ca/en/mobile/flight-information/arriving.aspx?search=mobile&
    sensor = 'yvr-arrive'

    f = getURL(s)
    if f == -1: raise Exception("invalid retrieval")
    
    else : #everything ok
     for l in f.readlines():
        pos = l.find('yvr-FlightInfoTableContainer', 0, 100)
        if pos > 0: #ok, have found line containing all arrivals data
            myList = l.split('Arrived at ',100)

            i = 0

            for s in myList:
                if s[0].isdigit():

                    # mmm...hacks, find the date index in the previous array cell
                    # we want to extract the date string, which is enclosed by
                    # the strings "Date: (some html)" and the length of the
                    # previous array cell plus some html
                    dateIndex = myList[i - 1].rfind ("Date: ")
                    date = myList[i - 1][dateIndex + 15 : len (myList[i - 1]) - 26]

                    # the date string is delimited by ", " so split it
                    # month and day of month is delimited by " " so split it
                    dateSplit = date.split (", ")
                    dayOfWeek = dateSplit[0]    # not used
                    monthStr = dateSplit[1].split (" ")[0]
                    dayOfMonth = int (dateSplit[1].split (" ")[1])
                    year = int (dateSplit[2])

                    # this is really silly, but I don't think python has any
                    # means to parse a date from a string
                    month = months[monthStr.lower ()]

                    # get the time of arrival
                    h = int(s[0] + s[1])
                    m = int(s[3] + s[4])

                    # and the arrival gate
                    gate = s[29] + s[30]

                    # sometimes the gates are two digits
                    if s[31].isdigit():
                        gate += s[31]

                    # create the arrival time object
                    t = datetime.datetime (year, month, dayOfMonth, h, m, 0)

                    # check for code share, if same arrival time and gate is already in the list, then it is not a new arrival
                    try:
                        arrivalsList.index ([t, gate])
                        print "%s %s is already in our arrival list, skipping it." % (t, gate)
                    except:
                        arrivalsList.append ([t, gate])
                        print "Found arrival: %s %s" % (t, gate)

                i += 1
             #end for
        #end if
     #end for

     now = datetime.datetime.now()
     arrivedCount = 0

     for arrival in arrivalsList:

         arrivalTime = arrival[0];

         # only count arrivals in the last hour
         oneDelta = datetime.timedelta (hours = 0, minutes = delta)
         boundTime = now - oneDelta

         if (arrivalTime > boundTime):
             arrivedCount += 1

    localTimestamp = time.time()
    CATimestamp = (localTimestamp - 0)# old??? -16H for Malaysia to Vancouver
    query_args = { 'timestamp': int(CATimestamp*1000),'data':'Vancouver arrivals (total last hour)', 'value':arrivedCount, 'lat':YVRlat, 'lng':YVRlon }
    sensetecnic.sendData(sensor, None, None, query_args)
    print "Arrivals in last %d minutes is %d" % (delta, arrivedCount)
    f.close()
    return [sensor]

#end def YVRarrv

def YVRdep():

    maxArrived = 0
    departuresList = []
    delta = 60

    s='http://www.yvr.ca/en/mobile/flight-information/departing.aspx?search=mobile&'
    # http://www.yvr.ca/services/FlightInfoHandler.ashx?tabletype=ArrivingDeparting&f=dep&ftt=ArrivalsDepartures&language=en
    sensor = 'yvr-depart'

    f = getURL(s)
    if f == -1: raise Exception("invalid retrieval")

    else : #everything ok
     for l in f.readlines():
        pos = l.find('yvr-FlightInfoTableContainer', 0, 200)
        if pos > 0: #ok, have found line containing all departure data
            myList = l.split('Departed at ',100)

            i = 0

            for s in myList:
                if s[0].isdigit():

                    # mmm...hacks, find the date index in the previous array cell
                    # we want to extract the date string, which is enclosed by
                    # the strings "Date: (some html)" and the length of the
                    # previous array cell plus some html
                    dateIndex = myList[i - 1].rfind ("Date: ")
                    date = myList[i - 1][dateIndex + 15 : len (myList[i - 1]) - 26]

                    # the date string is delimited by ", " so split it
                    # month and day of month is delimited by " " so split it
                    dateSplit = date.split (", ")
                    dayOfWeek = dateSplit[0]    # not used
                    monthStr = dateSplit[1].split (" ")[0]
                    dayOfMonth = int (dateSplit[1].split (" ")[1])
                    year = int (dateSplit[2])

                    # this is really silly, but I don't think python has any
                    # means to parse a date from a string
                    month = months[monthStr.lower ()]

                    # get the time of departure
                    h = int(s[0] + s[1])
                    m = int(s[3] + s[4])

                    # get the departure gate
                    gate = s[29] + s[30]

                    # sometimes the gates are two digits
                    if s[31].isdigit():
                        gate += s[31]

                    # create the departure time object
                    t = datetime.datetime (year, month, dayOfMonth, h, m, 0)

                    # check for code share, if same departure time and gate is already in the list, then it is not a new departure
                    try:
                        departuresList.index ([t, gate])
                        print "%s %s is already in our departure list, skipping it." % (t, gate)
                    except:
                        departuresList.append ([t, gate])
                        print "Found departure: %s %s" % (t, gate)

                i += 1

     now = datetime.datetime.now ()
     departureCount = 0

     for departure in departuresList:

         departureTime = departure[0]

         # only count departures in the last hour
         oneDelta = datetime.timedelta(hours = 0, minutes = delta)
         boundTime = now - oneDelta

         if (departureTime > boundTime):
             departureCount += 1

    localTimestamp = time.time()
    CATimestamp = localTimestamp
    query_args = { 'timestamp': int(CATimestamp*1000),'data':'Vancouver departures (total last hour)', 'value':departureCount, 'lat':YVRlat, 'lng':YVRlon  }
    
    sensetecnic.sendData(sensor, None, None, query_args)
    

    print "Departures in last %d minutes is %d" % (delta, departureCount)
    f.close()
    return [sensor]

#end def YVRdep


   
def updateWotkit():
    sensors = []
    sensors.extend(YVRarrv())
    sensors.extend(YVRdep())
    return sensors
    

# end def main


