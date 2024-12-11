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
import sys

import argparse
import random
from datetime import datetime
import threading

#Currently unused modules
import digitalio
import busio
import atexit
import subprocess
import signal
from subprocess import Popen, PIPE
from pathlib import Path

#%% Import the MCC library
if sys.platform.startswith('linux'):
#    from uldaq import DaqDevice, DioInfo, DigitalPortIoType, InterfaceType
#    import uldaq as ul
    # Additional imports or initialization specific to uldaq if needed
    print("Using uldaq for Linux")
elif sys.platform.startswith('win'):
#    from mcculw import ul
#    from mcculw.enums import DigitalPortType, DigitalIODirection
#    from mcculw.ul import ULError
    # Additional imports or initialization specific to mcculw if needed
    print("Using mcculw for Windows")
else:
    raise OSError("Unsupported platform")

#%% Local pi functions
from bipolar_class import Motor
from bipolar_class import rotate_dir
from rgbled_class import RGBLed
from turn_motor import *
import CameraControl
import MCC_Setup; mcc = MCC_Setup.MCCInterface()

#%% Helper Functions
# Function to read in a specific bit from the MCC sensor
def getBit(portType, channel, sensorState = None): #sensor_state
    if sensorState is None:
        sensorState = MCC.d_in(board_num, portType)
    return (sensorState >> channel) & 1

def setBit(portType, channel, value):
    # Read the current state of the port
    current_state = MCC.d_in(board_num, portType)
    # Set the specific bit without altering others
    if value:
        new_state = current_state | (1 << channel) #set a channel High
    else:
        new_state = current_state & ~(1 << channel) #set a channel Low
    # Write the new state back to the port
    MCC.d_out(board_num, portType, new_state)

# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a givin position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Function to allow flexible inputs for True in user-supplied strings
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

# Motor control parameters and functions
board_num = 0
last_step_index = {} # Global variable to keep track of the last step index for each motor
stop_motor = threading.Event()
motor_stopped = threading.Event()

shutterChannels = [0, 1, 2, 3]  # Motor 1 on channels A0-A3
shutterMagChannel = 5 #Mag sensor on channel B5
shutterInitSteps = -50 #The number of steps from the mag sensor to the "closed" position
shutterRunSteps = 100 #The number of steps to open/close the shutter
shutterDir = 1 #The base direction of the shutter
shutterSpeed = 0.005

tableChannels = [4, 5, 6, 7]  # Motor 2 on channels A4-A7
tableMagChannel = 4 #Mag sensor on channel B4
tableInitSteps = -17 #The number of steps from the mag sensor to the home position
tableRunSteps = 125 #The number of steps between bottle positions
tableDir = 0 #The base direction of the table
tableSpeed = 0.005

def step_motor(motor_channels, steps, delay=0.01, direction=0):
    global last_step_index
    global stop_motor
    motor_key = tuple(motor_channels)
    # Full-step sequence
    step_sequence = [
        #0b1110,  # Step 0.5
        0b1010,  # Step 1
        #0b1011,  # Step 1.5
        0b1001,  # Step 2
        #0b1101,  # Step 2.5
        0b0101,  # Step 3
        #0b0111,  # Step 3.5
        0b0110,  # Step 4
    ]

    # Reverse the sequence for backward direction
    if (steps < 0):
        steps = abs(steps)
        direction = not direction
    
    if direction:
        step_sequence = step_sequence[::-1]
        
    # Read in the current state of the output to avoid writing over the other motor
    current_state = MCC.d_in(board_num=board_num, port = 0)
    
    # Initialize last step index for the motor if not already set
    if motor_key not in last_step_index:
        last_step_index[motor_key] = 0  # Start at step 0 (step 1 in the sequence)

    # Start from the last step index
    current_step_index = last_step_index[motor_key]
    
    stepped = 0
    while (stepped < steps) and not stop_motor.is_set():
    #for _ in range(steps):
        #if stop_motor.is_set():
        #    break
        print(f'Steps: {stepped}, stop_motor: {stop_motor}')
        # Get the current step from the sequence
        step = step_sequence[current_step_index]

        # Clear the motor's 4 bits using a mask
        mask = ~(0b1111 << motor_channels[0])
        current_state &= mask  # Clears the 4 bits for the motor

        # Set the new 4-bit step sequence shifted to the motor channels
        new_state = current_state | (step << motor_channels[0])

        # Write the updated state to the port
        MCC.d_out(board_num = board_num, port = 0, data = new_state)
        time.sleep(delay)

        # Move to the next step in the sequence
        current_step_index = (current_step_index + 1) % len(step_sequence)
        stepped += 1
    motor_stopped.set()

    # Update the last step index for the motor
    last_step_index[motor_key] = current_step_index
    
    # Set motor to idle
    step = 0b1111
    mask = ~(0b1111 << motor_channels[0]) # Clear the motor's 4 bits using a mask
    current_state &= mask  # Clears the 4 bits for the motor
    new_state = current_state | (step << motor_channels[0]) # Set the new 4-bit step sequence shifted to the motor channels
    MCC.d_out(board_num = board_num, port = 0, data = new_state) # Write the updated state to the port
    stop_motor.clear()
    
