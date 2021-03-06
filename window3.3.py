#Pi Window Project v3.3.1 (WORKS AT HOME AND DORM)
#Made by Eric Weiler
#This program gathers the inside and outside temperatures, compares them, and tells you if you should open your window or not.
#All information is written to a file to be used by other programs. The order in which it is written is available in the filewrite function

#New in version 3.2: Allows differentiating between window open all the way or just at an angle

import time, os, urllib2, json, datetime
from gpiozero import Button, LED
from time import gmtime, strftime

# --- --- --- --- Enable or disable options here: --- --- --- ---
# ----Change the settings values, don't just comment them out ---

#Set to 0 if in Newberg, 1 if in Corvallis. For getting outside temperature
location = 1

#Set to true to enable the attic temperature
attic_enabled = False

#Set to true to keep track of any pre-coded record temperature. If you don't know what this is, set it to false
record = False

#Use correct temperature sensor. Serial number with letters == 1. If you have no idea which one, guess until it works.
#This option is for the inside sensor. Attic sensor will be opposite value, if enabled
temperature_sensor = 1

#Enable push notifications on your phone
notifications_enabled = False

#Enable error checking, specifically when the outside temperature is wrong
error_checking = True

#Enable or disable the angled window. Some windows can be opened in 2 different ways. Only uses bottomswitch variable if false
angled_window = True;

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---




#Set up switches and LEDs
greenled = LED(2)
redled = LED(17)
bottomswitch = Button(14)
topswitch = Button(5)
greenled.off()
redled.on()

#Set up program based on preferences selected
if location == 0:
    url = 'https://api.weather.gov/stations/AU955/observations/current'
    highurl = 'https://api.weather.gov/gridpoints/PQR/100,95/forecast'
elif location == 1:
    url = 'https://api.weather.gov/stations/C5709/observations/current'
    highurl = 'https://api.weather.gov/gridpoints/PQR/83,62/forecast'
if temperature_sensor == 0:
    temp_file = '/sys/bus/w1/devices/28-000008776471/w1_slave'
    if attic_enabled == True:
        attic_file = '/sys/bus/w1/devices/28-000008773a60/w1_slave'
elif temperature_sensor == 1:
    temp_file = '/sys/bus/w1/devices/28-000008773a60/w1_slave'
    if attic_enabled == True:
        attic_file = '/sys/bus/w1/devices/28-000008776471/w1_slave'

#Setting up sensors
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

def notify(message):
    if notifications_enabled == True:
	if message == 0:
	    os.system("curl 'https://api.simplepush.io/send/D2PAay/Close your window/Too warm outside'")
    	if message == 1:
	    os.system("curl 'https://api.simplepush.io/send/D2PAay/Close your window/Too cold outside'")
	if message == 2:
	    os.system("curl 'https://api.simplepush.io/send/D2PAay/Close your window/Raining outside'")
	if message == 3:
            os.system("curl 'https://api.simplepush.io/send/D2PAay/Close your window/Severe weather outside'")

#Get outside temperature
def internet_temp():
    try:
        f = urllib2.urlopen(url)
        json_string = f.read()
        parsed_json = json.loads(json_string)
        temp_c = float(parsed_json['properties']['temperature']['value'])
        temp_f = round((temp_c*9/5)+32, 1)
        weather = 0
        f.close()
    except:
        temp_f = -100
        weather = 0
    return temp_f, weather

def internet_high():
    try:
        f = urllib2.urlopen(highurl)
        json_string = f.read()
        parsed_json = json.loads(json_string)
        high = int(parsed_json['properties']['periods'][0]['temperature'])
    except:
        high = 0;
    return high

def insidetemp():
    try:
        f = open(temp_file, 'r')
        lines = f.readlines()
        f.close()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            tempin = round(temp_f, 1)
        return tempin
    except:
        print "Error: Couldn't get inside temperature"
        return -100

def attictemp():
    try:
        if attic_enabled == True:
            f = open(attic_file, 'r')
            lines = f.readlines()
            f.close()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                tempattic = round(temp_f, 1)
            return tempattic
        else:
            return -100
    except:
        print "Error: Couldn't get attic temperature"
        return -100

#Writes information to the file, with one piece of data per line. The order in which everything is written from top to bottom is as follows:
#updated month, day, hour, minute, inside temp, outside temp, attic temp, window open (T/F), predicted outside high, should you open or close (T/F), the reason to close, and the type of alert present
def filewrite(month, day, hour, minute, inside, outside, attic, window, forecast, red, reason):
    file = open("data.txt", "w")
    file.write("%s\n" % month)
    file.write("%s\n" % day)
    file.write("%s\n" % hour)
    if minute < 10:
        file.write("0%s\n" % minute)
    else:
        file.write("%s\n" % minute)
    if (inside == -100):
        file.write("N/A\n")
    else:
        file.write("%s\n" % inside)
    file.write("%s\n" % outside)
    if (attic == -100):
        file.write("N/A\n")
    else:
        file.write("%s\n" % attic)
    file.write("%s\n" % window)
    file.write("%s\n" % forecast)
    file.write("%s\n" % int(red))
    file.write("%s\n" % reason)
    file.close()

