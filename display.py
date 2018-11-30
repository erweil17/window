import time, urllib2, json
from gpiozero import Button, LED
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#segments = {'a':18, 'b':15, 'c':23, 'd':24, 'e':10, 'f':27, 'g':22}
digits = [9,11,25]
for i in (9,10,11,15,18,22,23,24,25,27):
    GPIO.setup(i, GPIO.OUT)
    GPIO.output(i, 0)
buttonI = Button(8)
buttonO = Button(7)

zero = [18, 15, 23, 24, 10, 27]
one = [15, 23,]
two = [18, 15, 24, 10, 22]
three = [18, 15, 23, 24, 22]
four = [15, 23, 27, 22]
five = [18, 23, 24, 27, 22]
six = [18, 23, 24, 10, 27, 22]
seven = [18, 15, 23]
eight = [18, 15, 23, 24, 10, 27, 22]
nine = [18, 15, 23, 24, 27, 22]
number = [zero, one, two, three, four, five, six, seven, eight, nine]

data = 'data.txt'
def temp_from_file():
    try:
        f = open(data, 'r')
        lines = open(data,'r').read().split('\n')
        f.close
        inside = lines[4]
        outside = lines[5]
        return inside, outside
    except:
        return -100, -100

numberstring = temp_from_file()
insidefloat = float(numberstring[0])
outsidefloat = float(numberstring[1])
inside = int(insidefloat)
outside = int(outsidefloat)
pushed = False
x = 0
while True:
    if (buttonI.is_pressed or buttonO.is_pressed) and pushed == False:
        pushed = True
        if buttonI.is_pressed:
            numbers = inside
            buttonI.wait_for_release()
            test = True
        else:
            numbers = outside
            buttonO.wait_for_release()
            test = False
        x = 50
    if (buttonI.is_pressed or buttonO.is_pressed) and pushed == True:
        pushed = False
        if buttonI.is_pressed:
            buttonI.wait_for_release()
        else:
            buttonO.wait_for_release()
    if pushed == True:
        if x >= 50:
            numberstring = temp_from_file()
            insidefloat = float(numberstring[0])
            outsidefloat = float(numberstring[1])
            if insidefloat > -100.0:
                inside = int(insidefloat)
                outside = int(outsidefloat)
                if test == True:
                    numbers = inside
                else:
                    numbers = outside
            x = 0
#            print "Hi"
        else:
            x += 1

        if numbers < 0:
            negative = True
            numbers = abs(numbers)
        else:
            negative = False
        ones = numbers % 10
        tens = (numbers - ones) / 10
        if tens >= 10:
            hundreds = 1
            tens -= 10
        else:
            hundreds = 0

        t = 0
        while t < 10:
            GPIO.output(number[ones], 1)
            GPIO.output(digits[2], 1)
            time.sleep(0.004)
            GPIO.output(number[ones], 0)
            GPIO.output(digits[2], 0)
            time.sleep(0.001)
            GPIO.output(number[tens], 1)
            GPIO.output(digits[1], 1)
            time.sleep(0.004)
            GPIO.output(number[tens], 0)
            GPIO.output(digits[1], 0)
            time.sleep(0.001)
            if hundreds == 1:
                GPIO.output(number[1], 1)
                GPIO.output(digits[0], 1)
                time.sleep(0.005)
                GPIO.output(number[1], 0)
                GPIO.output(digits[0], 0)
            elif negative == True:
                GPIO.output(22, 1)
                GPIO.output(digits[0], 1)
                time.sleep(0.005)
                GPIO.output(22, 0)
                GPIO.output(digits[0], 0)
            t += 1
    else:
        time.sleep(0.1)