def moveShutter(Open = False, Init = False):
    global stop_motor
    if Init:
        print("Backing up...")
        if getBit(portType = 1, channel = shutterMagChannel):
            step_motor(motor_channels = shutterChannels, steps = 50, direction = shutterDir, delay=shutterSpeed)
        print("Done. Advancing to mag switch...")
        stop_motor.clear()
        motor_thread = threading.Thread(target=step_motor, args=(shutterChannels, 10000, shutterSpeed, not shutterDir))
        motor_thread.start()
        while not getBit(portType = 1, channel = shutterMagChannel):
            time.sleep(0.01)
        stop_motor.set()  # Stop the motor loop
        print(f'Main Loop Stop_Motor: {stop_motor}')
        if motor_thread.is_alive():
            motor_thread.join()
        stop_motor.clear()
        motor_stopped.clear()
        print("Done. Moving to home position...")
        step_motor(motor_channels = shutterChannels, steps = shutterInitSteps, direction = shutterDir)
        print("Done. Shutter initialized.")
    else:
        if Open:
            step_motor(motor_channels = shutterChannels, steps = shutterRunSteps, direction = shutterDir, delay = shutterSpeed)
        else:
            step_motor(motor_channels = shutterChannels, steps = shutterRunSteps, direction = not shutterDir, delay = shutterSpeed)

def moveTable(movePos = 0, Init = False):
    global stop_motor
    if Init:
        print("Backing up...")
        step_motor(motor_channels = tableChannels, steps = 50, direction = tableDir, delay=tableSpeed)
        print("Done. Advancing to mag switch...")
        stop_motor.clear()
        motor_thread = threading.Thread(target=step_motor, args=(tableChannels, 10000, tableSpeed, not tableDir))
        motor_thread.start()
        while not getBit(portType = 1, channel = tableMagChannel):
            time.sleep(0.01)
        stop_motor.set()  # Stop the mtotor loop
        print(f'Main Loop Stop_Motor: {stop_motor}')
        if motor_thread.is_alive():
            motor_thread.join()
        stop_motor.clear()
        print("Done. Moving to home position...")
        step_motor(motor_channels = tableChannels, steps = tableInitSteps, direction = tableDir)
        print("Done. Table initialized.")
    else:
        if movePos > 0:
            step_motor(motor_channels = tableChannels, steps = movePos*tableRunSteps, direction = tableDir, delay = tableSpeed)
        else:
            step_motor(motor_channels = tableChannels, steps = abs(movePos)*tableRunSteps, direction = not tableDir, delay = tableSpeed)

#%% Setup Session Parameters

#TODO: Add in a option to set max licks per trial instead of max time, DONE, untested
#TODO: I think the max licks may break compatibility with the camera trigger in some circumstances, FIXED Untested
#TODO: Make the Gui more friendly, DONE, untested

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script for running a BAT session with photobeam lickometer')
    parser.add_argument('subjID', nargs='?', help = 'ID of animal being run', default=None)
    parser.add_argument('--ParamsFile', '-p', help = 'Params file to load for session', default = None)
    parser.add_argument('--OutputFolder', '-o', help = 'Directory to save output', default = None)
    parser.add_argument('--LED', '-l', help = 'Use the house LED (True/[False]/Cue)', default = 'False')
    parser.add_argument('--Camera', '-c', help = 'Record with the behavior camera (True/[False])', default = 'False')
    args = parser.parse_args()

date = time.strftime("%Y%m%d")
subjID = args.subjID
ParamsFile = args.ParamsFile
useLED = args.LED
useCamera = args.Camera
#print(args.subjID)

if args.OutputFolder is not None:
    proj_path = args.OutputFolder
else:
    proj_path = os.getcwd() #'/home/rig337-testpi/Desktop/katz_lickometer'
    
