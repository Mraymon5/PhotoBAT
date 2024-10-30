# This code records number of licks via IR beambreak detection
# Execute the code with python licking_test.py [subjID] [experimental duration]

#Import the necessary modules
import os
import time
import numpy as np
import pickle
import easygui
import json
import board
import digitalio
import argparse
import random
from datetime import datetime

#Currently unused modules
import sys
import busio
import atexit
import subprocess
import signal
from subprocess import Popen, PIPE
from pathlib import Path

#%% Local pi functions
from bipolar_class import Motor
from bipolar_class import rotate_dir
from rgbled_class import RGBLed
from turn_motor import *
import CameraControl

#%% Setup Session Parameters

#TODO: Add in a option to set max licks per trial instead of max time, DONE, untested
#TODO: I think the max licks may break compatibility with the camera trigger in some circumstances, FIXED Untested
#TODO: The intan cue gets pulled HIGH and can stay that way

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script for running a BAT session with photobeam lickometer')
    parser.add_argument('subjID', nargs='?', help = 'ID of animal being run', default=None)
    parser.add_argument('--ParamsFile', '-p', help = 'Params file to load for session', default = None)
    parser.add_argument('--OutputFolder', '-o', help = 'Directory to save output', default = None)
    parser.add_argument('--LED', '-l', help = 'Use the house LED (True/[False]/Cue)', default = 'False')
    parser.add_argument('--Camera', '-c', help = 'Record with the behavior camera (True/[False])', default = 'False')
    args = parser.parse_args()
 
if args.ParamsFile is None:
    ParamsFile = easygui.fileopenbox("Select a params file, or cancel for manual entry")

date = time.strftime("%Y%m%d")
subjID = args.subjID
ParamsFile = args.ParamsFile
#print(args.subjID)

if args.OutputFolder is not None:
    proj_path = args.OutputFolder
else:
    proj_path = os.getcwd() #'/home/rig337-testpi/Desktop/katz_lickometer'
    
#print(proj_path)

