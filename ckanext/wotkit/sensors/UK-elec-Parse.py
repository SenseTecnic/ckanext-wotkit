#-------------------------------------------------------------------------------
# Name:        Module1
# Purpose:     
#
# Author:      rlea
#
# Created:     04/12/2008
# Copyright:   (c) rlea 2008
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import string
import sys
import urllib
from urllib2 import Request, URLError
import datetime
import time
import re
import sensetecnic

SENSOR_NAME = 'rjl-elec'
def updateWotkit():
    
    maxArrived = 0
    timeList = []
    delta = 60
    elecLat = 54.0057
    elecLon = -02.784
    
    try:
        filename, msg = urllib.urlretrieve('http://www.nationalgrid.com/ngrealtime/realtime/systemdata.aspx')
        f = open(filename, 'r')
    except URLError, e:
     if hasattr(e, 'reason'):
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
     elif hasattr(e, 'code'):
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except IOError, e:
        print 'ioError Im afraid'
        return -1
    else : #everything ok
     p = re.compile('[0-9]+')
     p1 = re.compile('\D[0-9]+')

     for l in f.readlines():
        #print l
        pos = l.find('Demand', 0, 200)
        if pos > 0: #ok, have found line containing demand data
            m = p.search(l)
            UKdemand = int(m.group()) ; print 'UK demand is %d' % (UKdemand)
            wordlist = l.split('France',5)
            m1 = p1.search(wordlist[1])
            FRtransfer = int(m1.group()) ; print 'France to UK is %d' % (FRtransfer)
            # ok, now need time in UK
            localTimestamp = time.time()
            UKTimestamp = (localTimestamp + 28800)# +8H  to UK
            #print ' %s Elec is: %d' % (time.ctime(UKTimestamp), elec)
            query_args = { 'timestamp':int(UKTimestamp*1000),'data':'Total UK Elec demand', 'value':UKdemand, 'lat':elecLat, 'lng':elecLon  }
            encoded_args = urllib.urlencode(query_args)

            try:
                sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
                return [SENSOR_NAME]
            except:
                print 'strange network error - sending elec to RB'
                f.close()
                return -1
        # end if found a valid data record
    #loop back and read next line
    
