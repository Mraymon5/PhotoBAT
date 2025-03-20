# This code records number of licks via IR beambreak detection
# Execute the code with python licking_test.py [subjID] [experimental duration]

#TODO Make a gui wrapper for all of this. Piloting in MCC

#Import the necessary modules
import os
import time
import numpy as np
import pickle
import easygui
import json
import argparse
import random
from datetime import datetime
import sys
import threading
import queue

#Currently unused modules
import atexit
import subprocess
import signal
from subprocess import Popen, PIPE
from pathlib import Path

#%% Local pi functions
import rig_funcs as rig
try:
    import RPi.GPIO as GPIO
    from bipolar_class import Motor
    from bipolar_class import rotate_dir
    from rgbled_class import RGBLed
except:
    print('Could not import Pi-Specific Modules')

#%% Helper Functions
# Helper function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a given position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Helper function to allow flexible inputs for True in user-supplied strings
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})


#%% Setup Session Parameters
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script for running a BAT session with photobeam lickometer')
    parser.add_argument('subjID', nargs='?', help = 'ID of animal being run', default=None)
    parser.add_argument('--paramsFile', '-p', help = 'Params file to load for session', default = None)
    parser.add_argument('--OutputFolder', '-o', help = 'Directory to save output', default = None)
    parser.add_argument('--LED', '-l', help = 'Use the house LED (True/[False]/Cue)', default = 'False')
    parser.add_argument('--Camera', '-c', help = 'Record with the behavior camera (True/[False])', default = 'False')
    args = parser.parse_args()
 
rigParams = rig.read_params()

date = time.strftime("%Y%m%d")
subjID = args.subjID
paramsFile = args.paramsFile
useLED = args.LED
useCamera = args.Camera
#print(args.subjID)
#print(args.subjID)
proj_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

if args.OutputFolder is not None:
    out_path = args.OutputFolder
else:
    out_path = os.path.join(proj_path, 'data')
try:
    os.mkdir(out_path)
    print("No parent data folder, making one")
except:
    if os.path.isdir(out_path):
        print("Parent data folder found")
    else:
        print("Could not find or create parent data folder, can't save data")

dat_folder = os.path.join(out_path, '{}'.format(date))
try:
    os.mkdir(dat_folder)
    print("No session data folder, making one")
except:
    if os.path.isdir(dat_folder):
        print("Session data folder found")
    else:
        print("Could not find or create session data folder, can't save data")
print(f'Data folder is, {dat_folder}')

    
if os.path.isdir(os.path.join(proj_path, 'params')):
    paramsFolder = os.path.join(proj_path, 'params/*')
else:
    paramsFolder = os.path.join(proj_path, '/*')

    
if args.paramsFile is None:
    paramsFile = easygui.fileopenbox(msg="Select a params file, or cancel for manual entry", default=paramsFolder)

# Setup trial parameters
#paramsFile = '/home/ramartin/Documents/Forms/TrialParamsTemplate.txt'
spoutAddress = np.arange(2, rigParams['tableTotalPositions']+2,2)
NSpouts = len(spoutAddress)
lickMode = rigParams['lickMode']

