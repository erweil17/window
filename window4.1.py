#Pi Window Project v4
#Made by Eric Weiler
#This program gathers the inside and outside temperatures, compares them, and tells you if you should open your window or not.
#All information is written to a file to be used by other programs. The order in which it is written is available in the filewrite function
import time, os, urllib2, json, datetime
from gpiozero import Button, LED
from time import gmtime, strftime

# --- --- --- --- Enable or disable options here: --- --- --- ---
# ----Change the settings values, don't just comment them out ---

#Set to 0 if in Newberg, 1 if in Corvallis. For getting outside temperature
location = 0

#Set to true to enable the attic temperature
attic_enabled = True

#Set to true to keep track of any pre-coded record temperature. If you don't know what this is, set it to false
record = True

#Use correct temperature sensor. Serial number with letters == 1. If you have no idea which one, guess until it works.
#This option is for the inside sensor. Attic sensor will be opposite value, if enabled
temperature_sensor = 1

#Enable push notifications on your phone
notifications_enabled = False

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---




#Set up switches and LEDs
greenled = LED(2)
redled = LED(17)
windowsensor = Button(14)
topswitch = Button(21)
greenled.off()
redled.on()

#Set up program based on preferences selected
if location == 0:
    url = 'http://api.openweathermap.org/data/2.5/weather?id=5742726&APPID=a3b7103af578dc35a235d70f396c20f1'
    highurl = 'https://api.weather.gov/gridpoints/PQR/100,96/forecast'
elif location == 1:
    url = 'http://api.openweathermap.org/data/2.5/weather?id=5720727&APPID=a3b7103af578dc35a235d70f396c20f1'
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
        temp_k = float(parsed_json['main']['temp'])
        temp_f = round(((temp_k-273.15)*9/5)+32, 1)
        desc = parsed_json['weather'][0]['main']
        if (int(parsed_json['weather'][0]['id']) < 700):
            rain = 1
        else:
            rain = 0
        f.close()
    except:
        temp_f = -100
        rain = 0
        desc = 'N/A'
        print "Error: Unable to get outside temperature"
    return temp_f, rain, desc

def internet_high():
    try:
        f = urllib2.urlopen(highurl)
        json_string = f.read()
        parsed_json = json.loads(json_string)
        if (parsed_json['properties']['periods'][0]['name'] == 'Tonight'):
            low = int(parsed_json['properties']['periods'][0]['temperature'])
            high = int(parsed_json['properties']['periods'][1]['temperature'])
            nightdesc = parsed_json['properties']['periods'][0]['shortForecast']
            daydesc = parsed_json['properties']['periods'][1]['shortForecast']
        else:
            high = int(parsed_json['properties']['periods'][0]['temperature'])
            low = int(parsed_json['properties']['periods'][1]['temperature'])
            daydesc = parsed_json['properties']['periods'][0]['shortForecast']
            nightdesc = parsed_json['properties']['periods'][1]['shortForecast']
    except:
        high = -100
        low = -100
        daydesc = 'N/A'
        nightdesc = 'N/A'
        print "Error: Unable to get outside high temperature"
    return high, low, daydesc, nightdesc

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
    except:
        print "Error: Couldn't get attic temperature"
        return -100

#Writes information to the file, with one piece of data per line. The order in which everything is written from top to bottom is as follows:
#updated month, day, hour, minute, inside temp, outside temp, attic temp, window open (T/F), predicted outside high, should you open or close (T/F), the reason to close, and the type of alert present
def filewrite(month, day, hour, minute, inside, outside, attic, window, outsidehigh, red, reason, outsidelow, actualhigh, actuallow, daydesc, nightdesc):
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
    file.write("%s\n" % outsidehigh)
    file.write("%s\n" % int(red))
    file.write("%s\n" % reason)
    file.write("%s\n" % outsidelow)
    file.write(str(actualhigh) + '\n')
    file.write(str(actuallow) + '\n')
    file.write(daydesc + '\n')
    file.write(nightdesc + '\n')
    file.close()

