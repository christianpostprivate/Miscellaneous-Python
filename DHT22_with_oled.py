import RPi.GPIO as GPIO
import board
import adafruit_dht
from lib_oled96.lib_oled96 import ssd1306
from PIL import ImageFont
from smbus import SMBus
import time
from datetime import datetime
import csv
from os import path, system
import threading
import traceback
from collections import deque
import argparse
import logging

filepath = path.dirname(path.abspath(__file__))

logfile = f'{path.basename(__file__).strip(".py")}.log'

logging.basicConfig(filename=path.join(filepath, logfile), 
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# add logging to console
logging.getLogger().addHandler(logging.StreamHandler())


GPIO.setmode(GPIO.BCM)

# pin numbers
BUTTON1 = 14
BUTTON2 = 15
DHT = board.D4


class Button:
    BUTTONUP = 1
    BUTTONDOWN = 2
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.IN)
        self.pin = pin
        self.pressed = False
        self.prev_state = False
        self.time_pressed = 0
        self.events = []
        self.active = True
    
    def disable(self):
        self.active = False
        self.pressed = False
        self.time_pressed = 0
        
    def update(self, dt):
        if not self.active:
            return
        self.pressed = GPIO.input(self.pin)
        if self.pressed:
            self.time_pressed += dt
            if not self.prev_state:
                self.events.append(Button.BUTTONDOWN)
        else:
            self.time_pressed = 0
            if self.prev_state:
                self.events.append(Button.BUTTONUP)
        self.prev_state = self.pressed
     
    def get_events(self):
        # clear the event list
        events, self.events = self.events[::], []
        return events