if paramsFile is not None:
    with open(paramsFile, 'r') as params:
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
    try:
        useLaser = [line[1].split(',') for line in paramsData if 'UseLaser' in line[0]][0]
    except:
        useLaser = [False]

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
    #Set Laser List
    if len(useLaser) < NTrials:
        useLaser = (useLaser * -(-NTrials//len(useLaser)))[:NTrials]
        useLaserMsg = '-Fewer laser trials given than NTrials; recycling positions\n'
    if len(useLaser) > NTrials:
        useLaser = useLaser[:NTrials]
        useLaserMsg = '-More laser trials given than NTrials; trimming excess\n'
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
                               '1: Wait time before first trial to be delivered (30s)',
                               '2: Maximal wait time per trial (60s)',
                               '3: Number of trials per taste (10)',
                               '4: Enter inter-trial interval (30s)',
                               '5: Maxiumum duration of session in minutes (90min)',
                               '6: Maximum lick time per trial (10s)',
                               '7: Maximum lick count per trial (None)',
                               '8: Use LED indicators?',
                               '9: Use behavior camera?',
                               '10: Use laser? (False,Lick,Trial)',
                              ],
                              [subjID,30,60,10,30,90,10,None,useLED,useCamera,False])
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
    useLaser = params[10] #False
    
    # Get tastes and their spout locations
    bot_pos = ['Water'] + ['']*(NSpouts-1)
    Solutions = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                  'Taste List',
                                  ['Spout {}'.format(i) for i in np.arange(2, (NSpouts*2)+2,2)],
                                  values=bot_pos)
    
    # Setting up spouts for each trial
    tastes = [i for i in Solutions if len(i) > 0]
    taste_positions = [2*int(i+1) for i in range(len(Solutions)) if len(Solutions[i]) > 0]
    
    concs = easygui.multenterbox('Please enter the concentration of each taste.',
                                  'Concentration List',
                                  tastes,
                                  values=[None]*len(tastes))
    concN = iter(concs)
    Concentrations = [next(concN) if x != '' else '' for x in Solutions]

    
    trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(trials_per_taste)]
    trial_list = np.concatenate(trial_list)
    
    # Compute and Convert Session Variables
    NTrials = len(tastes)*trials_per_taste
    LickTime = [max_lick_time]*NTrials
    LickCount = [max_lick_count]*NTrials
    useLaser = [useLaser]*NTrials
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
outHeadings = 'PRESENTATION,TUBE,CONCENTRATION,SOLUTION,IPI,LENGTH,LICKS,Latency,Retries,Laser\n\n'
outLickTime = f'Lick time limits are, {LickTime}\n'
outLickCount = f'Lick count limits are, {LickCount}\n'
outIPI = f'IPIs are, {IPITimes}\n'
outLED = f'Use LEDs, {useLED}\n'
outCamera = f'Use Camera, {useCamera}\n'
outLaser = f'Laser Uses are, {useLaser}\n'
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
        trialLine = f"{trialN+1:>4},{spoutN:>4},{Concentrations[taste_idx]:>{padConc}},{Solutions[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{timeTemp:>7},{NLicks:>7},{latency:>{padLat}},{0:>7},{useLaser[trialN]:>7}\n"  # Left-aligned, padded with spaces
        with open(outFile, 'r') as outputFile:
            outputData = outputFile.readlines()
            outputData.insert((skipLines+trialN),trialLine)
        with open(outFile, 'w') as outputFile:
            outputFile.writelines(outputData)
            outLicks = f',{",".join(map(str, licks))}' if len(licks) > 0 else ''
            outputFile.write(f'{trialN + 1}{outLicks}\n')

#Report Parameters
print(outID + 'Output file is, ' + outFile + '\n' + outWait + outNumPres + outLickTime + outLickCount + outIPI + outLED + outCamera + outLaser)
print([f'Spout {taste_positions[i]}: {tastes[i]}' for i in range(len(tastes))])
print('Taste Sequence: {}'.format(TubeSeq))

#%% Setup Hardware

# setup motor [40 pin header for newer Raspberry Pi's]
stepPin =  rigParams['stepPin']       # Pin assigned to motor controller steps
directionPin =  rigParams['directionPin']  # Pin assigned to motor controller direction
enablePin =  rigParams['enablePin']     # Not required - leave unconnected
ms1Pin,ms2Pin,ms3Pin =  rigParams['msPins']
hallPin = rigParams['hallPin']     # Hall effect pin, was he_pin
np_led = rigParams['lickLEDPin'] # LED lick indicator pin, was np_led
nosepokeIR = rigParams['lickBeamPin'] #lick beam input pin, was nosepokeIR
laserPin = rigParams['laserPin'] # laser output pin
beamIntanIn = rigParams['intanBeamPin'] # intan lick indicator output, was beamIntanIn
cueIntanIn = rigParams['intanTrialPin'] # intan trial indicator output, was cueIntanIn
spoutsIntanIn = rigParams['intanSpoutPins'][0:NSpouts]
tot_pos = rigParams['tableTotalPositions'] # Total Positions on table, including walls
stepMode = rigParams['tableStepMode'] #Mode

# set up RGB LEDs
bluePin, greenPin, redPin = rigParams['cueLEDPins']
led = RGBLed(redPin, greenPin, bluePin)

# Set Up Touch Sensor
if lickMode == "cap":
    import board
    import busio
    import adafruit_mpr121
    i2c=busio.I2C(board.SCL, board.SDA)
    capSens = adafruit_mpr121.MPR121(i2c)
    mprPads = [0,1,2,3,4,5,6,7,8,9,10,11]
    pass


#Configure all GPIO pins listed in rigParams
rig.configureIOPins()
if hallPin > 0: rig.align_zero(he_inport=rigParams['hallPin'], adjust_steps=rigParams['tableInitSteps'][stepMode])
# Setup Camera: test settings with CamerControl.preview
if useCamera == 'True':
    import CameraControl
    #CameraControl.preview(mode=2)
    camMode = 2
    exposure = 63
    gain = 99
    buffer_duration = 2
    camera = CameraControl.TriggerCaptureFunctions()
    camera.setupCapture(mode = camMode, autoExposure = False, exposure = exposure, gain = gain, buffer_duration = buffer_duration, zeroTime = zeroTime, verbose=True)
    
