# this code record number oof licks via MPR121 touch sensor
# execute the code with python licking_test.py [rat_id] [experimental duration]


import sys
import os
import time
from pathlib import Path
import numpy as np
import pickle
import easygui
import json

import board
import busio
import digitalio
# import adafruit_mpr121

import atexit
from bipolar_class import Motor
from bipolar_class import rotate_dir
from rgbled_class import RGBLed
from turn_motor import *

import subprocess
import signal
from subprocess import Popen, PIPE



rat_id = sys.argv[1]
# exp_dur = sys.argv[2] # experimental duration, in minutes
date = time.strftime("%Y%m%d")
print(rat_id) #, exp_dur)

proj_path = os.getcwd() #'/home/rig337-testpi/Desktop/katz_lickometer'
print(proj_path)

# get number of trials in total to be delivered
one_trial = easygui.ynbox('Is it only ONE trial to be given?')

# Get experimental parameters based on trial numbers
try:
    if one_trial:
        f = open('./temp/params_1trial.txt', 'r')
    elif 'test' in rat_id:
        f = open('./temp/params_test.txt', 'r')
    else:
        f = open('./temp/params.txt', 'r')
except:
    f = open('./temp/default_params.txt', 'r')

params_vals = []
while True:
    str = f.readline().split(',')[-1]
    if len(str) == 0:
        break
    params_vals.append(str.rstrip())
print(params_vals)

# params_vals = f.readline().split(',')
# params_vals = [x.rstrip() for x in params_vals]
    
# setup trial params
params = easygui.multenterbox('Please enter parameters for this experiment!',
                              'Experiment Parameters',
                              ['[0]Wait time before first trial to be delivered (30s)',
                               '[1]Maximal wait time per trial (60s)',
                               '[2]Number of trials per taste',
                               '[3]Enter inter-trial interval (e.g., ITI=25s)',
                               '[4]Duration of session (in minutes)',
                               '[5]Maximal Lick time per trial (10s)',
                               '[6]Video Recording time (15s)'
                              ],
                              params_vals)

initial_wait = int(params[0]) #30
exp_dur = float(params[4]) * 60 # turn into seconds
max_trial_time = int(params[1]) #60
max_lick_time = int(params[5]) #10
iti = int(params[3]) #30
print(params)

# get tastes and their spout locations
position_f = open('./temp/bottle_positions.txt', 'r')
bot_pos = []
while True:
    pos = position_f.readline().split(',')
    if len(pos[0].rstrip()) == 0:
        break
    if 'position' in pos[0]:
        bot_pos.append(pos[-1].rstrip())
print(bot_pos)

t_list = easygui.multenterbox('Please enter what taste to be used in each Valve.',
                              'Taste List',
                              ['Spout {}'.format(i) for i in [2,4,6,8]],
                              values=bot_pos) #['water', '', 'water', ''])
    
# setting up spouts for each trial
tastes = [i for i in t_list if len(i) > 0]
taste_positions = [2*int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
print([f'Spout-{taste_positions[i]}: {tastes[i]}' for i in range(len(tastes))])

trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(int(params[2]))]
trial_list = np.concatenate(trial_list)
#trial_list = [2,6,2,6,2,6,2,6,2,6,2,6]
print('taste sequency: {}'.format(trial_list))

# setup motor [40 pin header for newer Raspberry Pi's]
step = 24
direction = 23
enable = 25     # Not required - leave unconnected
ms1 = 18
ms2 = 15
ms3 = 14
he_pin = 16 # Hall effect pin

# set up RGB LEDs
red_pin, green_pin, blue_pin = board.D13, board.D19, board.D26
led = RGBLed(red_pin, green_pin, blue_pin)

# setup NosePoke LED cue
np_led = digitalio.DigitalInOut(board.D21)
np_led.direction = digitalio.Direction.OUTPUT

# setup intaninput for touch sensor
#touchIntanIn = digitalio.DigitalInOut(board.D17)
#touchIntanIn.direction = digitalio.Direction.OUTPUT

# setup intaninput for touch sensor
cueIntanIn = digitalio.DigitalInOut(board.D27)
cueIntanIn.direction = digitalio.Direction.OUTPUT

# setup intaninput for spout presentation 
# Spout 2 
sp2IntanIn = digitalio.DigitalInOut(board.D2)
sp2IntanIn.direction = digitalio.Direction.OUTPUT