#This is just a bonus to keep track of the highest recorded attic temperature. It writes to a separate file
def record_filewrite(temperature):
    file = open("record.txt", "r")
    lines = open("record.txt","r").read().split("\n")
    file.close()
    record = lines[0]
    if (temperature < float(record)):
        file2 = open("record.txt", "w")
        file2.write("%s\n" % temperature)
        file2.close()

#Variable initial setup
notified = False
if error_checking == True:
    error_tries = 0
first = True
reason = 0      #This is for the text on the web server


#Main loop
while True:
    now = datetime.datetime.now()
    if ((now.minute % 10) == 0 and now.second == 0) or first == True:
        updated = datetime.datetime.now()
        if first != True:
            previousinternet = internet
            previousoutside = outside
            previousinside = inside
            previoushigh = outsidehigh
        internet = internet_temp()
        outside = internet[0]
        rain = internet[1]
        outsidehigh = internet_high()
        if rain == 0 and outside == -100:
            internet = previousinternet
            outside = internet[0]
            rain = internet[1]
            outsidehigh = previoushigh
            print "[" + str(updated.month) + "/" + str(updated.day) + " " + str(updated.hour) + ":" + str(updated.minute) + "] Unable to get outside temperature data"
        if error_checking == True and first != True:
            if error_tries >= 3:
                print "[" + str(updated.month) + "/" + str(updated.day) + " " + str(updated.hour) + ":" + str(updated.minute) + "] Accepted error"
                error_tries = 0
            elif previousoutside > (outside + 5) or previousoutside < (outside - 5):
                outside = previousoutside
                print "[" + str(updated.month) + "/" + str(updated.day) + " " + str(updated.hour) + ":" + str(updated.minute) + "] Incorrect outside temperature detected"
                error_tries += 1
            else:
                error_tries = 0

    inside = insidetemp()
    attic = attictemp()
    if (inside == -100):
        inside = previousinside

    if angled_window == True:
        if bottomswitch.is_pressed == False and topswitch.is_pressed == False:
            window = 1
        elif bottomswitch.is_pressed == True and topswitch.is_pressed == False:
            window = 2
        else:
            window = 0
    else:
        if bottomswitch.is_pressed == False:
            window = 1
        else:
            window = 0

    if record == True:
        record_filewrite(inside)
    tempdiff = outside - inside
    red = True
    first = False

#If it's raining outside, you want your window closed
    if (rain < 800 and (rain%100) != 0):
        red = True
        reason = 2

#If it's not too hot outside, you want to leave your window open
    elif outsidehigh <= 78 and outsidehigh >= 70:
        if tempdiff >= 1:
            red = True
            reason = 0
        elif outside < 50 and inside <= 72:
            red = True
            reason = 1
        else:
            red = False

#If it's cold outside, you want your window open when it's warm
    elif outsidehigh < 70:
        if outside < 60 and inside <= 72:
            red = True
            reason = 1
        else:
            red = False

#If it's hot outside, you want your window open when it's cool
    else:
        if updated.hour <= 14:    #Tolerances vary based on time of day
            highdiff = -2.0
            lowdiff = -3.0
        else:
            highdiff = 1
            lowdiff = -0.5
        if tempdiff >= highdiff:
            red = True
            reason = 0
        elif tempdiff <= lowdiff:
            red = False

#LED and notification controls
    filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, red, reason)
    if red == True:
        greenled.off()
        if window == 1:
            if notified == False:
                notify(reason)
                notified = True
            redled.blink(0.75,0.75)
        elif window == 2:
            if (reason == 0) or (reason == 3):
                if notified == False:
                    notify(reason)
                    notified = True
                redled.blink(0.75,0.75)
            else:
                redled.on()
        else:
            redled.on()
    else:
        redled.off()
        greenled.on()
        notified = False

#Check every second to see if the window was opened or closed. Only update temperatures every 5 minutes
    now = datetime.datetime.now()
    while (now.second != 0):
        if (bottomswitch.is_pressed == False) and (window != 1):     #if open
            window = 1
            filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, red, reason)
            if red == True:
                redled.blink(0.75,0.75)
                notified = True
        elif (angled_window == True) and (bottomswitch.is_pressed == True) and (topswitch.is_pressed == False) and (window != 2):     #if angled
            window = 2
            filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, red, reason)
            if red == True:
                if (reason == 0) or (reason == 3):
                    redled.blink(0.75,0.75)
                    notified = True
                else:
                    redled.on()
        elif ((bottomswitch.is_pressed == True) and (angled_window == False) and window != 0) or (angled_window == True) and (bottomswitch.is_pressed == True) and (topswitch.is_pressed == True) and (window != 0):      #if closed
            window = 0
            filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, red, reason)
            if red == True:
                redled.on()
        time.sleep(1)
        now = datetime.datetime.now()
