#!/usr/bin/python

import json
import sys
import time
import os
import glob
import datetime

#import Adafruit_DHT
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

GDOCS_OAUTH_JSON       = 'file.json'
GDOCS_SPREADSHEET_NAME = 'name'
FREQUENCY_SECONDS      = 30

#initiate the temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

#set up the location of the sensor in the system
device_folder = glob.glob('/sys/bus/w1/devices/28*')
device_file = [device_folder[0] + '/w1_slave', device_folder[0] + '/w1_slave']


def read_temp_raw(): #a function that grabs the raw temperature data from the sensor
    f_1 = open(device_file[0], 'r')
    lines_1 = f_1.readlines()
    f_1.close()
    f_2 = open(device_file[1], 'r')
    lines_2 = f_2.readlines()
    f_2.close()
    return lines_1 + lines_2


def read_temp(): #a function that checks that the connection was good and strips out the temperature
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES' or lines[2].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t='), lines[3].find('t=')
    temp = float(lines[1][equals_pos[0]+2:])/1000, float(lines[3][equals_pos[1]+2:])/1000
    return temp


def login_open_sheet(oauth_key_file, spreadsheet):
        """Connect to Google Docs spreadsheet and return the first worksheet."""
        try:
                json_key = json.load(open(oauth_key_file))
                credentials = SignedJwtAssertionCredentials(json_key['client_email'],json_key['private_key'],['https://spreadsheets.google.com/feeds'])
                gc = gspread.authorize(credentials)
                worksheet = gc.open(spreadsheet).sheet1
                return worksheet
        except Exception as ex:	
                print 'Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!'
                print 'Google sheet login failed with error:', ex
		sys.exit(1)


print 'Logging sensor measurements to {0} every {1} seconds.'.format(GDOCS_SPREADSHEET_NAME, FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'
worksheet = None

while True:
        # Login if necessary.
        if worksheet is None:
                worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

        # Attempt to get sensor reading.
        temp = read_temp() #get the temp
    	values = [datetime.datetime.now(), temp[0]]

        # Skip to the next reading if a valid measurement couldn't be taken.
        # This might happen if the CPU is under a lot of load and the sensor
        # can't be reliably read (timing is critical to read the sensor).
        if temp is None:
                time.sleep(2)
                continue

        print 'Temperature: C'.format(temp)
        #print 'Humidity:    {0:0.1f} %'.format(humidity)

        # Append the data in the spreadsheet, including a timestamp
        try:
                #worksheet.append_row((datetime.datetime.now(), temp))
		worksheet.append_row(values)
        except:
                # Error appending data, most likely because credentials are stale.
                # Null out the worksheet so a login is performed at the top of the loop.
                print 'Append error, logging in again'
                worksheet = None
                time.sleep(FREQUENCY_SECONDS)
                continue

        # Wait 30 seconds before continuing
        print 'Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME)
        time.sleep(FREQUENCY_SECONDS)
