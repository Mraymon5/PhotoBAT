# This code records number of licks via IR beambreak detection
# Execute the code with python licking_test.py [subjID] [experimental duration]

#Import the necessary modules
import os
import time
import numpy as np
import pickle
import easygui
import json
import sys
import argparse
import random
from datetime import datetime
import threading
import queue

#Currently unused modules
if False:
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
    import board
    from rgbled_class import RGBLed
    print("Using uldaq for Linux")
elif sys.platform.startswith('win'):
#    from mcculw import ul
#    from mcculw.enums import DigitalPortType, DigitalIODirection
#    from mcculw.ul import ULError
    # Additional imports or initialization specific to mcculw if needed
    print("Using mcculw for Windows")
else:
    raise OSError("Unsupported platform")

#%% Local py functions
import CameraControl
from MakeParams import readParameters
import MCC_Setup; mcc = MCC_Setup.MCCInterface(); dav = MCC_Setup.DavRun()
import rig_funcs as rig

#%% Helper Functions
# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a givin position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Function to allow flexible inputs for True in user-supplied strings
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

date = time.strftime("%Y%m%d")
subjID = args.subjID
paramsFile = args.paramsFile
useLED = args.LED
useCamera = args.Camera
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
    
    tastes = [stimN for stimN in Solutions if len(stimN) > 0]
    taste_positions = [int(stimN+1) for stimN in range(len(Solutions)) if len(Solutions[stimN]) > 0]
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
    taste_positions = [int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
    
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
try:
    padStim = max([len(str(stimN)) for stimN in tastes]) + 1
except:
    padStim = 1
try:
    padConc = max([len(str(stimN)) for stimN in concs]) + 1
except:
    padConc = 1
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
# Set up MCC ports
try:
    # Set Port A as output for motor relays
    mcc.d_config_port(board_num = dav.boardNum, port = 0, direction = 'output')

    # Set Port B as input for 5V TTL sensors
    mcc.d_config_port(board_num = dav.boardNum, port = 1, direction = 'input')

    # Set Port C as output for LED indicators or other outputs
    mcc.d_config_port(board_num = dav.boardNum, port = 2, direction = 'output')
    mcc.d_config_port(board_num = dav.boardNum, port = 3, direction = 'output')

    print("Ports configured successfully.")

except mcc.ul.ULError as e:
    print(f"Error configuring ports: {e}")

# Initialize Table and Shutter
dav.moveShutter(Init=True)
dav.moveTable(Init=True)

# setup motor [40 pin header for newer Raspberry Pi's]
# setup RGB LEDs, not implemented
#if sys.platform.startswith('linux'):
#    red_pin, green_pin, blue_pin = board.D13, board.D19, board.D26
#    led = RGBLed(red_pin, green_pin, blue_pin)

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
# GUI setup
#Function to start session
shutterThread = None #Add this so that the thread can be resolved before shutterThread is instanced
rig.AbortEvent.set() #Set the abort event, which will be turned off to start the session
#guiThread = threading.Thread(target=rig.TrialGui, kwargs={'paramsFile':paramsFile, 'outputFile':outputFile, 'subjID':subjID}, daemon=True)
#guiThread.start()


#TODO investigate putting all this code in a thread and running the gui in main thread
def runSession():
    curPos = 1 # Initial position of table should be 1

    #Final Check
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
    
    # Turn on white LED to set up the start of experiment, not implemented
    #if useLED == 'True' or useLED == 'Cue': led.white_on()
    
    #%% Open the trial loop
    cleanRun = False
    try:
        for trialN, spoutN in enumerate(TubeSeq): #trialN was index, spoutN was trial #spoutN = 2; trialN = 1
            #Check max session time
            if time.time() - exp_init_time >= SessionTimeLimit: #If session duration expires, exit the for loop
                break
    
            # rotate motor to move spout outside licking hole
            dest_pos = TubeSeq[trialN]
            dav.moveTable(movePos=dest_pos-curPos)
            curPos = dest_pos
    
            #Run Trial IPI
            while (time.time() - startIPI) < IPITimes[trialN]:
                #Check for an abort signal from GUI
                if rig.AbortEvent.is_set():
                    raise KeyboardInterrupt()
                time.sleep(0.001)
    
            # Open Shutter, in a thread so that other operations can proceed
            shutterThread = threading.Thread(target=dav.moveShutter, kwargs={'Open':True})
            shutterThread.start()
        
            # turn on nose poke LED cue and send signal to intan
            if useLED == 'Cue':
                pass #Not implemented yet
            mcc.setBit(portType=trialTTL[0], channel=trialTTL[1], value=1)
            
            # on-screen reminder
            print("\n")
            print("Trial {}_spout{} in Progress. Max lick time = {}, Max lick count = {}".format(trialN, spoutN, LickTime[trialN], LickCount[trialN]))
            
            # empty list to save licks for each trial
            this_spout = 'Position {}'.format(spoutN)
            licks[this_spout].append([])
            filteredLicks = 0
            # get the number of current trial for that particular spout
            this_trial_num = len(licks[this_spout]) - 1 
    
            # detecting the current status of touch sensor
            last_poke = mcc.getBit(portType=dav.lickSensor[0], channel=dav.lickSensor[1])
            print("Lick sensor is clear") if not last_poke else print ("Lick sensor is blocked")
            while last_poke: # stay here if lick sensor is touched
                last_poke = mcc.getBit(portType=dav.lickSensor[0], channel=dav.lickSensor[1]) # make sure nose-poke is not blocked when starting
            
            #Save Trial Start Time
            trial_start_time = time.time()
            trial_init_time = trial_start_time
            last_lick = trial_start_time
            trialTimeLimit = MaxWaitTime[trialN] #Initially set the trial time limit to the max wait for this trial
            print('Start detecting licks/nosepokes')
            
            #Update Lick Count and trial event in GUI
            rig.lickQueue.put(len(licks[this_spout][this_trial_num])) #push lick count to gui
            rig.timerQueue.put(trial_start_time+trialTimeLimit) #push the timeout time to GUI
            rig.TrialEvent.set() #Let gui know a trial has started
    
            #Start the camera
            if useCamera == 'True': camera.startBuffer()
    
            while ((time.time() - trial_init_time < trialTimeLimit) if trialTimeLimit is not None else True) and \
                (time.time() - exp_init_time < SessionTimeLimit) and \
                (len(licks[this_spout][this_trial_num]) < LickCount[trialN] if LickCount[trialN] is not None else True):
                
                # Check for an abort signal from the GUI
                if rig.AbortEvent.is_set():
                    raise KeyboardInterrupt()
                    
                # Check the state of the lick sensor
                current_poke = mcc.getBit(portType=dav.lickSensor[0], channel=dav.lickSensor[1])
    
                # First check if transitioned from not poke to poke.
                if current_poke == 1 and last_poke == 0: # 0 indicates poking
                    new_lick = time.time() #save the time of the new lick onset. was beam_break
                    if (useLED == 'True'): mcc.setBit(portType=lickLED[0], channel=lickLED[1], value=1)
                    #mcc.setBit(portType=lickTTL[0], channel=lickTTL[1], value=1)
                    
                # Next check if transitioned from poke to not poke.
                if current_poke == 0 and last_poke == 1:
                    off_lick = time.time() #save the time the lick sensor stops. was beam_unbroken
                    if (useLED == 'True'): mcc.setBit(portType=lickLED[0], channel=lickLED[1], value=0)
                    #mcc.setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)
    
                    if (off_lick - new_lick > 0.02) and (off_lick - new_lick < 0.12): # to avoid noise (from motor)- induced licks TODO: See if these limits can be tuned tighter. Also, add in an output of the number of filtered licks
                        licks[this_spout][this_trial_num].append(round((new_lick-last_lick)*1000))
                        rig.lickQueue.put(len(licks[this_spout][this_trial_num])) #Send new lick to GUI
                        if len(licks[this_spout][this_trial_num]) == 1:
                            trial_init_time = new_lick #if lick happens, reset the trial_init time
                            trialTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else None #If a lick happens, reset the trial time limit to maximal lick time
                            if trialTimeLimit is not None:
                                rig.timerQueue.put(trial_init_time+trialTimeLimit) #push the timeout time to GUI
                            else:
                                rig.timerQueue.put(trial_init_time) #push the timeout time to GUI
                            camTimeLimit = LickTime[trialN] if LickTime[trialN] is not None else 20 #If a lick happens, reset the trial time limit to maximal lick time
                            if useCamera == 'True': camera.saveBufferAndCapture(duration=min(20,camTimeLimit), title=f'{subjID}_trial{trialN}', outputFolder=dat_folder, start_time = trial_init_time) #Camera recording period capped to 20sec
                        last_lick = new_lick
                        print('Lick_{}'.format(len(licks[this_spout][-1])))
                    else:
                        filteredLicks += 1
                        print(f'Rejected lick: {filteredLicks}')
        
                # Update last state and wait a short period before repeating.
                last_poke = current_poke
                #time.sleep(0.001)
                
            #Start the clock for IPI
            startIPI = time.time()
    
            # Close Shutter
            dav.moveShutter(Open=False)
            
            # Update LEDs and Intan outs
            if useLED == 'Cue':
                pass
            
            if useLED == 'True': mcc.setBit(portType=lickLED[0], channel=lickLED[1], value=0)
            time.sleep(0.001)
            mcc.setBit(portType=trialTTL[0], channel=trialTTL[1], value=0)
            
            # Turn off nosepoke detection
            mcc.setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)
            
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
            trialLine = f"{trialN+1:>4},{spoutN:>4},{Concentrations[spoutN-1]:>{padConc}},{Solutions[spoutN-1]:>{padStim}},{IPITimes[trialN]:>7},{timeTemp:>7},{NLicks:>7},{latency:>{padLat}},{0:>7}\n"  # Left-aligned, padded with spaces
            with open(outFile, 'r') as outputFile:
                outputData = outputFile.readlines()
                outputData.insert((skipLines+trialN),trialLine)
            with open(outFile, 'w') as outputFile:
                outputFile.writelines(outputData)
                outLicks = f',{",".join(map(str, trialLicks[1:]))}' if len(trialLicks) > 0 else ''
                outputFile.write(f'{trialN + 1}{outLicks}\n')
    
            # Push trial information to the GUI
            if trialN+1<NTrials:
                rig.timerQueue.put(startIPI+IPITimes[trialN+1]) #push the timeout time to GUI
            rig.trialQueue.put([trialN,NLicks,latency])
            rig.TrialEvent.clear() #Let gui know a trial has ended
    
            # print out number of licks being made on this trial
            print('{} licks on Trial {}'.format(NLicks, trialN))
            print('\n=====  Inter-Trial Interval =====\n')
        
        #Note a clean run
        cleanRun = True
        
    #%% Ending the session
    finally:
        if not cleanRun:
            print("Session interrupted")
    
        if shutterThread and shutterThread.is_alive():
            shutterThread.join()
    
        # turn off LEDs and Intan outs
        mcc.setBit(portType=lickLED[0], channel=lickLED[1], value=0)
        mcc.setBit(portType=trialTTL[0], channel=trialTTL[1], value=0)
        mcc.setBit(portType=lickTTL[0], channel=lickTTL[1], value=0)
        
        # Return spout to home, close shutter
        dav.moveTable(Init=True)
        dav.moveShutter(Init=True)   
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

#%%
sessionThread = threading.Thread(target=runSession,daemon=True)
sessionThread.start()
rig.TrialGui(paramsFile, outputFile, subjID)