# Spout 4
sp4IntanIn = digitalio.DigitalInOut(board.D3)
sp4IntanIn.direction = digitalio.Direction.OUTPUT

# Spout 6
sp6IntanIn = digitalio.DigitalInOut(board.D4)
sp6IntanIn.direction = digitalio.Direction.OUTPUT

# Spout 8
sp8IntanIn = digitalio.DigitalInOut(board.D10)
sp8IntanIn.direction = digitalio.Direction.OUTPUT

spoutsIntanIn = {2:sp2IntanIn, 4:sp4IntanIn, 6:sp6IntanIn, 8:sp8IntanIn}

input('===  Please press ENTER to start the experiment! ===')

# # Create MPR121 instance via I2C module
# i2c=busio.I2C(board.SCL, board.SDA)
# # mpr121 = adafruit_mpr121.MPR121(i2c)
# cap = adafruit_mpr121.MPR121(i2c)

# setup nose poke beam break detection
nosepokeIR = digitalio.DigitalInOut(board.D6)
nosepokeIR.direction = digitalio.Direction.INPUT
nosepokeIR.pull = digitalio.Pull.UP
    

# Turn on white LED to set up the start of experiment
led.white_on()
# wait for experiment to start
time.sleep(initial_wait)


exp_init_time = time.time()
# make empty list to save lick data
spout_locs = ['Position {}'.format(i) for i in taste_positions]
licks = {spout:[] for spout in spout_locs}

print('\nPress Ctrl-C to quit.\n')
#video_path = '/home/blechbat/Desktop/temp_lick_pi_code'

dat_folder = os.path.join(proj_path, 'data', '{}'.format(date))
try:
    os.mkdir(dat_folder)
except:
    pass

print(dat_folder)


# save trial start time
#lick_start_path = '/home/blechbat/Desktop/lick_exp/data/20240418'
trial_start_time = open(os.path.join(dat_folder, f'{rat_id}_trial_start.txt'), "w")

for index, trial in enumerate(trial_list):
    if time.time() - exp_init_time >= exp_dur: # if reaches experiment time, exit the for loop
        break

    trial_start_time.write(repr(time.time())+',')
    trial_start_time.flush()    

    # turn on nose poke LED cue and send signal to intan
    if 'led' in rat_id:
        # turn_off house white led light
        led.white_off()
        np_led.value = True
    cueIntanIn.value = True
    spoutsIntanIn[trial].value = True
    
    taste_idx = int((trial - 2) / 2)
    
    # on-screen reminder
    print("\n")
    print("Trial {}_spout{} in Progress~".format(index, trial))
    
    # setup surrent and destinate spout positions
    if index == 0:
        cur_pos = 1
        dest_pos = trial_list[0]
    # using rotate_dir function to get the move of the motor
    turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
