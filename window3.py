#Pi Window Project v3.0.0 (WORKS AT HOME AND DORM)
#Made by Eric Weiler

import time, os, urllib2, json, datetime
from gpiozero import Button, LED
from time import gmtime, strftime

# --- --- --- --- Enable or disable options here: --- --- --- ---
# ----Change the settings values, don't just comment them out ---

#Set to true to enable the outside temperature
internet_enabled = True

#Set to 0 if in Newberg, 1 if in Corvallis. For getting outside temperature
location = 0

#Set to true to enable the attic temperature
attic_enabled = False

#Set to true to enable the temperature display (separate program)
display_enabled = False

#Get weather alerts along with temperature. Requires internet_enabled == True
alerts_enabled = True

#Use correct temperature sensor. Serial number with letters == 1. If you have no idea which one, guess until it works.
#This option is for the inside sensor. Attic sensor will be opposite value, if enabled
temperature_sensor = 0

#0 for celsius, 1 for fahrenheit
temperature_units = 1

#Enable push notifications on your phone
notifications_enabled = True

#Enable printing values to screen for debugging purposes
debug_mode = False

#Enable error checking, specifically when the outside temperature is wrong
error_checking = True

#Location of data file. 0 when using web server, 1 when using display
file_location = 0

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---




#Set up switches and LEDs
greenled = LED(2)
redled = LED(17)
whiteled = LED(3)
windowbutton = Button(14)
greenled.off()
redled.on()
whiteled.off()

#Set up program based on preferences selected
if display_enabled == True:
    os.system("screen -Smd display python /home/pi/window/display.py")
if location == 0:
    url = 'http://api.wunderground.com/api/0a4ad92564829dc7/conditions/q/pws:KORNEWBE43.json'
elif location == 1:
    url = 'http://api.wunderground.com/api/0a4ad92564829dc7/conditions/q/pws:KORCORVA13.json'
if temperature_sensor == 0:
    temp_file = '/sys/bus/w1/devices/28-000008776471/w1_slave'
    if attic_enabled == True:
        attic_file = '/sys/bus/w1/devices/28-000008773a60/w1_slave'
elif temperature_sensor == 1:
    temp_file = '/sys/bus/w1/devices/28-000008773a60/w1_slave'
    if attic_enabled == True:
        attic_file = '/sys/bus/w1/devices/28-000008776471/w1_slave'

severeweather = ['HUR','TOR','TOW','WRN','SEW','FLO','SVR','VOL','HWW']

#Setting up sensors
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

def notify(message):
    if notifications_enabled == True:
	if message == 0:
	    os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Too warm outside'")
    	if message == 1:
	    os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Too cold outside'")
	if message == 2:
	    os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Raining outside'")
	if message == 3:
            os.system("curl 'https://api.simplepush.io/send/twnQD4/Close your window/Severe weather outside'")

#Get outside temperature
def outsidetemp():
    if internet_enabled == True:
        try:
            f = urllib2.urlopen(url)
            json_string = f.read()
            parsed_json = json.loads(json_string)
            if temperature_units == 1:
                temp = parsed_json['current_observation']['temp_f']
            elif temperature_units == 0:
                temp = parsed_json['current_observation']['temp_c']
            weather = parsed_json['current_observation']['weather']
            if weather == 'Rain':
                raining = 1
            else:
                raining = 0
            f.close()
        except:
            temp = -100
            raining = 2
        return temp, raining
    else:
        return 0, 0

def insidetemp():
    f = open(temp_file, 'r')
    lines = f.readlines()
    f.close()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        if temperature_units == 1:
            tempin = round(temp_f, 1)
        elif temperature_units == 0:
            tempin = round(temp_c, 1)
    return tempin

def outsideforecast():
    if internet_enabled == True:
        if location == 0:
            f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/forecast/q/OR/Newberg.json')
        elif location == 1:
            f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/forecast/q/OR/Corvallis.json')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        if temperature_units == 1:
            temp_high_string = parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit']
        elif temperature_units == 0:
            temp_high_string = parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['celsius']
        f.close()
        temp_high = int(temp_high_string)
        return temp_high
    else:
        return 0

def weatheralerts():
    if internet_enabled == True:
        if alerts_enabled == True:
            if location == 0:
                f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/alerts/q/OR/Newberg.json')
            elif location == 1:
                f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/alerts/q/OR/Medford.json')
            json_string = f.read()
            parsed_json = json.loads(json_string)
            try:
                alert = parsed_json['alerts'][0]['type']
            except:
                alert = 0
            return alert
        else:
            return 0
    else:
        return 0

def attictemp():
    if attic_enabled == True:
        f = open(attic_file, 'r')
        lines = f.readlines()
        f.close()
    	equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            if temperature_units == 1:
                tempattic = round(temp_f, 1)
            elif temperature_units == 0:
                tempattic = round(temp_c, 1)
        return tempattic
    else:
        return 0

