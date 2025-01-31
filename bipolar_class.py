#!/usr/bin/env python3
#
# $Id: bipolar_class.py,v 1.6 2023/05/23 09:20:03 bob Exp $
# Raspberry Pi bipolar Stepper Motor Driver Class
# Hardware Nema17 12 Volt Stepper High Torque Motor
# Gear Reduction Ratio: 1/64 
# Uses the A4988 H-bridge circuit driver board:
# https://www.mouser.com/pdfDocs/A4988-Datasheet.pdf
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# Modified by Martin Raymond

#%% Module Imports
import sys
import os
import time
import numpy as np

import RPi.GPIO as GPIO

#%%
# The stepper motor can be driven in five different modes 
# See http://en.wikipedia.org/wiki/Stepper_motor

# Step resolution (The last column is the multiplier for one revolution)
FullStep = [0,0,0,1]
HalfStep = [1,0,0,2]
QuarterStep = [0,1,0,4]
EighthStep = [1,1,0,8]
SixteenthStep = [1,1,1,16]

# Other definitions
ENABLE = GPIO.LOW
DISABLE = GPIO.HIGH

#%% Import some Parameters
script_dir = os.path.dirname(os.path.abspath(__file__))
params_path = os.path.join(script_dir, 'BAT_params.txt')

with open(params_path, 'r') as params:
    paramsData = params.readlines()
paramsData = [line.rstrip('\n') for line in paramsData]
paramsData = [line.split('#')[0] for line in paramsData]
paramsData = [line.split('=') for line in paramsData]
tableTotalSteps = int([line[1] for line in paramsData if 'tableTotalSteps' in line[0]][0])