class Logger:
    def __init__(self, device, read_interval, retry_delay=3):
        # specifiy the DHT device
        self.device = device  
        # set the time between reads (ensure its >= 3)
        self.read_interval = max(3, read_interval)
        # set the time between an unsuccessful read and the next read
        self.retry_delay = retry_delay
        # flag that determines which interval is used between reads
        self.read_successfull = True
        # last read data
        self.row = []
        # set the belay for the main loop
        self.running_delay = 0.1
        # flag for the main loop
        self.should_stop = threading.Event()
        # saves the time for calculating the delta time beween iterations
        self.prev_time = time.time()
        # storage deque for readings
        self.storage = deque()
        # task lists (scheduled actions)
        self.tasks = []
        
        # prepare the log file if it doesn't exist
        self.logfile = path.join(filepath, 'logfile.csv')
        if not path.isfile(self.logfile):
            with open(self.logfile, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(['timestamp', 'time',
                                 'temperature', 'humidity'])

        self.buttons = {
                BUTTON1: Button(BUTTON1),
                BUTTON2: Button(BUTTON2)
            }
        
        # flag for confirmed program termination
        self.end_button_pressed = False
        
        # times a critical error occurred
        self.error_strikes = 0
        self.strike_threshold = 10
        # flag to determine if the pi is shutdown at the end
        self.initialise_shutdown = False

        # initialise OLED
        i2cbus = SMBus(1)
        self.oled = ssd1306(i2cbus)
        self.canvas = self.oled.canvas
        self.oled.cls()
        
        fontpath = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
        self.font = ImageFont.truetype(font=fontpath,
                                  size=14,
                                  encoding='unic')
        
        self.canvas.text((2, 16), 'Waiting for',
                         font=self.font, fill=1)
        self.canvas.text((2, 32), 'sensor data...',
                         font=self.font, fill=1)
        self.oled.display()
        self.display_on = True
    
    def schedule_task(self, time, func):
        # TODO: make this an object instead of list?
        self.tasks.append([0, time, func])
    
    def read_dht22(self, delay=0):
        # thread that sends a request to the DHT22 device after some time
        time.sleep(delay)
        interval = 0
        while not self.should_stop.wait(interval):
            self.read_successfull = False
            try:
                # Print the values to the console
                temperature_c = self.device.temperature
                humidity = self.device.humidity
                timestamp = datetime.timestamp(datetime.now())
                logtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                row = [timestamp, logtime, temperature_c, humidity]
                # append to the deque
                self.storage.append(row)
                # indicate a successfull read and activate the green LED
                self.read_successfull = True
            except RuntimeError as error:
                if ('Timed out waiting for PulseIn message' in error.args[0]
                    or 'DHT sensor not found, check wiring' in error.args[0]):
                    self.error_strikes += 1
                logging.error(error)
            except Exception as e:
                logging.error(e.args[0])
                
            interval = (self.read_interval if self.read_successfull
                    else self.retry_delay)
    
    
    def mainloop(self):
        # start the thread that receives data from the dht11
        tk_thread = threading.Thread(target=lambda: self.read_dht22(1))
        tk_thread.start()
        
        while not self.should_stop.wait(self.running_delay):
            # calculate how much time passed since the last iteration
            now = time.time()
            delta_time = now - self.prev_time
            self.prev_time = now
            
            # check for sensor readings
            if len(self.storage) > 0:
                self.row = self.storage.pop()
                with open(self.logfile, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter=',')
                    writer.writerow(self.row)
                
                # display row on oled
                self.oled.cls()
                
                self.canvas.text((1, 1), 'Temperature:',
                                 font=self.font, fill=1)
                self.canvas.text((1, 17), f'{self.row[2]} °C',
                                 font=self.font, fill=1)
                self.canvas.text((1, 33), 'Humidity:',
                                 font=self.font, fill=1)
                self.canvas.text((1, 50), f'{self.row[3]} %',
                                 font=self.font, fill=1)
                self.oled.display()
                
            # check if too many errors occurred in a row
            if self.error_strikes >= self.strike_threshold:
                self.shutdown()
            
            for number, button in self.buttons.items():
                button.update(delta_time)
                button_events = button.get_events()
                if number == BUTTON1:
                    for ev in button_events:
                        if ev == Button.BUTTONUP:
                            # toggle the display
                            self.display_on = not self.display_on
                            self.oled.onoff(self.display_on) 
                    
                    # shut down after button is pressed for 5 seconds
                    if button.time_pressed > 5:
                        self.schedule_task(5, self.shutdown)
                        button.disable()
                        
                        self.oled.cls()
                        self.canvas.text((1, 1), 'Shutdown in 5',
                                     font=self.font, fill=1)
                        self.oled.display()
                
                elif number == BUTTON2:
                    for ev in button_events:
                        if ev == Button.BUTTONUP:
                            if not self.end_button_pressed: 
                                self.oled.cls()
                                self.canvas.text((1, 1),
                                                 'Press again to',
                                                 font=self.font,
                                                 fill=1)
                                self.canvas.text((1, 17),
                                                 'end program',
                                                 font=self.font,
                                                 fill=1)
                                self.oled.display()
                                self.end_button_pressed = True
                                self.schedule_task(2,
                                    self.reset_button_flag)
                            else:
                                self.oled.cls()
                                self.oled.onoff(False) 
                                self.should_stop.set()
            
            for task in self.tasks:
                # advance the timer
                if task[0] != -1:
                    task[0] += self.running_delay
                # if timer > execution time
                if task[0] >= task[1]:
                    task[2]()
                    task[0] = -1
        
        # deactivate the GPIO pins
        GPIO.cleanup()
    
    def reset_button_flag(self):
        self.end_button_pressed = False
        if self.row:
            self.oled.cls()
            self.canvas.text((1, 1), 'Temperature:',
                             font=self.font, fill=1)
            self.canvas.text((1, 17), f'{self.row[2]} °C',
                             font=self.font, fill=1)
            self.canvas.text((1, 33), 'Humidity:',
                             font=self.font, fill=1)
            self.canvas.text((1, 50), f'{self.row[3]} %',
                             font=self.font, fill=1)
            self.oled.display()
    
    def shutdown(self):
        logging.info('Program terminated')
        self.oled.cls()
        self.oled.onoff(False)
        self.should_stop.set()
        self.initialise_shutdown = True


if __name__ == '__main__':
    # get the interval from command line args
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval',
                        help='Measurement interval in seconds',
                        type=int)
    args = parser.parse_args()
    # Initial the dht device, with data pin connected to:
    dhtDevice = adafruit_dht.DHT22(DHT)
    # initialise the logger object
    if args.interval:
        logger = Logger(device=dhtDevice,
                        read_interval=args.interval)
    else:
        logger = Logger(device=dhtDevice,
                        read_interval=300)  # 5 mins default
    try:
        logger.mainloop()
    except KeyboardInterrupt:
        logger.should_stop.set()
        logger.oled.cls()
    except Exception as e:
        logging.error(e.args[0])
    finally:
        GPIO.cleanup()

if logger.initialise_shutdown:
    time.sleep(3)
    system('sudo shutdown -P now') 
    