if os.path.isdir(os.path.join(proj_path, 'params')):
    paramsFolder = os.path.join(proj_path, 'params/*')
else:
    paramsFolder = os.path.join(proj_path, '/*')

    
if args.ParamsFile is None:
    ParamsFile = easygui.fileopenbox(msg="Select a params file, or cancel for manual entry", default=paramsFolder)

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
    try:
        useLED = [line[1] for line in paramsData if 'UseLED' in line[0]][0]
    except:
        useLED = useLED
    try:
        useCamera = [line[1] for line in paramsData if 'UseCamera' in line[0]][0]
    except:
        useCamera = useCamera
    
    tastes = [stimN for stimN in Solutions if len(stimN) > 0]
    taste_positions = [2*int(stimN+1) for stimN in range(len(Solutions)) if len(Solutions[stimN]) > 0]
    concs = [stimN for stimN in Concentrations if len(stimN) > 0]
    
    #Setup Messages
    trialMsg = ''
    IPIMsg = ''
    licktimeMsg = ''
    waitMsg = ''
    
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
    params = easygui.multenterbox('Please enter parameters for this experiment.\nPer-trial parameters can set by supplying a params file.',
                              'Experiment Parameters',
                              ['0: Animal ID',
                               '1: Wait time before delivery of first trial (30s)',
                               '2: Maximal wait time per trial (60s)',
                               '3: Number of trials per taste (10)',
                               '4: Enter inter-trial interval (30s)',
                               '5: Maxiumum duration of session in minutes (90min)',
                               '6: Maximum lick time per trial (10s)',
                               '7: Maximum lick count per trial (None)',
                               '8: Use LED indicators?',
                               '9: Use behavior camera?'
                              ],
                              [subjID,30,60,10,30,90,10,None,useLED,useCamera])
    if params is None:
        raise Exception("Session parameters must be supplied manually if no params file is given")

    #Read params
    subjID = params[0]
    initial_wait = int(params[1]) #30, initial_wait
    max_trial_time = int(params[2]) #60, max_trial_time
    trials_per_taste = int(params[3]) #10
    iti = int(params[4]) #30, iti
    exp_dur = float(params[5]) * 60 #90, turn into seconds, exp_dur
    max_lick_time = int(params[6]) if params[6] != '' else None #10, max_lick_time
    max_lick_count = int(params[7]) if params[7] != '' else None #100
    useLED = params[8] #0
    useCamera = params[9] #0
    
    # Get tastes and their spout locations
    bot_pos = ['Water', '', '', '']
    t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                  'Taste List',
                                  ['Spout {}'.format(i) for i in ['2, Yellow','4, Blue','6, Green','8, Red']],
                                  values=bot_pos)
    
    # Setting up spouts for each trial
    tastes = [i for i in t_list if len(i) > 0]
    taste_positions = [2*int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
    
    concs = easygui.multenterbox('Please enter the concentration of each taste.',
                                  'Concentration List',
                                  tastes,
                                  values=[None]*len(tastes))
    
    trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(trials_per_taste)]
    trial_list = np.concatenate(trial_list)
    
    # Compute and Convert Session Variables
    NTrials = len(tastes)*trials_per_taste
    LickTime = [max_lick_time]*NTrials
    LickCount = [max_lick_count]*NTrials
    TubeSeq = trial_list
    IPITimes = list(np.append(initial_wait,([iti]*(NTrials-1)))) #Make a list of IPIs with initial_wait as the first
    MaxWaitTime = [max_trial_time]*NTrials
    SessionTimeLimit = exp_dur
    
# Adjust to flexible inputs for LED and Camera
useLED = isTrue(useLED)
useCamera = isTrue(useCamera)

# Make empty list to save lick data
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
print(f'Data folder is, {dat_folder}')

#%% Setup the output files
fileTail = ''
sessnNum = 0
while os.path.isfile(os.path.join(dat_folder, f"{date}{subjID}{fileTail}.txt")):
    sessnNum += 1
    fileTail = f'_{sessnNum:03}'

outFile = os.path.join(dat_folder, "{}{}{}.txt".format(date,subjID,fileTail))
outVersion = 'Version #, 5.90\n'    
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
outLED = f'Use LEDs, {useLED}\n'
outCamera = f'Use Camera, {useCamera}\n'
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
        timeTemp = [LickTime[trialN] if LickTime[trialN] is not None else 'None'][0]
        trialLine = f"{trialN+1:>4},{spoutN:>4},{concs[taste_idx]:>{padConc}},{tastes[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{timeTemp:>7},{NLicks:>7},{latency:>{padLat}},{0:>7}\n"  # Left-aligned, padded with spaces
        with open(outFile, 'r') as outputFile:
            outputData = outputFile.readlines()
            outputData.insert((skipLines+trialN),trialLine)
        with open(outFile, 'w') as outputFile:
            outputFile.writelines(outputData)
            outLicks = f',{",".join(map(str, licks))}' if len(licks) > 0 else ''
            outputFile.write(f'{trialN + 1}{outLicks}\n')

