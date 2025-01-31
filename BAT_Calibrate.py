#%% Import Modules
import os
import time
import tkinter as tk
from tkinter import ttk
import sys
import warnings

#%% Import Local Functions
import rig_funcs
try:
    import bipolar_class as bipol
    import RPi.GPIO as GPIO
except:
    print("Could not import Pi-Specific Modules")

base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
rigParamsFile = os.path.join(base_path, 'BAT_params.txt')
rigParams = rig_funcs.read_params() #read parameters from file

def update_line_in_file(file_path, keyword, new_value):
    # Read all lines from the file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Find and update the target line
    updated = False
    for i, line in enumerate(lines):
        if keyword in line:
            lines[i] = f"{new_value}\n"  # Update the line with the new value
            updated = True
            break  # Stop after finding the first match

    # Write the updated lines back to the file
    if updated:
        with open(file_path, 'w') as file:
            file.writelines(lines)
        print(f"Updated `{keyword}` in {file_path}")
    else:
        print(f"Keyword `{keyword}` not found in {file_path}.")
        
#%% Helper Functions
# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a given position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Function to allow flexible inputs for True in user-supplied strings
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

#Allow tooltips hovering over widgets
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Removes window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, borderwidth=1, relief="solid", padx=5, pady=3, justify='l')# bg="grey", relief="solid",
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# Calibration Gui functions
# Function to update sensor values
def update_sensor_display(sensor_labels):
    readTime = time.time()
    lSens = f"Lick Sensor: {GPIO.input(rigParams['lickBeamPin'])}"
    tMagSens = f"Table Mag: {GPIO.input(rigParams['hallPin'])}"
    readDelay = f"Read Delay: {round(time.time() - readTime, 4):.3f}"
    labCurPos = f"Current Position: {TablePosition}"
    values = [lSens, tMagSens, readDelay, labCurPos]
    
    # Update each label with the corresponding sensor value
    for label, value in zip(sensor_labels.values(), values):
        label.config(text=value)
    
    # Schedule the function to run again after 500ms
    calibrateGUI.after(10, update_sensor_display, sensor_labels)

