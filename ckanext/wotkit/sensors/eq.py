#-------------------------------------------------------------------------------
# Name:        Module1
# Purpose:     
#
# Author:      rlea
#
# Created:     23/12/2008
# Copyright:   (c) rlea 2008
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
from bs4 import BeautifulSoup, NavigableString
import urllib, urllib2,sys, re, time, datetime
import sensetecnic

from urllib2 import Request, URLError
import socket
socket.setdefaulttimeout(120)
import re

lastEarthquake = [0.0,0.0,0.0,0.0]  # Magnitude, time, lat, lon

#WoTKit Key for user Sensetecnic
key_id = "fda59827f78d94d1"
key_password = "21ec32b4c02ebb67"

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
        

def getEQ():
    
    global lastEarthquake
    myEarthquake = [0.0,0.0,0.0,0.0]
    p3 = re.compile('-?\d+(?:\.\d+)?')
    p4 = re.compile('p>.+br')
    #<p>Tuesday, December 23, 2008 05:18:30 UTC<br>
    firstTime = True
    
    s = 'http://earthquake.usgs.gov/eqcenter/catalogs/1day-M2.5.xml'
    SENSOR_NAME = 'eq'

    f = getURL(s)
    #f = open('eq1.html')
    if f == -1: return -1
    
    soup = BeautifulSoup(f)

    myItems = soup.findAll('entry')


    for l in myItems:
        # Magnitude is a real in the title, get it first
        m = l.find('title')
        m1 = p3.search(m.string)
        mag = float(m1.group(0))


        # Date of EQ is in the summary section (can't parse this not valid XML)
        sum = l.find('summary')
        dateStr = p4.search(sum.string)
        myDate = dateStr.group(0)  # got the whole string

        #(update: Feb22/13 - rosey)
        #m1 = myDate.replace('p>','')
        #m2 = m1.replace('<br','')      
        m2 = myDate.split(">")[1].split("<")[0] #myDate format: 'p> Date <br> a different date'
        
        m3 = time.strptime(m2,'%A, %B %d, %Y %H:%M:%S %Z')
        m4 = time.mktime(m3)

        # Lat and Lon are in the georss tag
        refs = l.find('georss:point')
        pos = p3.findall(refs.string)
        lat = float(pos[0])
        lon = float(pos[1])

        #check we haven't seen this before
        if mag == lastEarthquake[0]:
            if m4 == lastEarthquake[1]:
                #assume we have seen the rest and exit
                print 'Have seen this before - bye: %s' % (myDate)
                if firstTime == False: lastEarthquake = myEarthquake
                f.close()
                return (1)

        # would send to RB now
        print 'Earthquake %f:%s:%f,%f' % (mag, time.ctime(m4), lat, lon)
        tmenow=time.time()
        query_args = { 'timestamp':int(m4*1000),'data':'Magnitude', 'value':mag, 'lat':lat, 'lng':lon  }
        sensetecnic.sendData(SENSOR_NAME, None, None, query_args)
        return [SENSOR_NAME]
        # Finally store the most recent so we know what's new next time
        if firstTime:
            myEarthquake = [mag, m4, lat, lon]
            firstTime = False
        # end for
  
    lastEarthquake = myEarthquake
    
    f.close()
    return 1
#end getEQ    

def updateWotkit():    
    return getEQ()
    