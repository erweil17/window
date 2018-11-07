#This program allows you to test the inside temperature sensor so you know if it's working or not.
#It will output the temperature it reads from each sensor once every second.
import os
import time
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_file1 = base_dir + '/28-000008773a60/w1_slave'      #Replace with temperature sensor serial number
device_file2 = base_dir + '/28-000008776471/w1_slave'
 
def read_temp_raw(file):
    if file == 1:
        f = open(device_file1, 'r')
    elif file == 2:
        f = open(device_file2, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp_attic():
    lines1 = read_temp_raw(1)
    while lines1[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines1 = read_temp_raw(1)
    equals_pos = lines1[1].find('t=')
    if equals_pos != -1:
        temp_string = lines1[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f

def read_temp_inside():
    lines2 = read_temp_raw(2)
    while lines2[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines2 = read_temp_raw()
    equals_pos = lines2[1].find('t=')
    if equals_pos != -1:
        temp_string = lines2[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f
	
while True:
    print (read_temp_inside())
    print (read_temp_attic())
    print " "
    time.sleep(1)