def updateParameters():
    global rigParams
    #Table Settings
    tableTotalSteps = int(tTotEnt.get()) #The total number of whole steps possible by the motor
    rigParams[tableTotalSteps] = tableTotalSteps
    outtableTotalSteps = ["tableTotalSteps", f"tableTotalSteps = {tableTotalSteps} #The total number of full steps possible by the motor"]

    tableTotalPositions = int(tPosEnt.get()) #The total number of positions, including walls, on the table
    rigParams[tableTotalPositions] = tableTotalPositions
    outtableTotalPositions = ["tableTotalPositions", f"tableTotalPositions = {tableTotalPositions} #The total number of positions, including walls, on the table"]

    rigParams['tableSpeed'][rigParams['tableStepMode']] = float(tSpdEnt.get()) #The total number of positions, including walls, on the table
    tableSpeed = rigParams['tableSpeed']
    speedvalues = [float(val) for val in tableSpeed.values()]
    speedvalues = ','.join(map(str, speedvalues))
    outtableSpeed = ["tableSpeed", f"tableSpeed = {speedvalues} #Delay between steps when driving table"]

    #Pin Assignments
    stepPin = int(pStepEnt.get())
    directionPin = int(pDirEnt.get())
    enablePin = int(pEnbEnt.get())
    ms1Pin = int(pMS1Ent.get())
    ms2Pin = int(pMS2Ent.get())
    ms3Pin = int(pMS3Ent.get())
    msPins = [ms1Pin,ms2Pin,ms3Pin]
    hallPin = int(pHallEnt.get())
    lickBeamPin = int(pBeamEnt.get()) #Pin for the beam-break input
    laserPin = int(pLazEnt.get()) #Laser TTL output
    lickLEDPin = int(pBeamLEDEnt.get()) #Pin for the beam-break indicator
    cueBluePin = int(pBlueEnt.get()) #Blue, Green, and Red channel pins for the chamber cue LED
    cueGreenPin = int(pGreenEnt.get()) #Blue, Green, and Red channel pins for the chamber cue LED
    cueRedPin = int(pRedEnt.get()) #Blue, Green, and Red channel pins for the chamber cue LED
    cueLEDPins = [cueBluePin,cueGreenPin,cueRedPin]
    intanBeamPin = int(pIntBeamEnt.get()) #Pin for beam indication output to intan
    intanTrialPin = int(pIntTrialEnt.get()) #Pin for trial indication output to intan
    intanSpoutPins = rigParams['intanSpoutPins']
    intanSpoutPins[0:len(spoutPinList)] = [int(widget.get()) for widget in spoutPinList.values()]
    
    outstepPin = ["stepPin", f"stepPin = {stepPin} #Pin assigned to motor control board to step the motor"]
    outdirectionPin = ["directionPin", f"directionPin = {directionPin} #Pin assigned to motor control board to control direction"]
    outenablePin = ["enablePin", f"enablePin = {enablePin} #Pin assigned to motor control board to enable/disable power"]
    outmsPins = ["msPins", f"msPins = {','.join(map(str, msPins))} #MS1,MS2,MS3 Motor communication logic pins"]
    outhallPin = ["hallPin", f"hallPin = {hallPin} #Hall Effect positional sensor"]
    outlickBeamPin = ["lickBeamPin", f"lickBeamPin = {lickBeamPin} #Pin for the beam-break input"]
    outlaserPin = ["laserPin", f"laserPin = {laserPin} #Laser TTL output"]
    outlickLEDPin = ["lickLEDPin", f"lickLEDPin = {lickLEDPin} #Pin for the beam-break indicator"]
    outcueLEDPins = ["cueLEDPins", f"cueLEDPins = {','.join(map(str, cueLEDPins))} #Blue, Green, and Red channel pins for the chamber cue LED"]
    outintanBeamPin = ["intanBeamPin", f"intanBeamPin = {intanBeamPin} #Pin for beam indication output to intan"]
    outintanTrialPin = ["intanTrialPin", f"intanTrialPin = {intanTrialPin} #Pin for trial indication output to intan"]
    outintanSpoutPins = ["intanSpoutPins", f"intanSpoutPins = {','.join(map(str, intanSpoutPins))} #spouts 2,4,6,8: pins for spout indication output to intan"]

    outputData = [outtableTotalSteps,outtableTotalPositions,outtableSpeed,
                  outstepPin, outdirectionPin, outenablePin, outmsPins, outhallPin, outlickBeamPin,
                  outlaserPin, outlickLEDPin, outcueLEDPins, outintanBeamPin, outintanTrialPin, outintanSpoutPins]
    #Write Updated Values
    for outN in outputData:
        update_line_in_file(file_path = rigParamsFile, keyword=outN[0], new_value=outN[1])
        rigParams[outN[0]] = eval(outN[0])
    initIntanSpouts(NPositions=rigParams['tableTotalPositions'])
    print(f'Params saved as {rigParamsFile}')
    #Reconfigure Pins
    rig_funcs.configureIOPins()
    
def updateStepMode(mode):
    global rigParams, stepsPerTurn, tSpdBox,tInitBox
    tableStepMode = mode #The mode to operate the stepper motor in
    rigParams['tableStepMode'] = tableStepMode
    outtableStepMode = ["tableStepMode =", f"tableStepMode = {tableStepMode} #The step mode for controlling the motor"]
    update_line_in_file(file_path = rigParamsFile, keyword=outtableStepMode[0], new_value=outtableStepMode[1])
    tSpdBox.delete(0,tk.END)
    tSpdBox.insert(0,rigParams['tableSpeed'][rigParams['tableStepMode']]) 
    tInitBox.delete(0,tk.END)
    tInitBox.insert(0,rigParams['tableInitSteps'][rigParams['tableStepMode']])
    tableFrame.update_idletasks()  # Force update
    try:
        steps360 = Motor.setStepSize(rigParams['tableStepMode'])
        stepsPerTurn = steps360/rigParams['tableTotalPositions']
        homePosition()
    except:
        print('Could not initialize Motor')
    
