
# Import things for running pi codes
import time
import sys
import os

import RPi.GPIO as GPIO
import numpy as np


# Import things for running pi codes
import time
from math import floor
import random
import RPi.GPIO as GPIO

# Import other things for video
from subprocess import Popen
import easygui
import numpy as np
import os

# for circuitpython
import board
import busio
import digitalio

   
def NP_intaninput(IR_port = board.D6, subj_id = None, trial_n=None):
    """
    IR_port 13: adafruit beam break
    IR_port 12: Coulbourn Instruments Nose poke 
    """
    
    #print('Press Ctrl-C to stop the program!')
    
    # Set up intan input from touch sensor
    # IR_inport = IR_port
    
    nosepokeIR = digitalio.DigitalInOut(IR_port)
    nosepokeIR.direction = digitalio.Direction.INPUT
    nosepokeIR.pull = digitalio.Pull.UP
    
    intanInput_port = board.D5 # use for laser intaninput in other programs
    IR_intaninput = digitalio.DigitalInOut(intanInput_port)
    IR_intaninput.direction = digitalio.Direction.OUTPUT
    
    
    date = time.strftime("%Y%m%d")
    trial_n = int(trial_n)
    proj_path = os.getcwd()
    dat_folder = os.path.join(proj_path, 'data',
                            '{}'.format(date))
    try:
        os.mkdir(dat_folder)
    except:
        pass
    
    np_s = open(os.path.join(dat_folder, f'{subj_id}_everyNP_trial{trial_n}_start.txt'), "w")
    np_e = open(os.path.join(dat_folder, f'{subj_id}_everyNP_trial{trial_n}_end.txt'), "w")
    
    #p = 0

    # start detecting touch and send signal to intan
    last_poke = nosepokeIR.value
    try:
        while True:
            current_poke = nosepokeIR.value
            if current_poke == 0 and last_poke == 1: # 0 indicates poking
                beam_break = time.time()
            
                IR_intaninput.value = True
                np_s.write(repr(time.time())+',')
                np_s.flush()
                #p=p+1
                #print('\nPoking_{}'.format(p))

        # Next check if transitioned from touched to not touched.
            if current_poke == 1 and last_poke == 0:
                beam_unbroken = time.time()
                IR_intaninput.value = False
                np_e.write(repr(time.time())+',')
                np_e.flush()
                #print('Not poking')
            
        # Update last state and wait a short period before repeating.
            last_poke = nosepokeIR.value
            time.sleep(0.001)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    
    NP_intaninput(IR_port = board.D6, subj_id = sys.argv[1], trial_n = sys.argv[2])
    


