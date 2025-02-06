import os
import sys
import time
import easygui
import atexit
import warnings
import tkintertable
#import tkinter as tk
from mttkinter import mtTkinter as tk
import threading
import queue
import pandas as pd

from MakeParams import readParameters

try:
    import RPi.GPIO as GPIO
    from bipolar_class import Motor
except:
    print('Rig: Could not import Pi-Specific Modules')

#%% Read Params function
def read_params():
    script_dir = os.path.dirname(os.path.abspath(__file__)) #script_dir = "/home/ramartin/PhotoBAT/"
    params_path = os.path.join(script_dir, 'BAT_params.txt')
    
    with open(params_path, 'r') as params:
        paramsData = params.readlines()
    paramsData = [line.rstrip('\n') for line in paramsData]
    paramsData = [line.split('#')[0] for line in paramsData]
    paramsData = [line.split('=') for line in paramsData]
    
    # Table Control Settings
    tableTotalSteps = int([line[1] for line in paramsData if 'tableTotalSteps' in line[0]][0])
    tableTotalPositions = int([line[1] for line in paramsData if 'tableTotalPositions' in line[0]][0])
    tableStepMode = str([line[1] for line in paramsData if 'tableStepMode' in line[0]][0]).strip()
    tableInitSteps = [line[1].split(',') for line in paramsData if 'tableInitSteps' in line[0]][0]
    tableInitSteps = [float(trialN) for trialN in tableInitSteps]
    tableInitSteps = {'FULL': tableInitSteps[0], 'HALF': tableInitSteps[1], 'QUARTER': tableInitSteps[2], 'EIGHTH': tableInitSteps[3], 'SIXTEENTH':tableInitSteps[0]}
    tableSpeed = [line[1].split(',') for line in paramsData if 'tableSpeed' in line[0]][0]
    tableSpeed = [float(trialN) for trialN in tableSpeed]
    tableSpeed = {'FULL': tableSpeed[0], 'HALF': tableSpeed[1], 'QUARTER': tableSpeed[2], 'EIGHTH': tableSpeed[3], 'SIXTEENTH':tableSpeed[0]}

    # Pin Assignments
    stepPin = int([line[1] for line in paramsData if 'stepPin' in line[0]][0])
    directionPin = int([line[1] for line in paramsData if 'directionPin' in line[0]][0])
    enablePin = int([line[1] for line in paramsData if 'enablePin' in line[0]][0])
    msPins = [line[1].split(',') for line in paramsData if 'msPins' in line[0]][0]
    msPins = [int(trialN) for trialN in msPins]
    hallPin = int([line[1] for line in paramsData if 'hallPin' in line[0]][0])
    lickBeamPin = int([line[1] for line in paramsData if 'lickBeamPin' in line[0]][0])
    
    # Accessory Pins
    laserPin = int([line[1] for line in paramsData if 'laserPin' in line[0]][0])
    lickLEDPin = int([line[1] for line in paramsData if 'lickLEDPin' in line[0]][0])
    cueLEDPins = [line[1].split(',') for line in paramsData if 'cueLEDPins' in line[0]][0]
    cueLEDPins = [int(trialN) for trialN in cueLEDPins]
    intanBeamPin = int([line[1] for line in paramsData if 'intanBeamPin' in line[0]][0])
    intanTrialPin = int([line[1] for line in paramsData if 'intanTrialPin' in line[0]][0])
    intanSpoutPins = [line[1].split(',') for line in paramsData if 'intanSpoutPins' in line[0]][0]
    intanSpoutPins = [int(trialN) for trialN in intanSpoutPins]
    
    # Lick Detection Mode
    lickMode = str([line[1] for line in paramsData if 'lickMode' in line[0]][0]).strip()
    
    rigParams = {'tableTotalSteps':tableTotalSteps, 'tableTotalPositions':tableTotalPositions, 'tableStepMode':tableStepMode, 'tableInitSteps':tableInitSteps, 'tableSpeed':tableSpeed,
                 'stepPin':stepPin, 'directionPin':directionPin, 'enablePin':enablePin, 'msPins':msPins, 'hallPin':hallPin, 'lickBeamPin':lickBeamPin,
                 'laserPin':laserPin, 'lickLEDPin':lickLEDPin, 'cueLEDPins':cueLEDPins, 'intanBeamPin':intanBeamPin, 'intanTrialPin':intanTrialPin, 'intanSpoutPins':intanSpoutPins,
                 'lickMode':lickMode}
    
    return rigParams