#This is just a bonus to keep track of the highest recorded attic temperature. It writes to a separate file
def record_filewrite(temperature):
    file = open("attic_record.txt", "r")
    lines = open("attic_record.txt","r").read().split("\n")
    file.close()
    record = lines[0]
    if (temperature > float(record)):
        now = datetime.datetime.now()
        file2 = open("attic_record.txt", "w")
        file2.write("%s\nAchieved at %s:%s on %s/%s\n" % (temperature, now.hour, now.minute, now.month, now.day))
        file2.close()
        
#Variable initial setup
notified = False
first = True
reason = 0
red = True
previous_red = False
actualhigh = 0
actuallow = 100

#Main loop
while True:
    now = datetime.datetime.now()

#Update the outside temperature and weather conditions every 10 minutes
    if ((now.minute % 20) == 0 and now.second == 0) or first == True:
        curr_array = internet_temp()
        if (curr_array[0] != -100 or first == True):
            updated_time = datetime.datetime.now()
            outside = curr_array[0]
            rain = curr_array[1]
            desc = curr_array[2]

#Update the high and low temperatures at 6am. 12pm and 5pm
    if (now.minute == 0 and now.second == 0 and (now.hour == 7 or now.hour == 12 or now.hour == 17)) or first == True:
        fore_array = internet_high()
        if (fore_array[0] != -100 or first == True):
            outsidehigh = fore_array[0]
            outsidelow = fore_array[1]
            daydesc = fore_array[2]
            nightdesc = fore_array[3]
        #Reset previous values
        if now.hour == 7:
            actualhigh = 0
        elif now.hour == 17:
            actuallow = 100

#Update inside temperatures
    inside = insidetemp()
    if attic_enabled == True:
        attic = attictemp()
    else:
        attic = -100

#Keep track of highest and lowest temperatures
    if (actualhigh < outside):
        actualhigh = outside
    if (actuallow > outside):
        actuallow = outside

#Check if window open or closed
    if windowsensor.is_pressed == False:
        window = 1
    else:
        window = 0

#Keep track of record value if enabled
    if record == True:
        record_filewrite(attic)
    tempdiff = outside - inside

    first = False
    previous_red = red
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
        if outside < 60 and inside <= 74:
            red = True
            reason = 1;
        elif inside >= 77 or outside >= 60:
            red = False

#If it's hot outside, you want your window open when it's cool
    else:
        if now.hour <= 14:    #Tolerances vary based on time of day
            highdiff = -4.0
            lowdiff = -5.0
        else:
            highdiff = 0.5
            lowdiff = -0.5
        if tempdiff >= highdiff:
            red = True
        elif tempdiff <= lowdiff:
            red = False
        reason = 0

#Write all the information to a file to be read by other programs
    filewrite(updated_time.month, updated_time.day, updated_time.hour, updated_time.minute, inside, outside, attic, window, outsidehigh, red, reason, outsidelow, actualhigh, actuallow, daydesc, nightdesc)

#LED and notification controls

    if red == True and previous_red == False:
        greenled.off()
        redled.blink(0.5,0.5)
        time.sleep(2)
    elif red == False and previous_red == True:
        redled.off()
        greenled.blink(0.5,0.5)
        time.sleep(2)
        
    if red == True:
        greenled.off()
        if window == 1:
            if notified == False:
                notify(reason)
                notified = True
        redled.on()
    else:
        redled.off()
        greenled.on()
        notified = False
        reason = 0

#Check every second to see if the window was opened or closed. Only run code above once every minute
    time.sleep(1)
    now = datetime.datetime.now()
    while (now.second != 0):
        if window == 0 and (windowsensor.is_pressed == False):
            window = 1
            file = open("window_logs.txt", "a")                    #New feature v4.1: Keep track of when window is opened and closed
            file.write("Opened: %s\n" % now)
            file.close()
        elif window == 1 and (windowsensor.is_pressed == True):
            window = 0
            file = open("window_logs.txt", "a")
            file.write("Closed: %s\n\n" % now)
            file.close()
        # window_record(window)
        time.sleep(1)
        now = datetime.datetime.now()
        filewrite(updated_time.month, updated_time.day, updated_time.hour, updated_time.minute, inside, outside, attic, window, outsidehigh, red, reason, outsidelow, actualhigh, actuallow, daydesc, nightdesc)