def updateInitSteps():
    global rigParams
    global TablePosition
    stepDiff = rigParams['tableInitSteps'][rigParams['tableStepMode']] - int(tInitEnt.get())
    rigParams['tableInitSteps'][rigParams['tableStepMode']] += stepDiff  #The total number of positions, including walls, on the table
    #Had a test here to send the table home if it wasn't in the home position, but decided that may be a bad idea. Better to allow tuning from any position?
    if stepDiff >= 0:
        Motor.turn(int(stepDiff), Motor.CLOCKWISE)
    else:
        Motor.turn(int(stepDiff), Motor.ANTICLOCKWISE)
    tableInitSteps = rigParams['tableInitSteps']
    initvalues = [int(val) for val in tableInitSteps.values()]
    initvalues = ','.join(map(str, initvalues))
    outtableInitSteps = ["tableInitSteps", f"tableInitSteps = {initvalues} #The number of steps from the mag sensor to the home position"]
    update_line_in_file(file_path = rigParamsFile, keyword=outtableInitSteps[0], new_value=outtableInitSteps[1])

#A function to send the table to the home position, and set up position dead-reckoning    
def homePosition():
    global TablePosition
    rig_funcs.align_zero(he_inport=rigParams['hallPin'], adjust_steps=rigParams['tableInitSteps'])
    TablePosition = 1

#A function to change the table position, and udpate position dead-reckoning    
def movePosition(forward):
    global TablePosition
    if forward:
        Motor.turn(stepsPerTurn, Motor.CLOCKWISE)
        if TablePosition == rigParams['tableTotalPositions']:
            TablePosition = 1
        else:
            TablePosition += 1
    else:
        Motor.turn(stepsPerTurn, Motor.ANTICLOCKWISE)
        if TablePosition == 1:
            TablePosition = rigParams['tableTotalPositions']
        else:
                TablePosition += -1
                
#A function for flipping the state of Pi GPIO output pins, and tracking what they're meant to be
def toggleIO(pin,label=None):
    if "RPi.GPIO" in sys.modules:
        labelIs = label.cget('text')
        if GPIO.input(pin):
            label.config(text='Status: 0')
            GPIO.output(pin,GPIO.LOW)
        else:
            label.config(text='Status: 1')
            GPIO.output(pin,GPIO.HIGH)
    else:
        print("GPIO not loaded, simulating IO")
        labelIs = label.cget('text')
        if labelIs == 'Status: 1':
            label.config(text='Status: 0')
        else:
            label.config(text='Status: 1')

#A function for dynamically creating input fields and toggles for Intan outputs for spout position depending on how many spouts there are        
def initIntanSpouts(NPositions):
    global spoutPinList, spoutToggleList, spoutLabelList, spoutEntLabelList

    NSpouts = int(NPositions / 2)

    # Wipe Existing Widgets
    if 'spoutPinList' in globals():
        for widget_dict in [spoutPinList, spoutToggleList, spoutLabelList, spoutEntLabelList]:
            for widget in widget_dict.values():
                widget.destroy()

    # Create new dictionaries
    spoutPinList = {}
    spoutToggleList = {}
    spoutLabelList = {}
    spoutEntLabelList = {}

    # Expand or Trim rigParams['intanSpoutPins']
    if len(rigParams['intanSpoutPins']) < NSpouts:
        rigParams['intanSpoutPins'].extend([0] * (NSpouts - len(rigParams['intanSpoutPins'])))

    yPad = 1
    xPad = 2
    for posN in range(NSpouts):
        spoutN = (posN + 1) * 2
        maxCols = 3
        rowMod, colMod = divmod(posN, maxCols)
        colMod *= 2
        # Create Label
        spoutEntLabel = tk.Label(pinFrame, text=f"{spoutN}:")
        spoutEntLabel.grid(row=NPinRows+rowMod, column=colMod, padx=xPad, pady=yPad, sticky='e')
        spoutEntLabelList[posN] = spoutEntLabel

        # Create Entry
        spoutVar = tk.DoubleVar(value=rigParams['intanSpoutPins'][posN])
        spoutEnt = tk.Entry(pinFrame, textvariable=spoutVar, width=5)
        spoutEnt.grid(row=NPinRows+rowMod, column=colMod+1, padx=xPad, pady=yPad)
        spoutPinList[posN] = spoutEnt

        # Create Toggle Button (fixing lambda capture)
        spoutToggle = tk.Button(
            IO_frame,
            text=f"Spout {spoutN}",
            command=lambda p=posN: toggleIO(pin=rigParams['intanSpoutPins'][p], label=spoutLabelList[p]),
            width=6,
        )
        spoutToggle.grid(row=NToggleRows+rowMod, column=colMod, padx=xPad, pady=yPad,sticky='e')
        spoutToggleList[posN] = spoutToggle

        # Create Status Label
        spoutLabel = tk.Label(IO_frame, text="Status: 0")
        spoutLabel.grid(row=NToggleRows+rowMod, column=colMod+1, padx=xPad, pady=yPad)
        spoutLabelList[posN] = spoutLabel
    