#%% Finish initializing the session
#Final Check
rig.AbortEvent.set() #Set the abort event, which will be turned off to start the session
rig.TrialEvent.set() #Set the trial event, which will be turned off to start the session
rig.cleanRun.clear()
#guiThread = threading.Thread(target=rig.TrialGui, kwargs={'paramsFile':paramsFile, 'outputFile':outputFile, 'subjID':subjID}, daemon=True)
#guiThread.start()
def runSession():
    #input('===  Please press ENTER to start the experiment ===')
    print('\n=== Press Ctrl-C to abort session ===\n')
    while rig.AbortEvent.is_set():
        try:
            time.sleep(0.001)
        except:
            rig.AbortEvent.clear()
    # save trial start time
    exp_init_time = time.time()
    startIPI = exp_init_time
    
    # Turn on white LED to set up the start of experiment
    if useLED == 'True' or useLED == 'Cue': led.white_on()
    
    #%% Open the trial loop
    cur_pos = 1     # Initial position of table should be 1
    dest_pos = TubeSeq[0] #Set initial destination
    try:
        for trialN, spoutN in enumerate(TubeSeq): #trialN was index, spoutN was trial #spoutN = 2; trialN = 1
            #Set index for identifying stimuli
            taste_idx = int((spoutN - 2) / 2)
            
            #Check max session time
            if time.time() - exp_init_time >= SessionTimeLimit: #If session duration expires, exit the for loop
                break
    
            #Run Trial IPI
            rig.timerQueue.put(startIPI+IPITimes[trialN]) #push the timeout time to GUI
            rig.TrialEvent.clear() #Let gui know IPI has started

            while (time.time() - startIPI) < IPITimes[trialN]:
                if rig.AbortEvent.is_set():
                    raise KeyboardInterrupt()
                time.sleep(0.001)
                
            # create Motor instance
            motora = Motor(stepPin, directionPin, enablePin, ms1Pin, ms2Pin, ms3Pin)
            motora.init()
            revolution = motora.setStepSize(stepMode)
            
            # using rotate_dir function to get the move of the motor
            turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = tot_pos)

            
            #Start the camera
            if useCamera == 'True': camera.startBuffer()

            # rotate motor to move spout outside licking hole
            direction = Motor.CLOCKWISE if turn_dir == -1 else Motor.ANTICLOCKWISE
            motorThread = threading.Thread(target=lambda: motora.turn(n_shift * (revolution / tot_pos), direction))
            motorThread.start()
                
            #Update motor position
            cur_pos = dest_pos

            # turn on nose poke LED cue and send signal to intan
            if useLED == 'Cue':
                # turn_off house white led light
                led.white_off()
                led.green_on() #Turn on the cue light
                #Code for differential cue lights
                #if spoutN == taste_positions[0]:
                #    led.red_on()
                #else:
                #   led.green_on()
            if useLaser[trialN] == 'Trial':
                laserTimeLimit = [LickTime[trialN] if LickTime[trialN] is not None else 5][0]
                print(f'laser pin: {laserPin}, duration: {laserTimeLimit}')
                laserThread = threading.Thread(target=rig.fireLaser, kwargs={'laserPin':laserPin, 'duration':laserTimeLimit})
                laserThread.start()
            GPIO.output(cueIntanIn,GPIO.HIGH) #Set cue Intan in High
            GPIO.output(spoutsIntanIn[taste_idx],GPIO.HIGH) #Set the correct spout Intan in High
            
            # on-screen reminder
            print("\n")
            print("Trial {}_spout{} in Progress. Max lick time = {}, Max lick count = {}".format(trialN, spoutN, LickTime[trialN], LickCount[trialN]))
            
            # empty list to save licks for each trial
            this_spout = 'Position {}'.format(spoutN)
            licks[this_spout].append([])
            # get the number of current trial for that particular spout
            this_trial_num = len(licks[this_spout]) - 1 
            
            # start nose poke detection
            NP_process = Popen(['python', 'nose_poking.py', subjID, f'{trialN}'], shell=False)
        
            # detecting the current status of touch sensor
            if lickMode == 'cap':
                last_poke = capSens.touched_pins # return status (touched or not) for each pin as a tuple
                while any(last_poke):
                    last_poke = capSens.touched_pins # make sure last_poke is not touched
            else:
                last_poke = GPIO.input(nosepokeIR) # return status (touched or not) for each pin as a tuple
                print("Beam is clear") if last_poke else print ("Beam is blocked")
                while not last_poke: # stay here if beam broken
                    last_poke = GPIO.input(nosepokeIR) # make sure nose-poke is not blocked when starting
                
            #Save Trial Start Time
            trial_start_time = time.time()
            trial_init_time = trial_start_time
            last_break = trial_start_time
            trialTimeLimit = MaxWaitTime[trialN] #Initially set the trial time limit to the max wait for this trial
            print('Start detecting licks/nosepokes')
    
            #Update Lick Count and trial event in GUI
            rig.lickQueue.put(len(licks[this_spout][this_trial_num])) #push lick count to gui
            rig.timerQueue.put(trial_start_time+trialTimeLimit) #push the timeout time to GUI
            rig.TrialEvent.set() #Let gui know a trial has started
    
            while ((time.time() - trial_init_time < trialTimeLimit) if trialTimeLimit is not None else True) and \
                  (time.time() - exp_init_time < SessionTimeLimit) and \
                  (len(licks[this_spout][this_trial_num]) < LickCount[trialN] if LickCount[trialN] is not None else True):
                
                if rig.AbortEvent.is_set():
                    raise KeyboardInterrupt()
                if lickMode == 'cap':
                    current_poke = (capSens.touched_pins)[mprPads[taste_idx]]
                else:
                    current_poke = GPIO.input(nosepokeIR)
                
                # First check if transitioned from not poke to poke.
                if current_poke == 0 and last_poke == 1: # 0 indicates poking
                    beam_break = time.time() #save the time of the beam break
                    GPIO.output(np_led,GPIO.HIGH) #Turn on the beam indicator LED
    
                # Next check if transitioned from poke to not poke.
                if current_poke == 1 and last_poke == 0:
                    beam_unbroken = time.time()
                    GPIO.output(np_led,GPIO.LOW) #Turn off the beam indicator LED
    
                    if beam_unbroken - beam_break > 0.02: # to avoid noise (from motor)- induced licks
                        licks[this_spout][this_trial_num].append(round((beam_break-last_break)*1000))
                        rig.lickQueue.put(len(licks[this_spout][this_trial_num])) #Send new lick to GUI
                        if len(licks[this_spout][this_trial_num]) == 1: #If this is the first lick:
                            trial_init_time = beam_break #if lick happens, reset the trial_init time
                            trialTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else None #If a lick happens, reset the trial time limit to maximal lick time
                            if trialTimeLimit is not None:
                                rig.timerQueue.put(trial_init_time+trialTimeLimit) #push the timeout time to GUI
                            else:
                                rig.timerQueue.put(trial_init_time) #push the timeout time to GUI
                            camTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else 10 #If a lick happens, reset the trial time limit to maximal lick time
                            if useCamera == 'True': camera.saveBufferAndCapture(duration=min(10,camTimeLimit), title=f'{subjID}_trial{trialN}', outputFolder=dat_folder, start_time = trial_init_time) #Camera recording period capped to 20sec
                            if useLaser[trialN] == 'Lick':
                                laserTimeLimit = [LickTime[trialN] if LickTime[trialN] is not None else 5][0]
                                print(f'laser pin: {laserPin}, duration: {laserTimeLimit}')
                                laserThread = threading.Thread(target=rig.fireLaser, kwargs={'laserPin':laserPin, 'duration':laserTimeLimit})
                                laserThread.start()
                        last_break = beam_break
                        print('Beam Broken! -- Lick_{}'.format(len(licks[this_spout][-1])))
        
                # Update last state and wait a short period before repeating.
                last_poke = current_poke
                time.sleep(0.001)
                
            # make sure the touch sensor is off after the trial
            #touchIntanIn.value = False
        
            #Start the clock for IPI
            startIPI = time.time()
            
            # find rest_direction
            cur_pos = TubeSeq[trialN]
            if trialN < len(TubeSeq) - 1:
                rest_dir, _ = rotate_dir(cur_pos, TubeSeq[trialN+1], tot_pos = tot_pos)
            else:
                rest_dir = -1
            dest_pos = cur_pos + rest_dir
            dest_pos = dest_pos if dest_pos<=tot_pos else dest_pos-tot_pos
            
            # rotate to rest position
            turn_dir, n_shift = rotate_dir(cur_pos, dest_pos, tot_pos = tot_pos)
            if turn_dir == -1: # turn clockwise
                motora.turn(n_shift * (revolution/tot_pos), Motor.CLOCKWISE)
            else:
                motora.turn(n_shift * (revolution/tot_pos), Motor.ANTICLOCKWISE)
        
            # setup cur_post and dest_pos for next trial, or just update cur_pos if the session is over
            if trialN < len(TubeSeq) - 1:
                cur_pos, dest_pos = dest_pos, TubeSeq[trialN+1]
            else:
                cur_pos = dest_pos
            
            # Reset the motor otherwise it will become hot
            motora.reset()
            
            # Update LEDs and Intan outs
            if useLED == 'Cue':
                # Code for differential cue lights
                #if spoutN == taste_positions[0]:
                #    led.red_off()
                #else:
                #    led.green_off()
                led.green_off() #Turn off the cue light
                led.white_on() # turn on house white led light
                GPIO.output(cueIntanIn,GPIO.LOW) #Turn off the cue Intan
            if useLED == 'True': GPIO.output(np_led,GPIO.LOW) # turn off nose poke LED
            time.sleep(0.001)
            GPIO.output(cueIntanIn,GPIO.LOW) #Turn off the cue Intan
            GPIO.output(spoutsIntanIn[taste_idx],GPIO.LOW) #Turn off the correct spout Intan
            
            # Turn off nosepoke detection
            NP_process.terminate()
            GPIO.output(beamIntanIn,GPIO.LOW) #Turn off the beam Intan
            
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
            trialLine = f"{trialN+1:>4},{spoutN:>4},{Concentrations[taste_idx]:>{padConc}},{Solutions[taste_idx]:>{padStim}},{IPITimes[trialN]:>7},{timeTemp:>7},{NLicks:>7},{latency:>{padLat}},{0:>7},{useLaser[trialN]:>7}\n"  # Left-aligned, padded with spaces
            with open(outFile, 'r') as outputFile:
                outputData = outputFile.readlines()
                outputData.insert((skipLines+trialN),trialLine)
            with open(outFile, 'w') as outputFile:
                outputFile.writelines(outputData)
                outLicks = f',{",".join(map(str, trialLicks[1:]))}' if len(trialLicks) > 0 else ''
                outputFile.write(f'{trialN + 1}{outLicks}\n')
                
            # Push trial information to the GUI
            rig.trialQueue.put([trialN,NLicks,latency])
    
            # print out number of licks being made on this trial
            print('{} licks on Trial {}'.format(NLicks, trialN))
            print('\n=====  Inter-Trial Interval =====\n')
        
        #Note a clean run
        rig.cleanRun.set()
        
    #%% Ending the session
    finally:
        if not rig.cleanRun.is_set():
            print("Session interrupted")
            
        # turn off LEDs and Intan outs
        led.white_off()
        led.red_off()
        led.green_off()
        GPIO.output(np_led,GPIO.LOW) #Turn off the beam break indicator
        GPIO.output(cueIntanIn,GPIO.LOW) #Turn off the cue Intan
        GPIO.output(spoutsIntanIn,GPIO.LOW) #Turn off the spout Intan(s)
        GPIO.output(beamIntanIn,GPIO.LOW) #Turn off the beam Intan
        GPIO.output(laserPin,GPIO.LOW) #Turn off the beam Intan
    
        # Return spout to home. This won't work if session is aborted while moving motor
        # create Motor instance
        motora = Motor(stepPin, directionPin, enablePin, ms1Pin, ms2Pin, ms3Pin)
        motora.init()
        revolution = motora.setStepSize(stepMode)
        # Turn the motor
        turn_dir, n_shift = rotate_dir(cur_pos, 1, tot_pos = tot_pos)
        if turn_dir == -1: # turn clockwise
            motora.turn(n_shift * (revolution/tot_pos), Motor.CLOCKWISE)
        else:
            motora.turn(n_shift * (revolution/tot_pos), Motor.ANTICLOCKWISE)
        # Shut down motor
        motora.reset()
    
        #Shut down camera
        if useCamera == 'True': camera.cleanup()
        
        #print(licks)
        for spout in spout_locs:
            num_licks_trial = [len(i) if i is not None else None for i in licks[spout]]
            print(spout, num_licks_trial)
            
            if licks[spout]:  # Check if list is non-empty
                tot_licks = np.concatenate(licks[spout])
                print("Total number of licks on {}: {}".format(spout, len(tot_licks)))
            else:
                print("No licks recorded for {}.".format(spout))                
                
        rig.AbortEvent.set() #Tell the GUI to close

#%%
sessionThread = threading.Thread(target=runSession,daemon=False)
sessionThread.start()
rig.TrialGui(paramsFile, outputFile, subjID)