#%%Motor control functions
# 40 pin header for newer Raspberry Pi's  (BPhysicals location, BCM locations)
#board_nums = [38,40,22,12,10,8]
#BCM_nums = [24,23,20,18,15,14] #this is what's being used
#step, direction, enable, ms1, ms2, ms3 = BCM_nums
rigParams = read_params()

stepPin = rigParams['stepPin']
directionPin = rigParams['directionPin']
enablePin = rigParams['enablePin']    # Not required - leave unconnected
ms1Pin = rigParams['msPins'][0]
ms2Pin = rigParams['msPins'][1]
ms3Pin = rigParams['msPins'][2]

hallPin = rigParams['hallPin']

stepMode = rigParams['tableStepMode']
posTotal = rigParams['tableTotalPositions']

initSteps = int(rigParams['tableInitSteps'][stepMode])

def detect_magnet(he_inport = hallPin, wait = 0.5):
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
    
def align_zero(step=stepPin, direction=directionPin,enable=enablePin,ms1=ms1Pin,ms2=ms2Pin,ms3=ms3Pin,
               rotate='clockwise', he_inport = hallPin, adjust_steps=initSteps, stepMode = stepMode): 
    motora = Motor(step,direction,enable,ms1,ms2,ms3)
    motora.init()
    revolution = motora.setStepSize(stepMode)
    print(f'Total steps in this mode: {revolution}')
    inport = he_inport
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(inport, GPIO.IN)
    n = 0 # iterator to stop the motor if it passes a full rotation
    #If the mag sensor is aligned, move away from it
    while not GPIO.input(inport) and n < revolution:
        if rotate == 'clockwise':
            motora.turn(1, Motor.CLOCKWISE)
        elif rotate == 'anticlockwise':
            motora.turn(1, Motor.ANTICLOCKWISE)
        n += 1
        time.sleep(0.0007)
    if  n >= revolution:
        print("Hall sensor read as 'on' through a full rotation, check hardware")
        motora.reset()
        return
        
    n = 0 # iterator to stop the motor if it passes a full rotation
    #If the mag sensor is not aligned, move to it
    while GPIO.input(inport) and n < revolution:
        if rotate == 'clockwise':
            motora.turn(1, Motor.ANTICLOCKWISE)
        elif rotate == 'anticlockwise':
            motora.turn(1, Motor.CLOCKWISE)
        n += 1
        time.sleep(0.0007)
    if  n >= revolution:
        motora.reset()
        print("Hall sensor read as 'off' through a full rotation, check hardware")
        return        
    
    if rotate == 'clockwise':
        motora.turn(adjust_steps, Motor.CLOCKWISE)
    elif rotate == 'anticlockwise':
        motora.turn(adjust_steps, Motor.ANTICLOCKWISE)

    print('Aligned to initial position')

def fine_align(step=stepPin, direction=directionPin,enable=enablePin,ms1=ms1Pin,ms2=ms2Pin,ms3=ms3Pin,stay=False):
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    # rotate motor to move spout outside licking hole
    steps360 = motora.setStepSize(stepMode)
    stepsPerPos = steps360/posTotal
    motora.turn(steps=stepsPerPos, direction=motora.ANTICLOCKWISE)
    
    while True:
        rotate_degrees = easygui.multenterbox(title = 'Fine Adjustment of initial spout position', 
                              msg = '# of Rotating Degrees (integer number)',
                              fields = ['Number of rotating degrees (>0:colockwise; <0:counter-clockwise'],
                              values = [1])
        rotate_deg = int([int(rotate_degrees[0]) if rotate_degrees is not None  else 0]*(steps360/360))
        #print(rotate_deg)
        if rotate_deg != 0:
            if rotate_deg > 0:
                motora.turn(rotate_deg, motora.CLOCKWISE)
            elif rotate_deg < 0:
                motora.turn(rotate_deg, motora.ANTICLOCKWISE)
        else:
            break
            
    if not stay:
        motora.turn(steps=stepsPerPos, direction=motora.CLOCKWISE)
    motora.reset()
    
