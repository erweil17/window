#Window open project
#By Eric Weiler

import time, os, glob, random, urllib2, json, requests
from gpiozero import Button, LED, Buzzer
from datetime import datetime
#from simplepush import send, send_encrypted

def notify(msg):      #send notification to phone
    if msg == 0:
        os.system('sudo sh send-encrypted.sh -k UZ4Y7A -p password -s isadueid -t "Close your window" -m "It\'s too warm outside" -e window')
    if msg == 1:
        os.system('sudo sh send-encrypted.sh -k UZ4Y7A -p password -s isadueid -t "Close your window" -m "Storms nearby" -e window')

os.system('modprobe w1-gpio')      #set up inside sensor
os.system('modprobe w1-therm')
device_file1 = '/sys/bus/w1/devices/28-000008776471/w1_slave'
device_file2 = '/sys/bus/w1/devices/28-000008773a60/w1_slave'

green = LED(20)    #set up LED's
red = LED(26)
alertled = LED(3)
green.off()
red.on()
alertled.off()

window = Button(21)   #Window magnet

verysevereweather = ['HUR','TOR','TOW','WRN','SEW','FLO','SVR','VOL','HWW']    #types of weather that trigger an alert
severeweather = ['HUR','TOR','TOW','WRN','SEW','WIN','FLO','WAT','WND','SVR','HEA','FOG','SPE','FIR','VOL','HWW']

def outsidetemp():    #temperature outside gathered from weather underground
    f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/conditions/q/pws:KORNEWBE30.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    temp_f = parsed_json['current_observation']['temp_f']
    return temp_f
    f.close()

def alerts():         #alerts gathered from weather underground
    f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/alerts/q/OR/Newberg.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    try:
        alert = parsed_json['alerts'][0]['type']
        description = parsed_json['alerts'][0]['description']
        expires = parsed_json['alerts'][0]['expires']
    except:
        alert = 'NA'
        description = ['Not available']
        expires = ['NA']
        
    return [alert, description, expires]
    f.close()

def read_temp_raw(file):               #inside temperature sensor data
    if file == 1:
        f = open(device_file1, 'r')
    elif file == 2:
        f = open(device_file2, 'r')
    lines = f.readlines()
    f.close()
    return lines

def insidetemp():                    #temperature inside
    lines = read_temp_raw(1)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        tempin = round(temp_f, 1)
    return tempin

def attictemp():
    lines = read_temp_raw(2)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        tempattic = round(temp_f, 1)
        return tempattic

activealert = False
notified = False
alertdelay = 2
while True:
    inside = insidetemp()         #get temperatures and alerts
    outside = outsidetemp()
    attic = attictemp()
    file2 = open("record.txt", "r")
    record = file2.read()
    atticrecord = float(record)
    file2.close()
    if alertdelay >= 1:            #only get alerts every 10 minutes
        currentalerts = alerts()
        alertdelay = 0
    else:
        alertdelay += 1
    file = open("/var/www/html/data.txt","w")
    file.write(datetime.now().strftime("%m-%d\n"))
    file.write(datetime.now().strftime("%H:%M\n"))
    file.write("%s\n" % inside)
    if outside < 0 or outside > 115:        #if the website has an error
        file.write("Unavailable\n")
        outside = inside - 2.5
    else:
        file.write("%s\n" % outside)
    file.write("%s\n" % attic)
    if window.is_pressed == False:
        file.write("1\n")
    else:
        file.write("0\n")
    diff = outside - inside
    if currentalerts[0] in verysevereweather:   #if alert exists
        activealert = True
        alertled.blink(1,1)
        diff = 100
        file.write("1\n")
        file.write("%s\n" % currentalerts[1])
        file.write("%s\n" % currentalerts[2])
    elif currentalerts[0] in severeweather:
        file.write("1\n")
        file.write("%s\n" % currentalerts[1])
        file.write("%s\n" % currentalerts[2])
    else:
        if activealert == True:
            alertled.off()
            activealert = False
        file.write("0\n")
        file.write("NA\n")
        file.write("NA\n")
    if attic > atticrecord:
        file.write("%s\n" % attic)
        file2 = open("record.txt","w")
        file2.write("%s\n" % attic)
        file2.close()
    else:
        file.write("%s\n" % atticrecord)
    file.close()
#    if diff >= 5 or diff <= -8:   #refresh time depends on temperature difference
#        sleeptime = 599
#        alertdelay += 1           #alert refresh time never changes
#    else:
    sleeptime = 299
    sleep = 0

    while sleep < sleeptime:             #wait ~5-10 minutes between temperature checks but still check if window open every second
        if diff >= -1.5 and window.is_pressed == False:
            green.off()
            if notified == False:
                if activealert == True:
                    notify(1)
                else:
                    notify(0)
                red.blink(0.75,0.75)
                notified = True
                sleep += 1
            else:
                sleep += 1
        elif diff >= -1.5 and window.is_pressed == True:    #if warmer outside, turn on red LED
            green.off()
            red.on()
            sleep += 1
            notified = False
        elif diff < -2.5:     #if colder outside, turn on green LED
            red.off()
            green.on()
            sleep += 1
            notified = False
        else:
            sleep += 1
        time.sleep(1)
