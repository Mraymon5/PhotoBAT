'''
pi_rig contrains basic functions for using the raspberry pi behavior and electrophysiology rig in the Katz Lab

These functions can be used directly via ipython in a terminal window or called by other codes
'''

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
import adafruit_mpr121
from rgbled_class import RGBLed

import atexit
from bipolar_class import Motor

# # Setup pi board
# GPIO.setwarnings(False)
# GPIO.cleanup()
# GPIO.setmode(GPIO.BOARD)
# 
# # set all the used OUT pins to GPIO.OUT
# GPIO_OUT_PINS = [23, 29, 31, 33, 35, 37,
#                  24, 26, 32, 36, 38, 40,
#                  8,
#                  7, 10, 15]
# for i in GPIO_OUT_PINS:
#     GPIO.setup(i, GPIO.OUT)
#     GPIO.output(i, 0)
#     
    
# To empty taste lines
def clearout(outports = [25,8,7,1], dur = 5):
    # gpio.board = [23,29,31,33,35,37] == >
    # gpio.bcm = [11, 5, 6, 13, 19, 26]

    # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BCM)
    for i in outports:
        GPIO.setup(i, GPIO.OUT) 
 
    for i in outports:
        GPIO.output(i, 1)
        time.sleep(dur)
        GPIO.output(i, 0)
        time.sleep(1)
        print('Tastant line {} clearing complete.'.format(i))


# To calibrate taste lines
def calibrate(outports = [25,8,7,1],
              intaninputs = [2,3,4,10],
              opentime = 0.1, repeats = 5):
    #gpio.board=[23,29,31,33,35,37] ==> gpio.bcm = [11,5,6,13,19,26]
    #gpio.board=[24,26,32,36,38,40] ==> gpio.bcm = [8,7,12,16,20,21]

        # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BCM)
    for i in range(len(outports)):
        GPIO.setup(outports[i], GPIO.OUT)
        GPIO.setup(intaninputs[i], GPIO.OUT)

        # Open ports  
    for rep in range(repeats):
        for i in range(len(outports)):
            GPIO.output(outports[i], 1)
            GPIO.output(intaninputs[i], 1)
        time.sleep(opentime)
        for i in range(len(outports)):
            GPIO.output(outports[i], 0)
            GPIO.output(intaninputs[i], 0)
        time.sleep(1)

    print('Calibration procedure complete.')
    
# Turn on/off a pin
def turn_onoff_pin(pin_num = [18], dur = 2):

        # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BCM)
    for i in pin_num:
        GPIO.setup(pin_num, GPIO.OUT)
    for i in pin_num:
        GPIO.output(i, 0)
    for i in pin_num:
        GPIO.output(i, 1)
        time.sleep(dur)
        GPIO.output(i, 0)

# Passive H2O deliveries
def passive(outports = [25,8,7,1],
            intaninputs = [2,3,4,10],
            tastes = ['water', 'NaCl', 'CA', 'Sucrose'],
            opentimes = [0.01,0.01,0.01,0.01], itimin = 10, itimax = 30, trials = 40):


    import datetime
    # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BCM)
    for i in outports:
        GPIO.setup(i, GPIO.OUT)
    for i in intaninputs:
        GPIO.setup(i, GPIO.OUT)

    tot_trials = [np.random.choice(np.arange(len(outports)),
                                   size=len(outports), replace=False) for i in range(trials)]
    trial_array = np.concatenate(tot_trials)
    print(trial_array)
    count = 0
    time.sleep(30)
    
    # Loop through trials
    for i in trial_array:
        GPIO.output(outports[i], 1)
        GPIO.output(intaninputs[i], 1)
        time.sleep(opentimes[i])
        GPIO.output(outports[i], 0)
        GPIO.output(intaninputs[i], 0)
        count += 1
        iti = random.randint(itimin, itimax)
        print('Trial '+str(count)+' ('+tastes[i]+') of '+str(len(trial_array))+' completed. ITI = '+str(iti)+' sec.')
        time.sleep(iti)

    print('Passive deliveries completed')
    now = datetime.datetime.now()
    now_str = now.strftime('%m_%d_%Y_%H_%M')
    np.save('./data/trial_order_{}.npy'.format(now_str), trial_array)
    