def filewrite(month, day, hour, minute, inside, outside, attic, window, forecast, alert):
    if file_location == 1:
        file = open("data.txt", "w")
    elif file_location == 0:
        file = open("/var/www/html/data.txt", "w")
    file.write("%s\n" % month)
    file.write("%s\n" % day)
    file.write("%s\n" % hour)
    if minute < 10:
        file.write("0%s\n" % minute)
    else:
        file.write("%s\n" % minute)
    file.write("%s\n" % inside)
    file.write("%s\n" % outside)
    file.write("%s\n" % attic)
    file.write("%s\n" % window)
    file.write("%s\n" % forecast)
    file.write("%s\n" % alert)

#Variable initial setup
notified = False
outsidehigh = outsideforecast()
alerts = weatheralerts()
if alerts in severeweather:
    activealert = True
    whiteled.blink(1,1)
else:
    activealert = False
    whiteled.off()
if debug_mode == True:
    print "Program starting"
conditions = outsidetemp()
outside = conditions[0]
if error_checking == True:
    error_tries = 0


#Main loop
while True:
    updated = datetime.datetime.now()
    if (updated.hour % 6) == 0 and updated.minute == 0:
        outsidehigh = outsideforecast()
        if debug_mode == True:
            print "High temperature updated"

    if (updated.minute % 10) == 0:
        alerts = weatheralerts()
        if debug_mode == True:
            print "Alerts updated"
        if alerts in severeweather:
            activealert = True
            whiteled.blink(1,1)
        else:
            activealert = False
            whiteled.off()

    if error_checking == True:
        previousoutside = outside

    outsideconditions = outsidetemp()
    outside = outsideconditions[0]
    rain = int(outsideconditions[1])
    inside = insidetemp()
    attic = attictemp()

    if error_checking == True:
        if rain == 2 and outside == -100:
            outside = previousoutside
            print "[" + str(updated.hour) + ":" + str(updated.minute) + "] Unable to get temperature data"
        elif error_tries >= 3:
            print "[" + str(updated.hour) + ":" + str(updated.minute) + "] Accepted error"
            error_tries = 0
        elif previousoutside >= (outside + 5) or previousoutside <= (outside - 5):
            outside = previousoutside
            print "[" + str(updated.hour) + ":" + str(updated.minute) + "] Incorrect temperature detected"
            error_tries += 1
        else:
            error_tries = 0

    if windowbutton.is_pressed == False:
        window = 1
    else:
        window = 0

    filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, alerts)

    if debug_mode == True:
        print "Temperatures updated"
        print updated.hour, updated.minute, updated.second
    cold = False #(for sending the right notification)
    tempdiff = outside - inside
    red = True

#If it's raining outside, you want your window closed
    if rain == 1:
        red = True

#If there's a severe weather alert, close your window
    elif activealert == True:
        red = True

#If it's not too hot outside, you want to leave your window open
    elif outsidehigh <= 78 and outsidehigh >= 70:
        if tempdiff >= 2:
            red = True
        elif outside < 50 and inside <= 71:
            red = True
            cold = True
        else:
            red = False

#If it's cold outside, you want your window open when it's warm
    elif outsidehigh < 70:
        if outside < 60 and inside <= 75:
            red = True
            cold = True
        else:
            red = False

#If it's hot outside, you want your window open when it's cool
    else:
        if updated.hour <= 14:    #Tolerances vary based on time of day
            highdiff = -2.0
            lowdiff = -3.0
        else:
            highdiff = 0.5
            lowdiff = -0.5
        if tempdiff >= highdiff:
            red = True
        elif tempdiff <= lowdiff:
            red = False

#LED and notification controls
    if red == True:
        greenled.off()
        if windowbutton.is_pressed == False:
            if notified == False:
                if activealert == True:
                    notify(3)
                elif rain == 1:
                    notify(2)
                elif cold == True:
                    notify(1)
                else:
                    notify(0)
                notified = True
                redled.blink(0.75,0.75)
        else:
            redled.on()
    else:
        redled.off()
        greenled.on()
        notified = False

#Check every second to see if the window was opened or closed
    now = datetime.datetime.now()
    while ((now.minute % 5) != 0) or (now.second != 0):
        if (windowbutton.is_pressed == False) and (window == 0):
            window = 1
            filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, alerts)
            if red == True:
                redled.blink(0.75,0.75)
                notified = True
        elif (windowbutton.is_pressed == True) and (window == 1):
            window = 0
            filewrite(updated.month, updated.day, updated.hour, updated.minute, inside, outside, attic, window, outsidehigh, alerts)
            if red == True:
                redled.on()
        time.sleep(1)
        now = datetime.datetime.now()