# Helper function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a givin position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Setup trial parameters
#ParamsFile = '/home/ramartin/Documents/Forms/TrialParamsTemplate.txt'
if ParamsFile is not None:
    with open(ParamsFile, 'r') as params:
        paramsData = params.readlines()
    paramsData = [line.rstrip('\n') for line in paramsData]
    paramsData = [line.split('#')[0] for line in paramsData]
    paramsData = [line.split('=') for line in paramsData]

    NTrials = int([line[1] for line in paramsData if 'NumberOfPres' in line[0]][0])
    Solutions = [line[1].split(',') for line in paramsData if 'Solutions' in line[0]][0]
    Concentrations = [line[1].split(',') for line in paramsData if 'Concentrations' in line[0]][0]
    try:
        LickTime = [line[1].split(',') for line in paramsData if 'LickTime' in line[0]][0]
    except:
        LickTime = list([None])
    LickTime = [intOrNone(trialN, factor=(1/1000)) for trialN in LickTime]
    try:
        LickCount = [line[1].split(',') for line in paramsData if 'LickCount' in line[0]][0]
    except:
        LickCount = list([None])
    LickCount = [intOrNone(trialN) for trialN in LickCount]
    TubeSeq = [line[1].split(',') for line in paramsData if 'TubeSeq' in line[0]][0]
    TubeSeq = [int(trialN) for trialN in TubeSeq]
    IPITimes = [line[1].split(',') for line in paramsData if 'IPITimes' in line[0]][0]
    IPITimes = [int(trialN)/1000 for trialN in IPITimes if len(trialN) != 0]
    IPImin = [int(line[1]) for line in paramsData if 'IPImin' in line[0]][0]
    IPImax = [int(line[1]) for line in paramsData if 'IPImax' in line[0]][0]
    MaxWaitTime = [line[1].split(',') for line in paramsData if 'MaxWaitTime' in line[0]][0]
    MaxWaitTime = [int(trialN)/1000 for trialN in MaxWaitTime]
    SessionTimeLimit = int([line[1] for line in paramsData if 'SessionTimeLimit' in line[0]][0])/1000

    tastes = [stimN for stimN in Solutions if len(stimN) > 0]
    taste_positions = [2*int(stimN+1) for stimN in range(len(Solutions)) if len(Solutions[stimN]) > 0]
    concs = [stimN for stimN in Concentrations if len(stimN) > 0]
        
    #Setup Messages
    trialMsg = '\n'
    IPIMsg = '\n'
    licktimeMsg = '\n'
    waitMsg = '\n'
    
    #Set Lick Time List
    if len(LickTime) < NTrials:
        LickTime = (LickTime * -(-NTrials//len(LickTime)))[:NTrials]
        licktimeMsg = '-Fewer trial durations given than NTrials; recycling positions\n'
    if len(LickTime) > NTrials:
        LickTime = LickTime[:NTrials]
        licktimeMsg = '-More trial durations given than NTrials; trimming excess\n'
    #Set Lick Count List
    if len(LickCount) < NTrials:
        LickCount = (LickCount * -(-NTrials//len(LickCount)))[:NTrials]
        lickcountMsg = '-Fewer trial durations given than NTrials; recycling positions\n'
    if len(LickCount) > NTrials:
        LickCount = LickCount[:NTrials]
        lickcountMsg = '-More trial durations given than NTrials; trimming excess\n'
    #Set Trial List
    if len(TubeSeq) < NTrials:
        TubeSeq = (TubeSeq * -(-NTrials//len(TubeSeq)))[:NTrials]
        trialMsg = '-Fewer bottles positions given than NTrials; recycling positions\n'
    if len(TubeSeq) > NTrials:
        TubeSeq = TubeSeq[:NTrials]
        trialMsg = '-More bottles positions given than NTrials; trimming excess\n'
    #Set IPI List
    if len(IPITimes) == 0 and (len(IPImin) != 0 and len(IPImax) != 0 ):
        IPITimes = [random.randrange(IPImin,IPImax) for trialN in range(NTrials)]
        IPIMsg = '-Randomizing IPIs\n'
    if len(IPITimes) < NTrials:
        IPITimes = (IPITimes * -(-NTrials//len(IPITimes)))[:NTrials]
        IPIMsg = '-Fewer IPIs given than NTrials; recycling positions\n'
    if len(IPITimes) > NTrials:
        IPITimes = IPITimes[:NTrials]
        IPIMsg = '-More IPIs given than NTrials; trimming excess\n'
    #Set Max Wait List
    if len(MaxWaitTime) < NTrials:
        MaxWaitTime = (MaxWaitTime * -(-NTrials//len(MaxWaitTime)))[:NTrials]
        waitMsg = '-Fewer wait limits given than NTrials; recycling positions\n'
    if len(MaxWaitTime) > NTrials:
        MaxWaitTime = MaxWaitTime[:NTrials]
        waitMsg = '-More wait limits given than NTrials; trimming excess\n'
    
    print(trialMsg + licktimeMsg + IPIMsg + waitMsg)
    
    if any(LickTime[trialN] is None and LickCount[trialN] is None for trialN in range(NTrials)):
        raise Exception("Both LickTime and LickCount are None for some trials")
        
    
else:
    params = easygui.multenterbox('Please enter parameters for this experiment!',
                              'Experiment Parameters',
                              ['0: Wait time before first trial to be delivered (30s)',
                               '1: Maximal wait time per trial (60s)',
                               '2: Number of trials per taste (10)',
                               '3: Enter inter-trial interval (30s)',
                               '4: Maxiumum duration of session in minutes (90min)',
                               '5: Maximal Lick time per trial (10s)',
                               '6: Video Recording time (15s)'
                              ],
                              [30,60,10,30,90,10,15])

    #Read params
    initial_wait = int(params[0]) #30, initial_wait
    max_trial_time = int(params[1]) #60, max_trial_time
    iti = int(params[3]) #30, iti
    exp_dur = float(params[4]) * 60 #90, turn into seconds, exp_dur
    max_lick_time = int(params[5]) #10, max_lick_time
    trials_per_taste = int(params[2])
    #print(params)
    
    # Get tastes and their spout locations
    bot_pos = ['water2', '', '', '']
    t_list = easygui.multenterbox('Please enter what taste to be used in each Valve.',
                                  'Taste List',
                                  ['Spout {}'.format(i) for i in ['2, Yellow','4, Blue','6, Green','8, Red']],
                                  values=bot_pos)
        
    # Setting up spouts for each trial
    tastes = [i for i in t_list if len(i) > 0]
    taste_positions = [2*int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
    
    concs = ['']*len(tastes)
    
    trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(trials_per_taste)]
    trial_list = np.concatenate(trial_list)

    # Compute and Convert Session Variables
    NTrials = len(tastes)*trials_per_taste
    LickTime = [max_lick_time]*NTrials
    LickCount = [None]*NTrials
    TubeSeq = trial_list
    IPITimes = list(np.append(initial_wait,([iti]*(NTrials-1)))) #Make a list of IPIs with initial_wait as the first
    MaxWaitTime = [max_trial_time]*NTrials
    SessionTimeLimit = exp_dur

# make empty list to save lick data
spout_locs = ['Position {}'.format(i) for i in taste_positions]
licks = {spout:[] for spout in spout_locs}


try:
    os.mkdir(os.path.join(proj_path, 'data'))
    print("No parent data folder, making one")
except:
    if os.path.isdir(os.path.join(proj_path, 'data')):
        print("Parent data folder found")
    else:
        print("Could not find or create parent data folder, can't save data")

dat_folder = os.path.join(proj_path, 'data', '{}'.format(date))
try:
    os.mkdir(dat_folder)
    print("No session data folder, making one")
except:
    if os.path.isdir(os.path.join(proj_path, 'data')):
        print("Session data folder found")
    else:
        print("Could not find or create session data folder, can't save data")
print(dat_folder)

#%% Setup the output files
outFile = os.path.join(dat_folder, "{}{}.txt".format(date,subjID))
outVersion = 'Version #, 2000\n'    
outSysID = 'System ID, 1\n'
outDate = f'Start Date, {time.strftime("%Y/%m/%d")}\n'
outTime = f"Start Time, {datetime.now().strftime('%H:%M:%S.%f')[:-3]}\n"
outID = f'Animal ID, {subjID}\n'
outCondition = 'Condition, \n'
outWait = f'Max Wait for first Lick is, {MaxWaitTime[0]}\n'
outRetries = 'Max Retries / Presentation, 0\n'
outNumPres = f'Max Number Presentations, {NTrials}\n'
outHeadings = 'PRESENTATION,TUBE,CONCENTRATION,SOLUTION,IPI,LENGTH,LICKS,Latency,Retries\n\n'
outLickTime = f'Lick time limits are, {LickTime}\n'
outLickCount = f'Lick count limits are, {LickCount}\n'
outIPI = f'IPIs are, {IPITimes}\n'
zeroTime = time.time()

with open(outFile, 'w') as outputFile:
    outputFile.write(outFile + '\n' + outVersion + outSysID + outDate + outTime + outID + outCondition + outWait + outRetries + outNumPres + outHeadings)
with open(outFile, 'r') as outputFile:
    outputData = outputFile.readlines()
skipLines = len(outputData)-1 #how many lines to skip when writing to outputDat

# Save Trial Start time
timeFile = os.path.join(dat_folder, f'{subjID}_trial_start.txt')
with open(timeFile, "w") as timeKeeper:
    timeKeeper.write('')

# Get the longest character width provided to stimulus and concentration
padStim = max([len(str(stimN)) for stimN in tastes]) + 1
padConc = max([len(str(stimN)) for stimN in concs]) + 1
padLat = len(str(round(max(MaxWaitTime)*1000))) + 1

if 0: # This is strictly for testing outputs and should be disabled or removed for actual sessions
    for trialN, spoutN in enumerate(TubeSeq): #trialN was index, spoutN was trial #spoutN = 2; trialN = 1
        # Write Trial Data to Output File
        taste_idx = int((spoutN - 2) / 2)
        NLicks = random.randrange(0,35)
        latency = random.randrange(0,round(max(MaxWaitTime)*1000))
        licks = [random.randrange(100,150) for lickN in range(NLicks-1)]
        trialLine = f"{trialN+1:>4},{spoutN:>4},{concs[taste_idx]:>{padConc}},{tastes[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{LickTime[trialN]:>7},{NLicks:>7},{latency:>{padLat}},{0:>7}\n"  # Left-aligned, padded with spaces
        with open(outFile, 'r') as outputFile:
            outputData = outputFile.readlines()
            outputData.insert((skipLines+trialN),trialLine)
        with open(outFile, 'w') as outputFile:
            outputFile.writelines(outputData)
            outLicks = f',{",".join(map(str, licks))}' if len(licks) > 0 else ''
            outputFile.write(f'{trialN + 1}{outLicks}\n')

#%% Setup Hardware

# setup motor [40 pin header for newer Raspberry Pi's]
step = 24       # Pin assigned to motor controller steps
direction = 23  # Pin assigned to motor controller direction
enable = 25     # Not required - leave unconnected
ms1 = 18
ms2 = 15
ms3 = 14
he_pin = 16     # Hall effect pin
cur_pos = 1     # Initial position of table should be 1
dest_pos = TubeSeq[0]

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
#TODO: d5 on the pi goes to port 11 on the intan, and doesn't seem to be controlled here

# setup nose poke beam break detection
nosepokeIR = digitalio.DigitalInOut(board.D6)
nosepokeIR.direction = digitalio.Direction.INPUT
nosepokeIR.pull = digitalio.Pull.UP

# Setup Camera: test settings with CamerControl.preview
if args.Camera == 'True':
    #CameraControl.preview(mode=2)
    camMode = 2
    exposure = 63
    gain = 99
    buffer_duration = 2
    camera = CameraControl.TriggerCaptureFunctions()
    camera.setupCapture(mode = camMode, autoExposure = False, exposure = exposure, gain = gain, buffer_duration = buffer_duration, zeroTime = zeroTime, verbose=True)
    
#%% Finish initializing the session
#Report Parameters
print(outID + outFile + '\n' + outWait + outNumPres + outLickTime + outLickCount + outIPI)
print([f'Spout {taste_positions[i]}: {tastes[i]}' for i in range(len(tastes))])
print('Taste Sequence: {}'.format(TubeSeq))

#Final Check
input('===  Please press ENTER to start the experiment ===')
print('\n=== Press Ctrl-C to abort session ===\n')

# save trial start time
exp_init_time = time.time()
startIPI = exp_init_time

# Turn on white LED to set up the start of experiment
if args.LED == 'True' or args.LED == 'Cue': led.white_on()

#%% Open the trial loop
cleanRun = False
try:
    for trialN, spoutN in enumerate(TubeSeq): #trialN was index, spoutN was trial #spoutN = 2; trialN = 1
        #Set index for identifying stimuli
        taste_idx = int((spoutN - 2) / 2)
        
        #Check max session time
        if time.time() - exp_init_time >= SessionTimeLimit: #If session duration expires, exit the for loop
            break

        #Run Trial IPI
        time.sleep(IPITimes[trialN] - (startIPI - time.time()))
    
        # turn on nose poke LED cue and send signal to intan
        if args.LED == 'Cue':
            # turn_off house white led light
            led.white_off()
            led.green_on() #Turn on the cue light
            #np_led.value = True # turn on nose poke LED
            #Code for differential cue lights
            #if spoutN == taste_positions[0]:
            #    led.red_on()
            #else:
            #   led.green_on()
        cueIntanIn.value = True
        spoutsIntanIn[spoutN].value = True
        
        # on-screen reminder
        print("\n")
        print("Trial {}_spout{} in Progress. Max lick time = {}, Max lick count = {}".format(trialN, spoutN, LickTime[trialN], LickCount[trialN]))
        
        # empty list to save licks for each trial
        this_spout = 'Position {}'.format(spoutN)
        licks[this_spout].append([])
        # get the number of current trial for that particular spout
        this_trial_num = len(licks[this_spout]) - 1 
        
        # using rotate_dir function to get the move of the motor
        turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
    
        # create Motor instance
        motora = Motor(step, direction, enable, ms1, ms2, ms3)
        motora.init()
        revolution = motora.setStepSize(Motor.EIGHTH) #SIXTEENTH)
        
        # start nose poke detection
        NP_process = Popen(['python', 'nose_poking.py', subjID, f'{trialN}'], shell=False)
    
        # rotate motor to move spout outside licking hole
        if turn_dir == -1: # turn clockwise
            motora.turn(n_shift * (revolution/8), Motor.CLOCKWISE)
        else:
            motora.turn(n_shift * (revolution/8), Motor.ANTICLOCKWISE)
            
        #Update motor position
        cur_pos = dest_pos
    
        # detecting the current status of touch sensor
        last_poke = nosepokeIR.value # return status (touched or not) for each pin as a tuple
        print("Beam is clear") if last_poke else print ("Beam is blocked")
        while not last_poke: # stay here if beam broken
            last_poke = nosepokeIR.value # make sure nose-poke is not blocked when starting
            
        #Save Trial Start Time
        trial_start_time = time.time()
        trial_init_time = trial_start_time
        last_break = trial_start_time
        trialTimeLimit = MaxWaitTime[trialN] #Initially set the trial time limit to the max wait for this trial
        print('Start detecting licks/nosepokes')
        #Start the camera
        if args.Camera == 'True': camera.startBuffer()

        while ((time.time() - trial_init_time < trialTimeLimit) if LickTime[trialN] is not None else True) and \
              (time.time() - exp_init_time < SessionTimeLimit) and \
              (len(licks[this_spout][this_trial_num]) < LickCount[trialN] if LickCount[trialN] is not None else True):
            current_poke = nosepokeIR.value
            
            # First check if transitioned from not poke to poke.
            if current_poke == 0 and last_poke == 1: # 0 indicates poking
                beam_break = time.time() #save the time of the beam break
                np_led.value = True

            # Next check if transitioned from poke to not poke.
            if current_poke == 1 and last_poke == 0:
                beam_unbroken = time.time()
                np_led.value = False

                if beam_unbroken - beam_break > 0.02: # to avoid noise (from motor)- induced licks
                    licks[this_spout][this_trial_num].append(round((beam_break-last_break)*1000))
                    if len(licks[this_spout][this_trial_num]) == 1:
                        trial_init_time = beam_break #if lick happens, reset the trial_init time
                        trialTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else 6000 #If a lick happens, reset the trial time limit to maximal lick time
                        if args.Camera == 'True': camera.saveBufferAndCapture(duration=trialTimeLimit, title=f'{subjID}_trial{trialN}', outputFolder=dat_folder, start_time = trial_init_time)
                    last_break = beam_break
                    print('Beam Broken! -- Lick_{}'.format(len(licks[this_spout][-1])))
    
            # Update last state and wait a short period before repeating.
            last_poke = nosepokeIR.value
            time.sleep(0.001)
            
        # make sure the touch sensor is off after the trial
        #touchIntanIn.value = False
    
        #Start the clock for IPI
        startIPI = time.time()
    
        # find rest_direction
        cur_pos = TubeSeq[trialN]
        if trialN < len(TubeSeq) - 1:
            rest_dir, _ = rotate_dir(cur_pos, TubeSeq[trialN+1], tot_pos = 8)
        else:
            rest_dir = -1
        dest_pos = cur_pos + rest_dir
        dest_pos = dest_pos if dest_pos<=8 else dest_pos-8
        
        # rotate to rest position
        turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
        if turn_dir == -1: # turn clockwise
            motora.turn(n_shift * (revolution/8), Motor.CLOCKWISE)
        else:
            motora.turn(n_shift * (revolution/8), Motor.ANTICLOCKWISE)
    
        # setup cur_post and dest_pos for next trial, or just update cur_pos if the session is over
        if trialN < len(TubeSeq) - 1:
            cur_pos, dest_pos = dest_pos, TubeSeq[trialN+1]
        else:
            cur_pos = dest_pos
        
        # Reset the motor otherwise it will become hot
        motora.reset()
        
        # Update LEDs and Intan outs
        if args.LED == 'Cue':
            # Code for differential cue lights
            #if spoutN == taste_positions[0]:
            #    led.red_off()
            #else:
            #    led.green_off()
            led.green_off() #Turn off the cue light
            led.white_on() # turn on house white led light
        if args.LED == 'True': np_led.value = False # turn off nose poke LED
        time.sleep(0.001)
        cueIntanIn.value = False
        spoutsIntanIn[spoutN].value = False
        
        # Turn off nosepoke detection
        NP_process.terminate()
        # Reset the Camera
        if args.Camera == 'True':
            camera.cleanup()
            camera.setupCapture(mode = camMode, autoExposure = False, exposure = exposure, gain = gain, buffer_duration = buffer_duration)
            
        #Write the outputs
        #Save Trial Start time
        with open(timeFile, 'a') as timeKeeper:
            timeKeeper.write(f'{trialN+1}, {trial_start_time}\n')
        trialLicks = licks[this_spout][this_trial_num]
        NLicks = len(trialLicks)
        if NLicks == 0:
            latency = round(MaxWaitTime[trialN]*1000)
        else:
            latency = trialLicks[0]
        trialLine = f"{trialN+1:>4},{spoutN:>4},{concs[taste_idx]:>{padConc}},{tastes[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{LickTime[trialN]:>7},{NLicks:>7},{latency:>{padLat}},{0:>7}\n"  # Left-aligned, padded with spaces
        with open(outFile, 'r') as outputFile:
            outputData = outputFile.readlines()
            outputData.insert((skipLines+trialN),trialLine)
        with open(outFile, 'w') as outputFile:
            outputFile.writelines(outputData)
            outLicks = f',{",".join(map(str, trialLicks[1:]))}' if len(trialLicks) > 0 else ''
            outputFile.write(f'{trialN + 1}{outLicks}\n')

        # print out number of licks being made on this trial
        print('{} licks on Trial {}'.format(NLicks, trialN))
        print('\n=====  Inter-Trial Interval =====\n')
    
    #Note a clean run
    cleanRun = True
    
#%% Ending the session
finally:
    if not cleanRun:
        print("Session interrupted")
        
    # turn off LEDs and Intan outs
    led.white_off()
    led.red_off()
    led.green_off()
    np_led.value = False
    cueIntanIn.value = False
    spoutsIntanIn[spoutN].value = False 
    
    # Return spout to home. This won't work if session is aborted while moving motor
    # create Motor instance
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    revolution = motora.setStepSize(Motor.EIGHTH) #SIXTEENTH)
    # Turn the motor
    turn_dir, n_shift = rotate_dir(cur_pos, 1, tot_pos = 8)
    if turn_dir == -1: # turn clockwise
        motora.turn(n_shift * (revolution/8), Motor.CLOCKWISE)
    else:
        motora.turn(n_shift * (revolution/8), Motor.ANTICLOCKWISE)
    # Shut down motor
    motora.reset()

    #Shut down camera
    if args.Camera == 'True': camera.cleanup()
    
    #print(licks)
    for spout in spout_locs:
        num_licks_trial = [len(i) for i in licks[spout]]
        print(spout, num_licks_trial)
        
        tot_licks = np.concatenate(licks[spout])
        print("Total number of licks on {}: {}".format(spout, len(tot_licks)))
    
    if 0: #old output files, disabled
        with open(os.path.join(dat_folder, "{}_lickTime.pkl".format(subjID)), 'wb') as handle:
            pickle.dump(licks, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        # save experimental info
        param_dict = {}
        param_dict['initial_wait'] = IPITimes[0]
        param_dict['SessionTimeLimit'] = SessionTimeLimit
        param_dict['MaxWaitTime'] = [f'{i}' for i in MaxWaitTime]
        param_dict['LickTime'] = [f'{i}' for i in LickTime]
        param_dict['IPITimes'] = [f'{i}' for i in IPITimes]
        param_dict['taste_list'] = {k:t for k, t in zip([f'spout-{(i+1)*2}' for i in range(4)], t_list)}
        param_dict['TubeSeq'] = [f'{i}' for i in TubeSeq]
        param_dict['licks'] = licks
        
        with open(os.path.join(dat_folder, "{}_exp_info.json".format(subjID)), 'w') as f:
            json.dump(param_dict, f)
    
    print('======= Remove rat from the box to its home cage =======')
