#!/usr/bin/python
#--------------------------------------
#
#  lcd2004.py
#  20x4 LCD Test Script with
#  backlight control and text justification
#
# https://www.sunfounder.com/
#
#--------------------------------------
 
# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#import
import RPi.GPIO as GPIO
import time, datetime
from gpiozero import LED, Button

# Define GPIO to LCD mapping
LCD_RS = 27
LCD_E  = 22
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
LED_ON = 15
BUTTON1 = 6
BUTTON2 = 13
 
# Define some device constants
LCD_WIDTH = 20    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
 
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line
 
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

led1 = LED(26)
led2 = LED(19)
led11 = LED(5)
button1 = Button(6)
button2 = Button(13)

def main():
  # Main program block
 
  GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
  GPIO.setup(LCD_E, GPIO.OUT)  # E
  GPIO.setup(LCD_RS, GPIO.OUT) # RS
  GPIO.setup(LCD_D4, GPIO.OUT) # DB4
  GPIO.setup(LCD_D5, GPIO.OUT) # DB5
  GPIO.setup(LCD_D6, GPIO.OUT) # DB6
  GPIO.setup(LCD_D7, GPIO.OUT) # DB7
  GPIO.setup(LED_ON, GPIO.OUT) # Backlight enable
 
  # Initialise display
  lcd_init()

  # Toggle backlight on-off-on
  lcd_backlight(True)
  time.sleep(0.5)
  lcd_backlight(False)
  time.sleep(0.5)
  lcd_backlight(True)
  time.sleep(0.5)

  busy = 0
  done = 0
  led1.off()
  led2.on()
  led11.off()

#---------------MAIN PROGRAM -----------------

  while True:
    now = datetime.datetime.now()
    try:
        file = open("data.txt", "r")
        lines = file.readlines()
        inside = lines[4][:-1]
        outside = lines[5][:-1]
        outsidehigh = lines[8][:-1]
        outsidelow = lines[11][:-1]
        actualhigh = lines[12][:-1]
        actuallow = lines[13][:-1]
        daydesc = lines[14][:-1]
        nightdesc = lines[15][:-1]
        file.close()
    except:
        time.sleep(1)

    try:
        file = open("/home/pi/busy/busy.txt", "r")
        lines = file.readlines()
        busy = int(lines[0][:-1])
        file.close()
    except:
        time.sleep(1)
            
    if (outsidehigh == '-100'):
        outsidehigh = 'N/A'
    if (outsidelow == '-100'):
        outsidelow = 'N/A'

    #Set up display strings
    string1 = 'In:' + inside + '     Out:' + outside
    if (now.hour > 6 and now.hour < 17):
        string2 = 'Today: ' + daydesc
        string3 = 'Low:' + actuallow + '     High:' + outsidehigh
    else:
        string2 = 'Tonight: ' + nightdesc
        string3 = 'High:' + actualhigh + '     Low:' + outsidelow

    #Fix the strings for 3 digit numbers
    if (len(string1) > 20):
        string1 = string1.replace('     ','    ')
    if (len(string3) > 20):
        string3 = string3.replace('     ','    ')

    string4 = mode_display(busy)

    #Write to LCD
    lcd_string(string1,LCD_LINE_1,1)
    lcd_string(string3,LCD_LINE_3,1)
    lcd_string(string4,LCD_LINE_4,1)
    
    if (busy == 0):
        led2.on()
        led1.off()
        led11.off()
    else:
        led2.off()
        led1.on()
        led11.on()

    #Controls for busy light
    string2_split = ([string2[i:i+20] for i in range(0, len(string2), 20)])
    for i in range(len(string2_split)):
        lcd_string(string2_split[i],LCD_LINE_2,1)
        waittime = 0
        while (waittime < 100):
            if button1.is_pressed:
                lcd_string(" ",LCD_LINE_1,1)
                lcd_string(" ",LCD_LINE_3,1)
                lcd_string(" ",LCD_LINE_4,1)
                lcd_string(mode_display(busy),LCD_LINE_2,2)

                while button1.is_pressed:
                    if button2.is_pressed:
                        if (busy >= 4):
                            busy = 0
                        else:
                            busy += 1
                        lcd_string(mode_display(busy),LCD_LINE_2,2)
                        while button2.is_pressed:
                            time.sleep(0.05)
                    time.sleep(0.05)
                    
                if (busy == 0):
                    led2.on()
                    led1.off()
                    led11.off()
                else:
                    led2.off()
                    led1.on()
                    led11.on()
                    
                try:
                    file = open("/home/pi/busy/busy.txt", "w")
                    file.write("%s\n" % busy)
                    file.close()
                except:
                    time.sleep(1)
                    
                waittime = 60
                done = 1
            waittime += 1
            time.sleep(0.05)
        if (done == 1):
            done = 0
            break







def mode_display(busy):
  if (busy == 0):
    text = 'Status: Free'
  elif (busy == 1):
    text = 'Status: Busy'
  elif (busy == 2):
    text = 'Status: Games'
  elif (busy == 3):
    text = 'Status: Sleep'
  elif (busy == 4):
    text = 'Status: Work'
  else:
    text = 'Status: Error'
  return text


def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
 
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command
 
  GPIO.output(LCD_RS, mode) # RS
 
  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)
 
def lcd_string(message,line,style):
  # Send string to display
  # style=1 Left justified
  # style=2 Centred
  # style=3 Right justified
 
  if style==1:
    message = message.ljust(LCD_WIDTH," ")
  elif style==2:
    message = message.center(LCD_WIDTH," ")
  elif style==3:
    message = message.rjust(LCD_WIDTH," ")
 
  lcd_byte(line, LCD_CMD)
 
  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
 
def lcd_backlight(flag):
  # Toggle backlight on-off-on
  GPIO.output(LED_ON, flag)
 
if __name__ == '__main__':
 
  try:
    main()
  except KeyboardInterrupt:
    pass
