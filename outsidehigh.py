import urllib2, json

def outsideforecast():
    f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/forecast/q/OR/Newberg.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    temp_high = parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit']
    return temp_high

print outsideforecast()
