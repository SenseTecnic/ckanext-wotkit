#-------------------------------------------------------------------------------
# Name:       ferry
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

# globals to hold ship most recent co-ords just incase we fail to pick up new ones
QueenLat = 49.0198
QueenLon = -123.4314
QueenSpeed = 0
MVTankerLat = 51.8968
MVTankerLon = 2.8674
FerrySpeed = 0
lastEarthquake = [0.0,0.0,0.0,0.0]  # Magnitude, time, lat, lon

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


def getQofOB():
    global QueenLat, QueenLon, QueenSpeed
    s1 = 'http://www.marinetraffic.com/ais/shipdetails.aspx?mmsi=316011407&header=true'
    s2 = 'http://www.marinetraffic.com/ais/datasheet.aspx?SHIPNAME=queen+of+oak+bay&TYPE_SUMMARY=&PORT_ID=&menuid=&datasource=SHIPS_CURRENT&app=&B1=Search'
    sensor = 'qofob'
    
    f = getURL(s2)
    if f == -1: return -3

    else : #everything ok
       
        p3 = re.compile('\d+(?:\.\d+)?')

        lat = lon = speed = 0
        neglon = neglat = False

        soup = BeautifulSoup(f)
        s = soup.find('div', id='datasheet')
        if s != None:
            records = s.next.next.next.next.string
            if records != 'No Records Found':
                myItems1 = soup.findAll('font', attrs={"class" : "data"})

                speed = float(myItems1[3].string)
                direction = float(myItems1[4].string)

                l1 = myItems1[9].contents
                ll = l1[0]['href']
                l2 = ll.split('&centerx=')
                l3 = l2[1].split('&centery=')
                lat= float(l3[1])
                lon = float(l3[0])
                QueenLat = lat; QueenLon = lon; QueenSpeed = speed
            else:
                return (-1)
        else:
            return (-2)

     # end readlines
    print 'Ferry. Speed: %f, Dir: %f, Lat: %f, Lon: %f' % (speed, direction, lat, lon)
    #now check we actually found some data, if not, use old data
    if lat == 0: lat = QueenLat; lon = QueenLon; speed = QueenSpeed
    
     # ok, now need time in Vancouver
    localTimestamp = time.time()
    UKTimestamp = (localTimestamp - 0)# -16H for Malaysia to Vancouver
    query_args = { 'timestamp':int(UKTimestamp*1000),'data':'Speed (Kts)', 'value':speed, 'lat':lat, 'lng':lon  }
    sensetecnic.sendData(sensor, None, None, query_args)
    f.close()
    return [sensor]
# end def QofOB

def updateWotkit():
    #if getShip() != 1: print 'getShip error'
    result = getQofOB()
    if result != 1:
        if result == -1: print 'getShip error: No records found'
        if result == -2: print 'getShip error: No datasheet found'
        if result == -3: print 'getShip error: failed http request'
        
    return result

# end def main