# Passive H2O deliveries
def passive_cue(outports = [11,5,6,13,19,26],
                intaninputs = [8,7,12,16,20,21],
                opentimes = [0.01], itimin = 10, itimax = 30, trials = 150):


    # Setup pi board GPIO ports
    cue_pin = 24 # cue GPIO pin: GPIO24
    GPIO.setmode(GPIO.BCM)
    for i in outports:
        GPIO.setup(i, GPIO.OUT)
    for i in intaninputs:
        GPIO.setup(i, GPIO.OUT)
    GPIO.setup(cue_pin, GPIO.OUT) 

    # Set and radomize trial order
    tot_trials = len(outports) * trials
    count = 0
    trial_array = trials * range(len(outports))
    random.shuffle(trial_array)

    time.sleep(30)
    
    # Loop through trials
    for i in trial_array:
        GPIO.output(cue_pin, 1)
        time.sleep(1)
        GPIO.output(cue_pin, 0)
        time.sleep(1)
        GPIO.output(outports[i], 1)
        GPIO.output(intaninputs[i], 1)
        time.sleep(opentimes[i])
        GPIO.output(outports[i], 0)
        GPIO.output(intaninputs[i], 0)
        count += 1
        iti = random.randint(itimin, itimax)
        print('Trial '+str(count)+' of '+str(tot_trials)+' completed. ITI = '+str(iti)+' sec.')
        time.sleep(iti)

    print('Passive deliveries completed')


# Passive deliveries with video recordings
def passive_with_video(outports = [11,5,6,13,19,26],
                       intaninputs = [8,7,12,16,20,21],
                       tastes = ['water', 'sucrose', 'NaCl', 'quinine', '', ''],
                       opentimes = [0.015, 0.015, 0.015, 0.015, 0.015, 0.015],
                       iti = 15, repeats = 30):

    # Set the outports to outputs
    GPIO.setmode(GPIO.BCM)
    for i in outports:
        GPIO.setup(i, GPIO.OUT)

    # Set the input lines for Intan to outputs
    for i in intan_inports:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, 0)


    # Define the port for the video cue light, and set it as output
    video_cue = 23 # cue as GPIO23
    GPIO.setup(video_cue, GPIO.OUT)

    # Make an ordered array of the number of tastes (length of outports)
    taste_array = []
    for i in range(len(outports)*repeats):
        taste_array.append(int(i%len(outports)))

    # Randomize the array of tastes, and print it
    np.random.shuffle(taste_array)
    print("Chosen sequence of tastes:" + '\n' + str(taste_array))

    # Ask the user for the directory to save the video files in    
    directory = easygui.diropenbox(msg = 'Select the directory to save the videos from this experiment', title = 'Select directory')
    # Change to that directory
    os.chdir(directory)

    # A 10 sec wait before things start
    time.sleep(30)

    # Deliver the tastes according to the order in taste_array
    trials = [1 for i in range(len(outports))]
    for taste in taste_array:
        # Make filename, and start the video in a separate process
        process = Popen('sudo streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t 180 -r 30 -j 75 -w 0 -o ' + tastes[taste] + '_trial_' + str(trials[taste]) + '.avi', shell = True, stdout = None, stdin = None, stderr = None, close_fds = True)

        # Wait for 2 sec, before delivering tastes
        time.sleep(2)

        # Switch on the cue light
        GPIO.output(video_cue, 1)

        # Deliver the taste, and send outputs to Intan
        GPIO.output(outports[taste], 1)
        GPIO.output(intan_inports[taste], 1)
        time.sleep(opentimes[taste])    
        GPIO.output(outports[taste], 0)
        GPIO.output(intan_inports[taste], 0)

        # Switch the light off after 50 ms
        time.sleep(0.050)
        GPIO.output(video_cue, 0)

        # Increment the trial counter for the taste by 1
        trials[taste] += 1

        # Print number of trials completed
        print("Trial " + str(np.sum(trials) - len(outports)) + " of " + str(len(taste_array)) + " completed.")

        # Wait for the iti before delivering next taste
        time.sleep(iti)