#A function to configure the IO Pins
def configureIOPins():
    rigParams = read_params()
    if not "RPi.GPIO" in sys.modules:
        warnings.warn("GPIO not loaded, IO not configured")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    pinList = {'stepPin':GPIO.OUT,
            'directionPin':GPIO.OUT,
            'enablePin':GPIO.OUT,
            'msPins':GPIO.OUT,
            'hallPin':GPIO.IN,
            'lickBeamPin':GPIO.IN,
            'laserPin':GPIO.OUT,
            'lickLEDPin':GPIO.OUT,
            'cueLEDPins':GPIO.OUT,
            'intanBeamPin':GPIO.OUT,
            'intanTrialPin':GPIO.OUT,
            'intanSpoutPins':GPIO.OUT,
        }
    for pinN, pinMode in pinList.items():
        pinData = rigParams[pinN]
        if pinN == 'intanSpoutPins':
            NSpouts = int(rigParams['tableTotalPositions'] / 2)
            pinData = pinData[0:NSpouts]
        # Ensure pinData is iterable
        if isinstance(pinData, (list, tuple)):  
            for subPinN in pinData:
                try:
                    if subPinN > 0 :GPIO.setup(subPinN, pinMode)
                except Exception as e:
                    print(f"Could not configure {pinN}[{subPinN}]: {e}")
        else:
            try:
                if pinN == 'lickBeamPin':
                    if pinData > 0 :GPIO.setup(pinData, pinMode, pull_up_down = GPIO.PUD_UP)
                else:
                    if pinData > 0 :GPIO.setup(pinData, pinMode)
            except Exception as e:
                print(f"Could not configure {pinN}[{pinData}]: {e}")

#Function to Power on Laser for some duration
def fireLaser(laserPin,duration):
    laserOnTime = time.time()
    GPIO.output(laserPin,GPIO.HIGH)
    while (time.time()-laserOnTime < duration):
        time.sleep(1e-3)
    GPIO.output(laserPin,GPIO.LOW)

#%% Functions for running the Session Gui    
AbortEvent = threading.Event()
TrialEvent = threading.Event()
lickQueue = queue.Queue()
timerQueue = queue.Queue()
trialQueue = queue.Queue()

Debug = False
if Debug: #Debugging
    subjID = "Test"
    paramsFile = '/home/ramartin/PhotoBAT/params/params.txt'
    outputFile = '/home/ramartin/PhotoBAT/data/20250204/20250204None.txt'
    

