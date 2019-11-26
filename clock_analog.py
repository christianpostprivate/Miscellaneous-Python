# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:41:50 2019

A Pygame app that displays the current system time as an analog clock

"""

import pygame as pg
import traceback
from math import pi, cos, sin
import datetime

vec = pg.math.Vector2

# game settings
W_WIDTH = 600
W_HEIGHT = 600
FPS = 30

# clock settings
RADIUS_SECONDS = 200
WIDTH_SECONDS = 6
RADIUS_MINUTES = 180
WIDTH_MINUTES = 16
RADIUS_HOURS = 140
WIDTH_HOURS = 24
CENTER = (W_WIDTH // 2, W_HEIGHT // 2)


TWO_PI = pi * 2


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((W_WIDTH, W_HEIGHT))
        self.clock = pg.time.Clock()
        self.synced = False

        self.color_scheme = {
                'hand_seconds': (253, 0, 225),
                'hand_minutes': (0, 100, 100),
                'hand_hours': (0, 253, 241),
                'background': (40, 0, 80),
                'ticks_5m': (255, 255, 255),
                'ticks_1m': (200, 200, 200),
                'center': (253, 0, 225)
                }
        
        # save current time
        self.get_system_time()
        
        
    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.events()
            self.update(dt)
            self.draw()
        pg.quit()
        
        
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
    
    
    def update(self, dt):
        # calculate the values for seconds, minutes and hours based on the seconds
        # passed. Also get the angles of the hands
        self.seconds = (self.seconds + dt) % 60
        self.angle_sec = TWO_PI * (int(self.seconds) / 60)
        self.angle_sec += pi / 2
        
        self.minutes = (self.minutes + dt / 60) % 60
        self.angle_min = TWO_PI * (int(self.minutes) / 60)
        self.angle_min += pi / 2
        
        self.hours = (self.hours + dt / 3600) % 12
        self.angle_hour = TWO_PI * (int(self.hours) / 12)
        self.angle_hour += pi / 2
    
        time = f'Current time: {int(self.hours):02d}:{int(self.minutes):02d}:{int(self.seconds):02d}'
        pg.display.set_caption(time)
        
        # sync time after one minute
        if int(self.seconds) % 60 == 0:
            if not self.synced:
                self.get_system_time()
                self.synced = True
        else:
            self.synced = False
    
    
    def draw(self):
        self.screen.fill(self.color_scheme['background'])
        
        # draw the tickmarks
        for i in range(60):
            angle = (i * (360 / 60)) * pi / 180
            x = RADIUS_SECONDS * cos(angle)
            y = RADIUS_SECONDS * sin(angle)
            # translate to center
            x += CENTER[0]
            y += CENTER[1]
            # make hour marks appear thicker
            if i % 5 == 0:
                width = 6
                c = self.color_scheme['ticks_5m']
            else:
                c = self.color_scheme['ticks_1m']
                width = 2
            pg.draw.circle(self.screen, c, (int(x), int(y)), width)
        
        # draw the hours
        v_sec = vec(-RADIUS_HOURS, 0)
        v_sec.rotate_ip(self.angle_hour * 180/pi)
        pg.draw.line(self.screen, self.color_scheme['hand_hours'], 
                     CENTER, CENTER + v_sec, WIDTH_HOURS)
        
        # draw the minutes
        v_min = vec(-RADIUS_MINUTES, 0)
        v_min.rotate_ip(self.angle_min * 180/pi)
        pg.draw.line(self.screen, self.color_scheme['hand_minutes'], 
                     CENTER, CENTER + v_min, WIDTH_MINUTES)
        
        # draw the seconds
        v_hour = vec(-RADIUS_SECONDS, 0)
        v_hour.rotate_ip(self.angle_sec * 180/pi)
        pg.draw.line(self.screen, self.color_scheme['hand_seconds'], 
                     CENTER, CENTER + v_hour, WIDTH_SECONDS)
        
        pg.draw.circle(self.screen, self.color_scheme['center'], CENTER, 12)
        
        pg.display.update()
        
    
    def get_system_time(self):
        # synchronise with system time
        time = datetime.datetime.now().time()
        ms = time.microsecond
        self.seconds = time.second + ms / 1000000
        self.minutes = time.minute + self.seconds / 60
        self.hours = time.hour % 12 + self.minutes / 60
        
        
    

if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()