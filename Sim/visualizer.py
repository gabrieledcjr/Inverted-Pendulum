#!/usr/bin/python

import pygame
import math
import sys


class Visualizer:
    def __init__(self, track_length, screen_size=(640, 480),
                 exit_handler=None):
        pygame.init()

        # How much of the screen should the rod length be
        self.rod_length_factor = 0.2

        (self.xsize, self.ysize) = screen_size
        self.track_length = track_length

        # Create screen object.
        self.screen = pygame.display.set_mode(screen_size)

        # Give the screen a white background.
        self.screen.fill((255, 255, 255))

        self.rod_length = self.rod_length_factor * min(self.xsize, self.ysize)

        #calculate track positions on the screen
        self.track_origin = self.rod_length
        self.track_end = self.xsize - self.rod_length

        self.exit_handler = exit_handler

    def draw(self, cartx, angle):
        #first handle any events
        self.handle_events()

        #scale the cart position
        cartx = float(self.xsize-(self.rod_length*2))/self.track_length * cartx + self.track_origin

        #calculate the mass position
        massx = cartx + self.rod_length*math.cos(angle)
        massy = self.ysize/2 - self.rod_length*math.sin(angle)

        # Give the screen a white background.
        self.screen.fill((255, 255, 255))
        # Draw the track
        pygame.draw.line(self.screen, (0,0,0), [self.track_origin, self.ysize/2], [self.track_end, self.ysize/2], 3)

        #draw the rod
        pygame.draw.line(self.screen, (0,0,255), [cartx, self.ysize/2], [massx, massy], 2)

        #draw the cart
        pygame.draw.circle(self.screen, (255,0,0), [int(cartx), self.ysize/2], 8)

        #draw the mass at the end of the rod
        pygame.draw.circle(self.screen, (0,0,0), [int(massx), int(massy)], 5)

        pygame.display.flip()

    def save_screen(self, filename):
            pygame.image.save(self.screen, filename)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print "close window detected, running handler: ", self.exit_handler
                if self.exit_handler is None:
                    sys.exit(0)
                else:
                    self.exit_handler()



def tester():
    import time
    screen = Visualizer(track_length=1000)
    angle = 0
    position = 500
    adder = 1
    while(1):
        screen.draw(position, math.pi/180*angle)
        time.sleep(.01)
        angle += 1
        position += adder
        if(position > 800):
            adder = -1
        if(position < 200):
            adder = 1

if __name__ == "__main__":
    tester()