#Report Parameters
print(outID + 'Output file is, ' + outFile + '\n' + outWait + outNumPres + outLickTime + outLickCount + outIPI + outLED + outCamera)
print([f'Spout {taste_positions[i]}: {tastes[i]}' for i in range(len(tastes))])
print('Taste Sequence: {}'.format(TubeSeq))

#%% Setup Hardware
#TODO: replace all of this with MCC

# Set up MCC ports
try:
    # Set Port A as output for motor relays
    mcc.d_config_port(board_num = board_num, port = 0, direction = 'output')

    # Set Port B as input for 5V TTL sensors
    mcc.d_config_port(board_num = board_num, port = 1, direction = 'input')

    # Set Port C as output for LED indicators or other outputs
    mcc.d_config_port(board_num = board_num, port = 2, direction = 'output')
    mcc.d_config_port(board_num = board_num, port = 3, direction = 'output')

    print("Ports configured successfully.")

except mcc.ul.ULError as e:
    print(f"Error configuring ports: {e}")

# Initialize Table and Shutter
moveShutter(Init=True)
moveTable(Init=True)


# setup motor [40 pin header for newer Raspberry Pi's]
step = 24       # Pin assigned to motor controller steps
direction = 23  # Pin assigned to motor controller direction
enable = 25     # Not required - leave unconnected
ms1 = 18
ms2 = 15
ms3 = 14
he_pin = 16     # Hall effect pin
cur_pos = 1     # Initial position of table should be 1

# setup input for beam break detection
lickSensor = [1, 7] #port B, channel 7

#getBit(portType=lickSensor[0], channel=lickSensor[1])


# setup RGB LEDs
red_pin, green_pin, blue_pin = board.D13, board.D19, board.D26
led = RGBLed(red_pin, green_pin, blue_pin)

# setup NosePoke LED cue
lickLED = [2, 2] #port CL, channel 2
#setBit(portType=lickSignal[0], channel=lickSignal[1],1)

# setup TTL out for beam sensor
lickTTL = [2, 0] #port CL, channel 0
#setBit(portType=lickSignal[0], channel=lickSignal[1],1)

# setup TTL out for trial signal
trialTTL = [2, 1] #port CL, channel 1


# Setup Camera: test settings with CamerControl.preview
if useCamera == 'True':
    #CameraControl.preview(mode=2)
    camMode = 2
    exposure = 63
    gain = 99
    buffer_duration = 2
    camera = CameraControl.TriggerCaptureFunctions()
    camera.setupCapture(mode = camMode, autoExposure = False, exposure = exposure, gain = gain, buffer_duration = buffer_duration, zeroTime = zeroTime, verbose=True)
    
#%% Finish initializing the session
#Final Check
input('===  Please press ENTER to start the experiment ===')
print('\n=== Press Ctrl-C to abort session ===\n')

# save trial start time
exp_init_time = time.time()
startIPI = exp_init_time

# Turn on white LED to set up the start of experiment
if useLED == 'True' or useLED == 'Cue': led.white_on()

