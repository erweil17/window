#Window Project v2.0
#Made by Eric Weiler

#Necessary imports
import time, os, urllib2, json, datetime
from gpiozero import Button, LED
from time import gmtime, strftime

attic_enabled = False
internet_enabled = True

#Sending notifications to phone
def notify(message):
    if message == 0:
        os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Too warm outside'")
    if message == 1:
        os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Too cold outside'")
    if message == 2:
        os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Raining outside'")

#Setting up temperature sensors
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
temp_file_1 = '/sys/bus/w1/devices/28-000008776471/w1_slave'
temp_file_2 = '/sys/bus/w1/devices/28-000008773a60/w1_slave'

#Setting up LED's and switches
greenled = LED(20)
redled = LED(26)
greenled.off()
redled.on()
window = Button(21)

#Gathering the outside temperature from Weather Underground API
def outsidetemp():
    try:
        f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/conditions/q/pws:KORNEWBE30.json')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        temp_f = parsed_json['current_observation']['temp_f']
        weather = parsed_json['current_observation']['weather']
        if weather == 'Rain':
            rain = 1
        else:
            rain = 0
        f.close()
    except:
        temp_f = -1
        rain = 2
    return temp_f, rain

#Getting the predicted high temperature today
def outsideforecast():
    f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/forecast/q/OR/Newberg.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    temp_highs = parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit']
    f.close()
    temp_high = int(temp_highs) 
    return temp_high

#More setting up inside temperature sensors
def read_temp_raw(sensor):
    if sensor == 0:
        f = open(temp_file_1, 'r')
    elif sensor == 1:
        f = open(temp_file_2, 'r')
    lines = f.readlines()
    f.close()
    return lines

#Gathering inside temperature data
def insidetemp():
    lines = read_temp_raw(0)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(0)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        tempin = round(temp_f, 1)
    return tempin

#Gathering attic temperature data, if enabled
def attictemp():
    if attic_enabled == True:
        lines = read_temp_raw(1)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw(1)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            tempattic = round(temp_f, 1)
            return tempattic
    else:
        return "N/A"

#Writing the data to a text file to be used by a web server
def filewrite(day, hour, inside, outside, attic, window):
    file = open("/var/www/html/data.txt","w")
    file.write("%s\n" % day)
    file.write("%s\n" % hour)
    file.write("%s\n" % inside)
    file.write("%s\n" % outside)
    file.write("%s\n" % attic)
    file.write("%s\n" % window)
    file.close()

#Setting up variables for first run
activealert = False
notified = False
updated = datetime.datetime.now()
conditions = outsidetemp()
outside = conditions[0]
rain = int(conditions[1])
inside = insidetemp()
attic = attictemp()
outsidehigh = outsideforecast()
errors = 0
updatedday = strftime("%m-%d")
updatedhour = strftime("%H:%M")
print "High updated to ",outsidehigh

#The main loop
while True:
    now = datetime.datetime.now()
    #Program changes based on high temperature of the day
    if now.hour == 0 and now.minute == 0 and now.second == 0:
        outsidehigh = outsideforecast()
        print "High updated to {} at {}:{}".format(outsidehigh, now.hour, now.minute)
    #Temperatures only update every 5 minutes
    if (now.minute % 5) == 0 and now.second == 0:
        updated = datetime.datetime.now()
        prevoutside = outside
        conditions = outsidetemp()
        outside = conditions[0]
        rain = int(conditions[1])
        inside = insidetemp()
        attic = attictemp()
        updatedday = strftime("%m-%d")
        updatedhour = strftime("%H:%M")
        if outside > 120 or outside < 0:
            outside = prevoutside
            print "Unable to get temperature data at {}:{}".format(updated.hour, updated.minute)
        elif (outside-prevoutside) > 5 or (outside-prevoutside) < -5:
            if errors < 3:
                outside = prevoutside
                print "Temperature Error Occurred at {}:{}".format(updated.hour, updated.minute)
                errors += 1
            else:
                errors = 0
                print "Accepted Error at {}:{}".format(updated.hour, updated.minute)
        else:
            errors = 0
    tempdiff = inside - outside
    #Check if window is closed
    if window.is_pressed == False:
        windowopen = 1
    else:
        windowopen = 0
#Write everything to a file
    filewrite(updatedday, updatedhour, inside, outside, attic, windowopen)
#Green and red LED controls (vary based on predicted high temperature)
#If it's raining outside, you want your window closed
    if rain == 1:
        greenled.off()
        if windowopen == 1:
            if notified == False:
                notify(2)
                redled.blink(0.75,0.75)
                notified = True
        else:
            redled.on()
            notified = False
#If it's not too hot outside, you want to leave your window open
    elif outsidehigh <= 78 and outsidehigh >= 70:
        if tempdiff <= -2 or (outside < 50 and inside < 70):
            greenled.off()
            if windowopen == 1:
                if notified == False:
                    if outside < 50:
                        notify(1)
                    else:
                        notify(0)
                    redled.blink(0.75,0.75)
                    notified = True
            else:
                redled.on()
                notified = False
        elif tempdiff >= 0 or tempdiff <= 19:
            redled.off()
            greenled.on()
            notified = False
        else:
            time.sleep(0.00001)
#If it's cold outside, you want your window open when it's warm
    elif outsidehigh < 70:
        if outside <= 59 and inside <= 73:
            greenled.off()
            if windowopen == 1:
                if notified == False:
                    notify(1)
                    redled.blink(0.75,0.75)
                    notified = True
            else:
                redled.on()
                notified = False
        elif outside >= 60 or inside >= 75:
            redled.off()
            greenled.on()
            notified = False
        else:
            time.sleep(0.00001)
#If it's hot outside, you want your window open when it's cool
    else:
        if now.hour <= 14:
            highdiff = 3.0
            lowdiff = 2.0
        else:
            highdiff = 0.5
            lowdiff = -0.5
        if tempdiff <= lowdiff:  
            greenled.off()
            if windowopen == 1:
                if notified == False:
                    notify(0)
                    redled.blink(0.75,0.75)
                    notified = True
            else:
                redled.on()
                notified = False
        elif tempdiff >= highdiff:
            redled.off()
            greenled.on()
            notified = False
        else:
            time.sleep(0.00001)
    time.sleep(1)
