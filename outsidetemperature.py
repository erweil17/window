import urllib2
import json
f = urllib2.urlopen('http://api.wunderground.com/api/0a4ad92564829dc7/geolookup/conditions/q/pws:KORNEWBE43.json')
json_string = f.read()

parsed_json = json.loads(json_string)

location = parsed_json['location']['city']

temp_f = parsed_json['current_observation']['temp_f']

print "Current temperature in %s is: %s" % (location, temp_f)

f.close()