def TrialGui(paramsFile, outputFile, subjID):
    #Make tables that don't allow editing
    class passiveTableCanvas(tkintertable.TableCanvas):
        def __init__(self, master=None, *args, **kw):
            super().__init__(master, *args, **kw)
            self.columnactions = {}

        def drawCellEntry(self, row, col):
            pass

    def on_close():
        abortSession = easygui.ccbox(msg="Terminate Session?",title="Terminate Check")
        if abortSession:
            AbortEvent.set()
            sessionGUI.destroy()  # Destroy the Toplevel window
            if not isChild: trialRoot.destroy()    # Destroy the hidden root window
        else:
            pass

    def runSession():
        global paramsData, TrialEventWasSet
        #Wait to run session
        AbortEvent.clear()        
        
        #Flip to running session
        runButton.destroy()  # Destroy the run button, and replace it with an Abort button
        abortButton = tk.Button(controlFrame,text="Abort",command=on_close,width=9)
        abortButton.grid(row=0, column=0, padx=10, pady=10)
        tableFrame.configure(text = "Session Data")
        paramsData.insert(loc=4, column= 'Licks',value =[None]*len(paramsData))
        paramsData.insert(loc=5, column= 'Latency',value =[None]*len(paramsData))
        paramTable.model.importDict(paramsData.to_dict(orient="index"))  # Update the table model
        paramTable.model.columnNames = list(paramsData.columns)  # Force correct column order
        paramTable.redraw()  # Refresh table display
        table_model.columnwidths = {col_name: 50 for col_name in table_model.columnNames}  # Adjust 50 to your preference

        #Start Updating the information display
        TrialEventWasSet = False
        updateInfo()

        
    def updateTrial():
        global paramsData
        try:
            trialData = trialQueue.get_nowait()  # Non-blocking queue retrieval
            trialN, NLicks, latency = trialData  # Unpack the list
            paramsData.at[trialN, 'Licks'] = NLicks
            paramsData.at[trialN, 'Latency'] = latency
            paramTable.model.importDict(paramsData.to_dict(orient="index"))
            paramTable.redraw()
        except queue.Empty:
            pass  # No new trial data yet
    
                
    def updateInfo():
        global timerIs, TrialEventWasSet
        #update data in the table display
        try: 
            lickIs = lickQueue.get_nowait() #Read lick data off the queue
            if lickIs == 1:
                eventDispEnt.set("Licking")
            lickDispEnt.set(lickIs) #Write lick data to GUI
        except queue.Empty:
            pass
        try:
            timerIs = timerQueue.get_nowait() #Read timer data off the queue. timerQueue needs to be formatted as the endpoint time of the current timer
        except queue.Empty:
            pass
        timerDispEnt.set(f'{round(timerIs - time.time(),2):.3f}') #Write timer data to GUI
        
        if TrialEvent.is_set() and not TrialEventWasSet:
            eventDispEnt.set("Waiting for Lick")
        if TrialEventWasSet and not TrialEvent.is_set():
            eventDispEnt.set("ITI")
            updateTrial() 
        TrialEventWasSet = TrialEvent.is_set()
        sessionGUI.after(10,updateInfo)
        
    
    #Start GUI Code
    global timerIs, paramsData
    timerIs = time.time()
    if not tk._default_root:
        trialRoot = tk.Tk()  # Create a root window if none exists
        trialRoot.withdraw()  # Hide the root window since we only want Toplevel
        isChild = False
    else:
        isChild = True
        trialRoot = tk._default_root  # Use the existing root
    version, paramsData = readParameters(paramsFile)
    sessionGUI = tk.Toplevel(trialRoot)
    sessionGUI.title(f"BAT Session: {subjID}")
    sessionGUI.protocol("WM_DELETE_WINDOW", on_close)
    tableFrame = tk.LabelFrame(sessionGUI, text = "Session Parameters")
    tableFrame.grid(row=0, column=0, padx=10, pady=10, rowspan=3, sticky='nwse')
    table_model = tkintertable.TableModel()
    table_model.importDict(paramsData.to_dict(orient="index"))
    table_model.columnwidths = {col_name: 50 for col_name in table_model.columnNames}  # Adjust 50 to your preference
    # Create and display the table
    paramTable = passiveTableCanvas(tableFrame, model=table_model)
    paramTable.show()

    #Frame for controls
    controlFrame = tk.LabelFrame(sessionGUI, text = "Session Controls")
    controlFrame.grid(row=0, column=1, padx=10, pady=10, sticky='nw', rowspan=1)
    #Run Session Button
    runButton = tk.Button(controlFrame, text="Run Session", command=runSession, width=9)
    runButton.grid(row=0, column=0, padx=10, pady=10)
    
    #Frame for Display
    infoFrame = tk.LabelFrame(sessionGUI, text = "Session Information")
    infoFrame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew', rowspan=2)
    infoRow = 0
    infoPad = 5
    lickLabel = tk.Label(infoFrame, text= "Lick Count:")
    lickLabel.grid(row=infoRow, column=0, padx=infoPad, pady=10, sticky='ne', rowspan=1)
    lickDispEnt = tk.IntVar(); lickDispEnt.set(0)
    lickDispBox = tk.Label(infoFrame, textvariable=lickDispEnt, background='white', borderwidth=1, relief="solid", width=7, anchor='e')
    lickDispBox.grid(row=infoRow, column=1, padx=infoPad, pady=10, sticky='nw', rowspan=1)
    infoRow +=1
    eventLabel = tk.Label(infoFrame, text= "Current Event:")
    eventLabel.grid(row=infoRow, column=0, padx=infoPad, pady=10, sticky='ne', rowspan=1)
    eventDispEnt = tk.StringVar(); eventDispEnt.set("Waiting to Start")
    eventDispBox = tk.Label(infoFrame, textvariable=eventDispEnt, width=12, anchor='w') # background='white', borderwidth=1, relief="solid",
    eventDispBox.grid(row=infoRow, column=1, padx=infoPad, pady=10, sticky='nw', rowspan=1)
    infoRow +=1
    timerLabel = tk.Label(infoFrame, text= "Timer:")
    timerLabel.grid(row=infoRow, column=0, padx=infoPad, pady=10, sticky='ne', rowspan=1)
    timerDispEnt = tk.StringVar(); timerDispEnt.set("0")
    timerDispBox = tk.Label(infoFrame, textvariable=timerDispEnt, background='white', borderwidth=1, relief="solid", width=7, anchor='e')
    timerDispBox.grid(row=infoRow, column=1, padx=infoPad, pady=10, sticky='nw', rowspan=1)
    
    sessionGUI.mainloop()