#%% Open the trial loop
cleanRun = False
try:
    for trialN, spoutN in enumerate(TubeSeq): #trialN was index, spoutN was trial #spoutN = 2; trialN = 1
        #Set index for identifying stimuli
        taste_idx = int((spoutN - 2) / 2)
        
        #Check max session time
        if time.time() - exp_init_time >= SessionTimeLimit: #If session duration expires, exit the for loop
            break

        # rotate motor to move spout outside licking hole
        dest_pos = TubeSeq[trialN]
        moveTable(movePos=dest_pos-cur_pos)
        cur_pos = dest_pos

        #Run Trial IPI
        time.sleep(IPITimes[trialN] - (startIPI - time.time()))

        # Open Shutter, in a thread so that other operations can proceed
        shutterThread = threading.Thread(target=moveShutter(Open=True))
        shutterThread.start()
    
        # turn on nose poke LED cue and send signal to intan
        if useLED == 'Cue':
            pass #Not implemented yet
        setBit(portType=trialTTL[0], channel=trialTTL[1], value=1)
        
        # on-screen reminder
        print("\n")
        print("Trial {}_spout{} in Progress. Max lick time = {}, Max lick count = {}".format(trialN, spoutN, LickTime[trialN], LickCount[trialN]))
        
        # empty list to save licks for each trial
        this_spout = 'Position {}'.format(spoutN)
        licks[this_spout].append([])
        # get the number of current trial for that particular spout
        this_trial_num = len(licks[this_spout]) - 1 

        # detecting the current status of touch sensor
        last_poke = getBit(portType=lickSensor[0], channel=lickSensor[1])
        print("Lick sensor is clear") if not last_poke else print ("Lick sensor is blocked")
        while last_poke: # stay here if beam broken
            last_poke = getBit(portType=lickSensor[0], channel=lickSensor[1]) # make sure nose-poke is not blocked when starting
        
        #Save Trial Start Time
        trial_start_time = time.time()
        trial_init_time = trial_start_time
        last_lick = trial_start_time #was last_break
        trialTimeLimit = MaxWaitTime[trialN] #Initially set the trial time limit to the max wait for this trial
        print('Start detecting licks/nosepokes')
        #Start the camera
        if useCamera == 'True': camera.startBuffer()

        while ((time.time() - trial_init_time < trialTimeLimit) if LickTime[trialN] is not None else True) and \
              (time.time() - exp_init_time < SessionTimeLimit) and \
              (len(licks[this_spout][this_trial_num]) < LickCount[trialN] if LickCount[trialN] is not None else True):
            current_poke = getBit(portType=lickSensor[0], channel=lickSensor[1])
            
            # First check if transitioned from not poke to poke.
            if current_poke == 1 and last_poke == 0: # 0 indicates poking
                new_lick = time.time() #save the time of the new lick onset. was beam_break
                if (useLED == 'True'): setBit(portType=lickLED[0], channel=lickLED[1], value=1)
                setBit(portType=lickTTL[0], channel=lickTTL[1], value=1)
                
            # Next check if transitioned from poke to not poke.
            if current_poke == 0 and last_poke == 1:
                off_lick = time.time() #save the time the lick sensor stops. was beam_unbroken
                if (useLED == 'True'): setBit(portType=lickLED[0], channel=lickLED[1], value=0)
                setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)

                if off_lick - new_lick > 0.02: # to avoid noise (from motor)- induced licks
                    licks[this_spout][this_trial_num].append(round((new_lick-last_lick)*1000))
                    if len(licks[this_spout][this_trial_num]) == 1:
                        trial_init_time = new_lick #if lick happens, reset the trial_init time
                        trialTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else 6000 #If a lick happens, reset the trial time limit to maximal lick time
                        if useCamera == 'True': camera.saveBufferAndCapture(duration=trialTimeLimit, title=f'{subjID}_trial{trialN}', outputFolder=dat_folder, start_time = trial_init_time)
                    last_lick = new_lick
                    print('Lick_{}'.format(len(licks[this_spout][-1])))
    
            # Update last state and wait a short period before repeating.
            last_poke = getBit(portType=lickSensor[0], channel=lickSensor[1])
            time.sleep(0.001)
            
        #Start the clock for IPI
        startIPI = time.time()
    
        # Close Shutter
        moveShutter(Open=False)
        
        # Update LEDs and Intan outs
        if useLED == 'Cue':
            pass
        
        if useLED == 'True': setBit(portType=lickLED[0], channel=lickLED[1], value=0)
        time.sleep(0.001)
        setBit(portType=trialTTL[0], channel=trialTTL[1], value=0)
        
        # Turn off nosepoke detection
        setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)
        
        # Reset the Camera
        if useCamera == 'True':
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
        timeTemp = [LickTime[trialN] if LickTime[trialN] is not None else 'None'][0]
        trialLine = f"{trialN+1:>4},{spoutN:>4},{concs[taste_idx]:>{padConc}},{tastes[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{timeTemp:>7},{NLicks:>7},{latency:>{padLat}},{0:>7}\n"  # Left-aligned, padded with spaces
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
    setBit(portType=lickLED[0], channel=lickLED[1], value=0)
    setBit(portType=trialTTL[0], channel=trialTTL[1], value=0)
    setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)
    
    # Return spout to home, close shutter
    moveTable(Init=True)
    moveShutter(Init=True)   
    mcc.d_close_port()
    
    #Shut down camera
    if useCamera == 'True': camera.cleanup()
    
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
