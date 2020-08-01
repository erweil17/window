import time, os, urllib2, json, datetime
highurl = 'https://api.weather.gov/gridpoints/PQR/100,96/forecast'

def internet_high():
    if True: # try:
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
    # except:
        # high = -100
        # low = -100
        # daydesc = 'N/A'
        # nightdesc = 'N/A'
        # print "Error: Unable to get outside high temperature"
    return high, low, daydesc, nightdesc
    
var = internet_high()
print var[0]