#    print(turn_dir, n_shift)
            
    # empty list to save licks for each trial
    this_spout = 'Position {}'.format(trial)
    licks[this_spout].append([])
    # get the number of current trial for that particular spout
    this_trial_num = len(licks[this_spout]) - 1 
    
    # turn on LED_light
    if 'led' in rat_id:
        if trial == taste_positions[0]:
            led.red_on()
        else:
            led.green_on()
    # create Motor instance
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    
    # start nose poke detection
    NP_process = Popen(['python', 'nose_poking.py', rat_id, f'{index}'], shell=False)
    # rotate motor to move spout outside licking hole
    revolution = motora.setStepSize(Motor.EIGHTH) #SIXTEENTH)
    if turn_dir == -1: # turn clockwise
        motora.turn(n_shift * (revolution/8), Motor.CLOCKWISE)
    else:
        motora.turn(n_shift * (revolution/8), Motor.ANTICLOCKWISE)

    # detecting the current status of touch sensor
    last_poke = nosepokeIR.value # return status (touched or not) for each pin as a tuple
    print(last_poke)
    while not last_poke: # stay here if beam broken
        last_poke = nosepokeIR.value # make sure nose-poke is not blocked when starting
        
    trial_init_time = time.time()
    cur_trial_time = max_trial_time
    print('Start detecting licks/nosepokes')
    
    while (time.time() - trial_init_time < cur_trial_time) and \
          (time.time() - exp_init_time < exp_dur):
        current_poke = nosepokeIR.value
        
        # First check if transitioned from not poke to poke.
        if current_poke == 0 and last_poke == 1: # 0 indicates poking
            beam_break = time.time()

        # Next check if transitioned from poke to not poke.
        if current_poke == 1 and last_poke == 0:
            beam_unbroken = time.time()

            if beam_unbroken - beam_break > 0.02: # to avoid noise (from motor)- induced licks
                licks[this_spout][this_trial_num].append(beam_break)
                if len(licks[this_spout][this_trial_num]) == 1:
                    first_lick = time.time()
                    trial_init_time = first_lick # if lick happens, reset the trial_init time
                    cur_trial_time = max_lick_time # if lick happens, reset trial time to maximal lick time
                
                print('Beam Broken! -- Lick_{}'.format(len(licks[this_spout][-1])))

        # Update last state and wait a short period before repeating.
        last_poke = nosepokeIR.value
        time.sleep(0.001)
        
    # make sure the touch sensor is off after the trial
    #touchIntanIn.value = False

    # find rest_direction
    if index < len(trial_list) - 1:
        rest_dir, _ = rotate_dir(trial_list[index], trial_list[index+1], tot_pos = 8)
    else:
        rest_dir = -1
    cur_pos = trial_list[index]
    dest_pos = cur_pos + rest_dir
    dest_pos = dest_pos if dest_pos<=8 else dest_pos-8
    
    # rotate to rest position
    turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
    if turn_dir == -1: # turn clockwise
        motora.turn(n_shift * (revolution/8), Motor.CLOCKWISE)
    else:
        motora.turn(n_shift * (revolution/8), Motor.ANTICLOCKWISE)

    # setup cur_post and dest_pos for next trial
    if index < len(trial_list) - 1:
        cur_pos, dest_pos = dest_pos, trial_list[index+1]
    else:
        pass
    
    # Reset the motor otherwise it will become hot
    motora.reset()
    
    # turn off LED
    if 'led' in rat_id:
        if trial == taste_positions[0]:
            led.red_off()
        else:
            led.green_off()
    
    # turn off nose poke LED
    if 'led' in rat_id:
        np_led.value = False
        
        # turn on house white led light
        led.white_on()
        
    time.sleep(0.001)
    cueIntanIn.value = False
    spoutsIntanIn[trial].value = False
    
    # turn of nosepoke detection
    NP_process.terminate()
    
    # print out number of licks being made on this trial
    print('{} licks on Trial {}'.format(len(licks[this_spout][this_trial_num]), index))
    print('\n')
    print(' =====  Inter-Trial Interval =====')
    print('\n')
    time.sleep(iti-2) # inter - trial intervals

# turn off house white led light when experiment finished
led.white_off()

#print(licks)
for spout in spout_locs:
    num_licks_trial = [len(i) for i in licks[spout]]
    print(spout, num_licks_trial)
    
    tot_licks = np.concatenate(licks[spout])
    print("Total number of licks on {}: {}".format(spout, len(tot_licks)))


# make folder with date as name to save data
# proj_path = '/home/rig337-testpi/Desktop/katz_lickometer'

#date = time.strftime("%Y%m%d")
with open(os.path.join(dat_folder, "{}_lickTime.pkl".format(rat_id)), 'wb') as handle:
    pickle.dump(licks, handle, protocol=pickle.HIGHEST_PROTOCOL)

# save experimental info
param_dict = {}
param_dict['initial_wait'] = initial_wait
param_dict['exp_dur'] = exp_dur
param_dict['max_trial_time'] = max_trial_time
param_dict['max_lick_time'] = max_lick_time
param_dict['iti'] = iti
param_dict['taste_list'] = {k:t for k, t in zip([f'spout-{(i+1)*2}' for i in range(4)], t_list)}
param_dict['trial_list'] = [f'{i}' for i in trial_list]
param_dict['licks'] = licks

with open(os.path.join(dat_folder, "{}_exp_info.json".format(rat_id)), 'w') as f:
    json.dump(param_dict, f)

# with open('./data/{}_{}_exp_info.json'.format(rat_id, date), 'w') as f:
#     json.dump(param_dict, f)
    
print('======= Remove rat from the box to its home cage =======')


#with open('filename.pickle', 'rb') as handle:
#    b = pickle.load(handle)