# Basic nose poking procedure to train poking for discrimination 2-AFC task
def basic_np(outport = 6, opentime = 0.012, iti = [.4, 1, 2], trials = 200, outtime = 0):

    intaninput = 14
    trial = 1
    inport = 27
    pokelight = 20
    houselight = 24
    lights = 0
    maxtime = 60

        # Setup pi board GPIO ports 
    GPIO.setmode(GPIO.BCMOARD)
    GPIO.setup(pokelight, GPIO.OUT)
    GPIO.setup(houselight, GPIO.OUT)
    GPIO.setup(inport, GPIO.IN)
    GPIO.setup(outport, GPIO.OUT)
    GPIO.setup(intaninput, GPIO.OUT)
    
    time.sleep(30)
    starttime = time.time()

    while trial <= trials:

                # Timer to stop experiment if over 60 mins
        curtime = time.time()
        elapsedtime = round((curtime - starttime)/60, 2)
        if elapsedtime > maxtime:
            GPIO.output(pokelight, 0)
            GPIO.output(houselight, 0)
            break

        if lights == 0:
            GPIO.output(pokelight, 1)
            GPIO.output(houselight, 1)
            lights = 1

                # Check for pokes
        if GPIO.input(inport) == 0:
            poketime = time.time()
            curtime = poketime

                        # Make rat remove nose from nose poke to receive reward
            while (curtime - poketime) <= outtime:
                if GPIO.input(inport) == 0:
                    poketime = time.time()
                curtime = time.time()

                        # Taste delivery and switch off lights
            GPIO.output(outport, 1)
            GPIO.output(intaninput, 1)
            time.sleep(opentime)
            GPIO.output(outport, 0)
            GPIO.output(intaninput, 1)
            GPIO.output(pokelight, 0)
            GPIO.output(houselight, 0)
            print('Trial '+str(trial)+' of '+str(trials)+' completed.')
            trial += 1
            lights = 0

                        # Calculate and execute ITI delay.  Pokes during ITI reset ITI timer.
            if trial <= trials/2:
                delay = floor((random.random()*(iti[1]-iti[0]))*100)/100+iti[0]
            else:
                delay = floor((random.random()*(iti[2]-iti[0]))*100)/100+iti[0]
    
            poketime = time.time()
            curtime = poketime

            while (curtime - poketime) <= delay:
                if GPIO.input(inport) == 0:
                    poketime = time.time()
                curtime = time.time()
        
    print('Basic nose poking has been completed.')

# Passive H2O deliveries
def baseline(intaninputs = [10], iti = 15, dur = 3600):

    # Setup pi board GPIO ports
    GPIO.setmode(GPIO.BCM)
    for i in intaninputs:
        GPIO.setup(i, GPIO.OUT)
       
    # get exp_start time
    start_time = time.time()
    trial_n = 0
    
    # Loop through experimental duration
    while time.time() - start_time <= dur:
        GPIO.output(intaninputs[0], 1)
        time.sleep(0.1)
        GPIO.output(intaninputs[0], 0)

        time.sleep(iti)
        trial_n = trial_n + 1
        if trial_n % int(60/iti) == 0:
            print(f'{round((time.time() - start_time)/60, 2)} min passed')
    
    print('Test completed')
    
    
# Clear all pi board GPIO settings
def clearall():
    
    GPIO.setmode(GPIO.BCM)
    # Pi ports to be cleared
    outports = [11, 5, 6, 13, 19, 26]
    inports = [8, 7, 12, 16, 20, 21]
    #pokelights = [36, 38, 40]
    houselight = 14
    lasers = [18, 25, 23]
    intan = [4, 15, 22]
    
    # Set all ports to default/low state
    for i in intan:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, 0)
    
    for i in outports:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, 0)
        
    for i in inports:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, 0)
        
    #for i in pokelights:
    #    GPIO.setup(i, GPIO.OUT)
    #    GPIO.output(i, 0)
        
    for i in lasers:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i, 0)
        
    GPIO.setup(houselight, GPIO.OUT)
    GPIO.output(houselight, 0)