#%%
class Motor:
    # Direction
    CLOCKWISE = 0
    ANTICLOCKWISE = 1

    # Step sizes (Don't change values)
    FULL = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16

    pulse = 0.001 #0.0007
    interval = 0.001 #0.0007
    curPosition = 1
    
    def __init__(self, step, direction, enable, ms1, ms2, ms3, stepTotal = tableTotalSteps):
        self.step = step
        self.direction = direction
        self.enable = enable
        self.ms1 = ms1
        self.ms2 = ms2
        self.ms3 = ms3
        self.stepTotal = stepTotal
        return

    # Initialise GPIO pins for this bipolar motor
    def init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.direction,GPIO.OUT)
        GPIO.setup(self.step,GPIO.OUT)
        GPIO.setup(self.enable,GPIO.OUT)
        GPIO.setup(self.ms1,GPIO.OUT)
        GPIO.setup(self.ms2,GPIO.OUT)
        GPIO.setup(self.ms3,GPIO.OUT)
        self.zeroPosition()
        self.setStepSize(self.FULL)
        return  

    # Reset (stop) motor
    def reset(self):
        GPIO.output(self.step,GPIO.LOW)
        GPIO.output(self.direction,GPIO.LOW)
        GPIO.output(self.enable,GPIO.HIGH)
        GPIO.output(self.ms1,GPIO.LOW)
        GPIO.output(self.ms2,GPIO.LOW)
        GPIO.output(self.ms3,GPIO.LOW)
        return  

    # Set up stepper resolution
    def setStepResolution(self,stepres):
        GPIO.output(self.ms1,stepres[0])
        GPIO.output(self.ms2,stepres[1])
        GPIO.output(self.ms3,stepres[2])
        self.oneRevolution = self.stepTotal * stepres[3]
        return self.oneRevolution

    # Turn the motor
    def turn(self,steps,direction,lock=False):
        count = steps
        GPIO.output(self.enable,ENABLE)
        GPIO.output(self.direction,direction)
        while count > 0:
            GPIO.output(self.step,GPIO.HIGH)
            time.sleep(self.pulse)
            GPIO.output(self.step,GPIO.LOW)
            time.sleep(self.interval)
            count -= 1
        if lock: #MAR if enable/disable is used, this is neccessary to prevent sliding/overshooting
            time.sleep(0.05)
        GPIO.output(self.enable,DISABLE)
        return

    def interrupt(self):
        self.halt = True
        return

    # Increment current position 
    def incrementPosition(self):
        return

    # Increment current position 
    def decrementPosition(self):
        return 

    # Increment current position 
    def zeroPosition(self):
        self.position = 0
        return self.position

    # Goto a specific position
    def goto(self, position):
        newpos = position
        while newpos > self.oneRevolution:
                newpos -= self.oneRevolution

        delta =  newpos - self.position

        # Figure which direction to turn
        if delta > self.oneRevolution/2:
            delta = self.oneRevolution/2 - delta

        elif delta < (0-self.oneRevolution/2):
                delta = self.oneRevolution + delta

        # Turn the most the efficient direction
        if delta > 0:
                self.turn(delta,self.CLOCKWISE)

        elif delta < 0:
                delta = 0 - delta
                self.turn(delta,self.ANTICLOCKWISE)

        self.position = newpos
        if self.position == self.oneRevolution:
                self.position = 0
        return self.position

    # Homing the motor
    def home(self, he_pin = None, adjust_steps=None):
        print("Did you mean to use this? Try rig_funcs.align_zero instead")
        # setup hall effect input
        inport = he_pin
        GPIO.setup(inport, GPIO.IN)
        
        GPIO.output(self.enable,ENABLE)
        GPIO.output(self.direction, 0) # 0 CLOCKWISE
        cur_time = time.time()
        status = 0
        on_steps = 0
        
        last_status = GPIO.input(inport)
        while (time.time()-cur_time) <= 15:
        #while GPIO.input(inport) and (time.time()-cur_time) <= 5:
            GPIO.output(self.step,GPIO.HIGH)
            time.sleep(self.pulse)
            GPIO.output(self.step,GPIO.LOW)
            time.sleep(self.interval)
            
            cur_status = GPIO.input(inport)
            
            if cur_status != last_status: # gets close enough to trigger sensor
                status = status + 1
            if status== 1: # Magnet becomes close
                on_steps = on_steps + 1
            if status == 2: #Magnet becomes far again
                break
            last_status = GPIO.input(inport)
        print(on_steps)
        
        time.sleep(0.5)
        self.turn(on_steps//2, self.ANTICLOCKWISE)
        #self.turn(adjust_steps,self.CLOCKWISE)
        
        GPIO.output(self.enable,DISABLE)
        self.curPosition = 1
        return
    
    # Stop the motor (calls reset)
    def stop(self):
        self.reset()    
        return

    # Lock the motor (also keeps motor warm)
    def lock(self):
        return  

    # Set Step size
    def setStepSize(self,size):

        if size == self.HALF or size == 'HALF':
            steps = self.setStepResolution(HalfStep)    
            self.interval = 0.0075 #0.0007
        elif size == self.QUARTER or size == 'QUARTER':
            steps = self.setStepResolution(QuarterStep) 
            self.interval = 0.001 #0.0007
        elif size == self.EIGHTH or size == 'EIGHTH':
            steps = self.setStepResolution(EighthStep)
            self.interval = 0.001 #0.0007
        elif size == self.SIXTEENTH or size == 'SIXTEENTH':
            steps = self.setStepResolution(SixteenthStep)   
            self.interval = 0.001 #0.0007
        else:
            steps = self.setStepResolution(FullStep)    
            self.interval = 0.01 #0.0007

        self.oneRevolution = steps
        return self.oneRevolution


    # Get number of revolution steps
    def getRevolution(self):
        return self.oneRevolution
        

# End of Unipolar Motor class

def get_cw_steps(cur_pos, dest_pos, tot_pos = None):
    """ count number of steps needed to the destination in clockwise direction"""
    seq = np.arange(cur_pos, cur_pos+tot_pos)
    seq[seq > tot_pos] = seq[seq > tot_pos] - tot_pos
#    print(seq)
    steps_to_dest = np.where(seq == dest_pos)[0] - \
                    np.where(seq == cur_pos)[0]
    return int(steps_to_dest)

def get_ccw_steps(cur_pos, dest_pos, tot_pos = None):
    """ count number of steps needed to the destination in counter-clockwise direction"""
    seq = np.arange(cur_pos+tot_pos, cur_pos, -1)
    seq[seq > tot_pos] = seq[seq > tot_pos] - tot_pos
#    print(seq)
    steps_to_dest = np.where(seq == dest_pos)[0] - \
                    np.where(seq == cur_pos)[0]
    return int(steps_to_dest)

def rotate_dir(cur_pos, dest_pos, tot_pos = 8):
    """determine the steps and rotation direction"""
    cw_steps = get_cw_steps(cur_pos, dest_pos, tot_pos = tot_pos)
    ccw_steps = get_ccw_steps(cur_pos, dest_pos, tot_pos = tot_pos)
#    print(f'cw_steps={cw_steps}; ccw_steps={ccw_steps}')
    if cw_steps <= ccw_steps:
        return 1, cw_steps 
    else:
        return -1, ccw_steps 