#%% Code execution
try:
    global tSpdBox,tInitBox
    try:
        rig_funcs.configureIOPins()
        Motor = bipol.Motor(rigParams['stepPin'], rigParams['directionPin'], rigParams['enablePin'], rigParams['msPins'][0], rigParams['msPins'][1], rigParams['msPins'][2]) #initialize motor
        steps360 = Motor.setStepSize(rigParams['tableStepMode'])
        stepsPerTurn = steps360/rigParams['tableTotalPositions']
        homePosition()
    except:
        print('Could not initialize Motor')

    # GUI setup
    if not tk._default_root:
        root = tk.Tk()  # Create a root window if none exists
        root.withdraw()  # Hide the root window since we only want Toplevel
        isChild = False
    else:
        isChild = True
        root = tk._default_root  # Use the existing root
    def on_close():
        calibrateGUI.destroy()  # Destroy the Toplevel window
        if not isChild: root.destroy()    # Destroy the hidden root window

    # Now create your Toplevel window
    calibrateGUI = tk.Toplevel(root)
    calibrateGUI.title("Motor and Sensor Calibration")
    calibrateGUI.protocol("WM_DELETE_WINDOW", on_close)
    
    # Button for updating parameters
    updateButton = tk.Button(calibrateGUI, text="Update Parameters", command=updateParameters)
    updateButton.grid(row=1, column=1, padx=10, pady=10,sticky='sw')
    ToolTip(updateButton, 'Updates all parameters from text entry boxes,\nincluding both table settings and pin assignments')
    
    # Table control section
    tableFrame = ttk.LabelFrame(calibrateGUI, text="Table Control")
    tableFrame.grid(row=0, column=0, padx=10, pady=10, sticky= 'ew',rowspan=2)
    
    rowN = 0
    tk.Label(tableFrame, text="Motor Total Steps:").grid(row=rowN, column=0, padx=10, pady=5)
    tTotEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=rigParams['tableTotalSteps']), width=7)
    tTotEnt.grid(row=rowN, column=1, padx=10, pady=5)
    
    rowN += 1
    tk.Label(tableFrame, text="Total Positions:").grid(row=rowN, column=0, padx=10, pady=5)
    tPosEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=rigParams['tableTotalPositions']), width=7)
    tPosEnt.grid(row=rowN, column=1, padx=10, pady=5)
    ToolTip(tPosEnt, 'Total positions on table,\n including bottles and walls')

    rowN += 1
    modeOptions = ['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'SIXTEENTH']
    modeLabel = tk.Label(tableFrame, text="Step Mode:")
    modeLabel.grid(row = rowN, column=0, padx=10, pady=5)
    tModeEnt = tk.StringVar()
    tModeEnt.set(rigParams['tableStepMode'])
    modeList = tk.OptionMenu(tableFrame,tModeEnt, *modeOptions, command=updateStepMode)
    modeList.grid(row = rowN, column=1, padx=10, pady=5)

    rowN += 1
    tk.Label(tableFrame, text="Initial Steps:").grid(row=rowN, column=0, padx=10, pady=5)
    tInitEnt = tk.IntVar()
    tInitEnt.set(rigParams['tableInitSteps'][rigParams['tableStepMode']])
    tInitBox = tk.Spinbox(tableFrame, textvariable=tInitEnt, command= updateInitSteps, width=6)
    tInitBox.grid(row=rowN, column=1, padx=10, pady=5)
    
    rowN += 1
    tk.Label(tableFrame, text="Step Delay:").grid(row=rowN, column=0, padx=10, pady=5)
    tSpdEnt = tk.DoubleVar()
    tSpdEnt.set(value=rigParams['tableSpeed'][rigParams['tableStepMode']])
    tSpdBox = tk.Entry(tableFrame, textvariable=tSpdEnt, width=7)
    tSpdBox.grid(row=rowN, column=1, padx=10, pady=5)
    # Create buttons
    rowN += 1
    tk.Button(tableFrame, text="Init", command= homePosition).grid(row=rowN, column=0, padx=10, pady=10)
    tk.Button(tableFrame, text="Next", command= lambda: movePosition(forward=True)).grid(row=rowN, column=1, padx=10, pady=10)
    tk.Button(tableFrame, text="Prev", command= lambda: movePosition(forward=False)).grid(row=rowN, column=2, padx=10, pady=10)

    
    #Pin Config Section
    pinFrame = ttk.LabelFrame(calibrateGUI, text="Pin Configuration")
    pinFrame.grid(row=2, column=0, padx=10, pady=10, columnspan=1, sticky='w')
    
    xPad = 0
    rowNPin = 0
    tk.Label(pinFrame, text="Step Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pStepEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['stepPin']), width=5)
    pStepEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Direction Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pDirEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['directionPin']), width=5)
    pDirEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Enable Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pEnbEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['enablePin']), width=5)
    pEnbEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Motor Logic Pins:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    rowNPin += 1
    tk.Label(pinFrame, text="MS1:").grid(row=rowNPin, column=0, padx=0, pady=5, sticky='e')
    pMS1Ent = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['msPins'][0]), width=5)
    pMS1Ent.grid(row=rowNPin, column=1, padx=0, pady=5)
    tk.Label(pinFrame, text="MS2:").grid(row=rowNPin, column=2, padx=0, pady=5, sticky='e')
    pMS2Ent = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['msPins'][1]), width=5)
    pMS2Ent.grid(row=rowNPin, column=3, padx=0, pady=5)
    tk.Label(pinFrame, text="MS3:").grid(row=rowNPin, column=4, padx=0, pady=5, sticky='e')
    pMS3Ent = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['msPins'][2]), width=5)
    pMS3Ent.grid(row=rowNPin, column=5, padx=0, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Hall Effect Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pHallEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['hallPin']), width=5)
    pHallEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Beam Sense Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pBeamEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['lickBeamPin']), width=5)
    pBeamEnt.grid(row=rowNPin, column=1, padx=10, pady=5)
    
    rowNPin += 1
    tk.Label(pinFrame, text="Laser Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pLazEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['laserPin']), width=5)
    pLazEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Beam LED Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pBeamLEDEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['lickLEDPin']), width=5)
    pBeamLEDEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Cue LED Pins:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    rowNPin += 1
    tk.Label(pinFrame, text="Blue:").grid(row=rowNPin, column=0, padx=0, pady=5, sticky='e')
    pBlueEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['cueLEDPins'][0]), width=5)
    pBlueEnt.grid(row=rowNPin, column=1, padx=0, pady=5)
    tk.Label(pinFrame, text="Green:").grid(row=rowNPin, column=2, padx=0, pady=5, sticky='e')
    pGreenEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['cueLEDPins'][1]), width=5)
    pGreenEnt.grid(row=rowNPin, column=3, padx=0, pady=5)
    tk.Label(pinFrame, text="Red:").grid(row=rowNPin, column=4, padx=0, pady=5, sticky='e')
    pRedEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['cueLEDPins'][2]), width=5)
    pRedEnt.grid(row=rowNPin, column=5, padx=0, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Intan Beam Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pIntBeamEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['intanBeamPin']), width=5)
    pIntBeamEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Intan Trial Pin:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    pIntTrialEnt = tk.Entry(pinFrame, textvariable=tk.DoubleVar(value=rigParams['intanTrialPin']), width=5)
    pIntTrialEnt.grid(row=rowNPin, column=1, padx=10, pady=5)

    rowNPin += 1
    tk.Label(pinFrame, text="Intan Spout Pins:").grid(row=rowNPin, column=0, padx=xPad, pady=5, sticky='e')
    NPinRows = rowNPin + 1

    # Sensor display section
    sensor_frame = ttk.LabelFrame(calibrateGUI, text="Sensor Readouts")
    sensor_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
    
    # Create labels for sensors
    sensor_labels = {
        "Lick Sensor": ttk.Label(sensor_frame, text="Lick Sensor: ---"),
        "Table Mag Sensor": ttk.Label(sensor_frame, text="Table Mag Sensor: ---"),
        "Read Delay": ttk.Label(sensor_frame, text="Read Delay: ---"),
        "Current Position": ttk.Label(sensor_frame, text="Current Position: ---")
    }
    
    # Place each label in the grid
    for i, (sensor_name, label) in enumerate(sensor_labels.items()):
        label.grid(row=i, column=0, padx=5, pady=5)
    
    # Start updating the sensor display
    if "RPi.GPIO" in sys.modules:
        update_sensor_display(sensor_labels)
    else:
        print("GPIO not loaded: Sensors will not update")
        
    #I/O Toggle section
    xPad = 2
    IO_frame = ttk.LabelFrame(calibrateGUI, text="I/O Toggles")
    IO_frame.grid(row=2, column=1, padx=10, pady=10, columnspan=2, sticky='nw')
    rowN = 0
    buttonWidth = 8
    yPad = 4
    tk.Button(IO_frame, text="Enable", command= lambda: toggleIO(pin=rigParams['enablePin'], label=labEnable), width=buttonWidth).grid(row=rowN, column=0, padx=xPad, pady=yPad, sticky='e')
    labEnable = tk.Label(IO_frame, text= "Status: 0")
    labEnable.grid(row=rowN, column=1, padx = 10, pady=yPad)
    
    rowN += 1
    tk.Button(IO_frame, text="Beam LED", command= lambda: toggleIO(pin=rigParams['lickLEDPin'], label=labBeam), width=buttonWidth).grid(row=rowN, column=0, padx=xPad, pady=yPad, sticky='e')
    labBeam = tk.Label(IO_frame, text= "Status: 0")
    labBeam.grid(row=rowN, column=1, padx = 10, pady=yPad)
    
    rowN += 1
    tk.Button(IO_frame, text="Laser", command= lambda: toggleIO(pin=rigParams['laserPin'], label=labLaser), width=buttonWidth).grid(row=rowN, column=0, padx=xPad, pady=yPad, sticky='e')
    labLaser = tk.Label(IO_frame, text= "Status: 0")
    labLaser.grid(row=rowN, column=1, padx = 10, pady=yPad)

    rowN += 1
    tk.Label(IO_frame, text= "Cue LED:").grid(row=rowN, column=0, padx = 10, pady=yPad)
    rowN += 1
    tk.Button(IO_frame, text="Blue", command= lambda: toggleIO(pin=rigParams['cueLEDPins'][0], label=labBlue), width=6).grid(row=rowN, column=0, padx=2, pady=2, sticky='e')
    labBlue = tk.Label(IO_frame, text= "Status: 0")
    labBlue.grid(row=rowN, column=1, padx = 2, pady=2)
    tk.Button(IO_frame, text="Green", command= lambda: toggleIO(pin=rigParams['cueLEDPins'][1], label=labGreen), width=6).grid(row=rowN, column=2, padx=2, pady=2, sticky='e')
    labGreen = tk.Label(IO_frame, text= "Status: 0")
    labGreen.grid(row=rowN, column=3, padx = 2, pady=2)
    tk.Button(IO_frame, text="Red", command= lambda: toggleIO(pin=rigParams['cueLEDPins'][2], label=labRed), width=6).grid(row=rowN, column=4, padx=2, pady=2, sticky='e')
    labRed = tk.Label(IO_frame, text= "Status: 0")
    labRed.grid(row=rowN, column=5, padx = 2, pady=2)

    rowN += 1
    tk.Label(IO_frame, text= "Intan Outs:").grid(row=rowN, column=0, padx = 10, pady=yPad)
    rowN += 1
    tk.Button(IO_frame, text="Beam", command= lambda: toggleIO(pin=rigParams['intanBeamPin'], label=labIntBeam), width=buttonWidth).grid(row=rowN, column=0, padx=xPad, pady=yPad, sticky='e')
    labIntBeam = tk.Label(IO_frame, text= "Status: 0")
    labIntBeam.grid(row=rowN, column=1, padx = 10, pady=yPad)
    rowN += 1
    tk.Button(IO_frame, text="Trial", command= lambda: toggleIO(pin=rigParams['intanTrialPin'], label=labIntTrial), width=buttonWidth).grid(row=rowN, column=0, padx=xPad, pady=yPad, sticky='e')
    labIntTrial = tk.Label(IO_frame, text= "Status: 0")
    labIntTrial.grid(row=rowN, column=1, padx = 10, pady=yPad)
    NToggleRows = rowN +1
    initIntanSpouts(NPositions=rigParams['tableTotalPositions'])

    calibrateGUI.mainloop()
finally:
    try:
        Motor.reset()
    except:
        print('Could not reset Motor during shutdown')