def getTime():
    try:
        s = np.load('exp_start.npy')
        dt = time.time() - s
        print("{}'".format(int(dt//60)) + '{}"'.format(int(dt%60)))
    except:
        print('Experiment start time not found')
        s = time.time()

def detect_nosepoke(np_inport = 18, wait = 0.5):

    inport = np_inport

        # Setup pi board GPIO ports 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(inport, GPIO.IN)
    
    try:
        while True:
            if GPIO.input(inport) == 0:
                print('Breaking')
            else:
                print('No Poking')
            time.sleep(wait)

    except KeyboardInterrupt:
        pass

def detect_nosepoke_cirpy(np_inport = None, wait = 0.5):

    break_beam = digitalio.DigitalInOut(np_inport)
    break_beam.direction = digitalio.Direction.INPUT
    break_beam.pull = digitalio.Pull.UP
    try:
        while True:
            if not break_beam.value:
                print('Breaking')
            else:
                print('No Breaking')
            time.sleep(wait)

    except KeyboardInterrupt:
        pass
    
    
def detect_lick(record=False):
    # Create MPR121 instance via I2C module
    i2c=busio.I2C(board.SCL, board.SDA)
    # mpr121 = adafruit_mpr121.MPR121(i2c)
    cap = adafruit_mpr121.MPR121(i2c)
        
    if record:
        proj_path = os.getcwd()
        dat_folder = os.path.join(proj_path, 'data')
        subj_id = input('Input rat ID:  ')
        np_s = open(os.path.join(dat_folder, f'{subj_id}_lick_time.txt'), "w")
        n_lick = 0

    print("\nExperiment in Progress!! Press Ctrl + C to quit\n")
    
    # detecting the current status of touch sensor
    last_touched = cap.touched_pins # return status (touched or not) for each pin as a tuple
    while any(last_touched):
        last_touched = cap.touched_pins # make sure last_touched is not touched
        
    try:
        while True:
            current_touched = cap.touched_pins
            # Check each pin's last and current state to see if it was pressed or released.
            for i in range(12):
                # First check if transitioned from not touched to touched.
                if current_touched[i] and not last_touched[i]:
                    touch = time.time()
                    print('touch')

                # Next check if transitioned from touched to not touched.
                if not current_touched[i] and last_touched[i]:
                    #print('{0} released!'.format(i))
                    release = time.time()
                    print('release')

                    if release - touch > 0.02: # to avoid noise (from motor)- induced licks
                        if record:
                            np_s.write(repr(time.time())+',')
                            np_s.flush()
                            n_lick += 1
                            print(f'{n_lick} touched!')
                        else:
                            print('Spout touched!')

            # Update last state and wait a short period before repeating.
            last_touched = current_touched
            time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    
        
def LED_on(led_port = 14, dur = 10):
    # Setup pi board GPIO ports 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led_port, GPIO.OUT)
    GPIO.output(led_port, 1)
    time.sleep(dur)
    GPIO.output(led_port, 0)

def reset_cues():
    # set up RGB LEDs
    red_pin, green_pin, blue_pin = board.D13, board.D19, board.D26
    led = RGBLed(red_pin, green_pin, blue_pin)
    led.white_off()

    # setup NosePoke LED cue
    np_led = digitalio.DigitalInOut(board.D21)
    np_led.direction = digitalio.Direction.OUTPUT
    np_led.value = False
    
# 40 pin header for newer Raspberry Pi's  (BPhysicals location, BCM locations)
# GPIO pins used for step motor
board_nums = [38,40,22,12,10,8]
BCM_nums = [24,23,25,18,15,14]
step, direction, enable, ms1, ms2, ms3 = BCM_nums
hall_e = 16 #11

def turn_clockwise(step,direction,enable,ms1,ms2,ms3, degree=45, rotate='clockwise'):
    motora = Motor(step,direction,enable,ms1,ms2,ms3)
    motora.init()
    
    revolution = motora.setStepSize(Motor.SIXTEENTH) # Motor.EIGHTH
    print(revolution)
    rotate_pt = int(360/degree)
    if rotate == 'clockwise':
        motora.turn(revolution/rotate_pt, Motor.CLOCKWISE)
    elif rotate == 'anticlockwise':
        motora.turn(revolution/rotate_pt, Motor.ANTICLOCKWISE)
    motora.reset()

def detect_magnet(he_inport = hall_e, wait = 0.5):
    # Setup pi board
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    
    inport = he_inport
    GPIO.setup(inport, GPIO.IN)
    
    try:
        while True:
            if GPIO.input(inport) == 0:
                print('Magnet')
            else:
                print('No Magnet')
            time.sleep(wait)

    except KeyboardInterrupt:
        pass

def align_zero1(step,direction,enable,ms1,ms2,ms3, he_inport = None, adjust_steps=None):
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    # rotate motor to move spout outside licking hole
    revolution = motora.setStepSize(Motor.SIXTEENTH)
    cur_time = time.time()
    
    motora.home(he_pin = he_inport, adjust_steps=adjust_steps)
    motora.reset()
    print('Please check if the Motor aligned to initial position!')

def fine_align(step,direction,enable,ms1,ms2,ms3, adjust_steps=None, stay=False):
    """
    adjust_steps:: int # of degrees offset from 45 degree
    stay:: whether the spout to stay at the licking hole after fine-adjustment
    """
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    # rotate motor to move spout outside licking hole
    revolution = motora.setStepSize(Motor.SIXTEENTH)
    
    turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                   degree=45+adjust_steps, rotate='anticlockwise')
    
    while True:
        rotate_degrees = easygui.multenterbox('Fine Adjustment of initial spout position',
                              '# of Rotating Degrees (integer number)',
                              ['[0]Number of rotating degrees (>0:colockwise; <0:counter-clockwise',
                              ],
                              [1])
        rotate_deg = int(rotate_degrees[0])
        #print(rotate_deg)
        if rotate_deg != 0:
            if rotate_deg > 0:
                turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=rotate_deg, rotate='clockwise')
            elif rotate_deg < 0:
                turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=-rotate_deg, rotate='anticlockwise')
        else:
            break
            
    if not stay:
        turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=45, rotate='clockwise')
    motora.reset()
