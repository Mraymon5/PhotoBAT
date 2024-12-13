#%% Import Modules
import time
import tkinter as tk
from tkinter import ttk

#%% Import Local Functions
import MCC_Setup; MCC = MCC_Setup.MCCInterface(); Dav = MCC_Setup.DavRun()

#%% Helper Functions
# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a givin position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Function to allow flexible inputs for True in user-supplied strings
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

# Calibration Gui functions
# Function to update sensor values
def update_sensor_display(sensor_labels):
    readTime = time.time()
    readSens = MCC.d_in(0, 1)
    readDelay = f"Read Delay: {round(time.time() - readTime, 4)}"
    lSens = f"Lick Sensor: {MCC.getBit(portType=1, channel=7, sensorState=readSens)}"
    sMagSens = f"Shutter Mag: {MCC.getBit(portType=1, channel=5, sensorState=readSens)}"
    tMagSens = f"Table Mag: {MCC.getBit(portType=1, channel=4, sensorState=readSens)}"
    values = [lSens, sMagSens, tMagSens, readDelay]
    
    # Update each label with the corresponding sensor value
    for label, value in zip(sensor_labels.values(), values):
        label.config(text=value)
    
    # Schedule the function to run again after 500ms
    root.after(10, update_sensor_display, sensor_labels)

def update_parameters():
    # Example of retrieving values from the text boxes
    
    shutterInitSteps = round(float(sInitEnt.get())) #The number of steps from the mag sensor to the "closed" position
    shutterRunSteps = int(sRunEnt.get()) #The number of steps to open/close the shutter
    shutterDir = int(sDirEnt.get()) #The base direction of the shutter
    shutterSpeed = float(sSpdEnt.get())

    tableInitSteps = round(float(tInitEnt.get())) #The number of steps from the mag sensor to the home position
    tableRunSteps = int(tRunEnt.get()) #The number of steps between bottle positions
    tableDir = int(tDirEnt.get()) #The base direction of the table
    tableSpeed = float(tSpdEnt.get())
    
    outHeader = "#Davis Rig Hardware Parameters. You probably don't want to edit this manually; try MCC_Test.py instead.\n"
    outboardNum = f"boardNum={Dav.boardNum}\n"
    outshutterInitSteps = f"shutterInitSteps={shutterInitSteps}\n"
    outshutterRunSteps = f"shutterRunSteps={shutterRunSteps}\n"
    outshutterDir = f"shutterDir={shutterDir}\n"
    outshutterSpeed = f"shutterSpeed={shutterSpeed}\n"
    outtableInitSteps = f"tableInitSteps={tableInitSteps}\n"
    outtableRunSteps = f"tableRunSteps={tableRunSteps}\n"
    outtableDir = f"tableDir={tableDir}\n"
    outtableSpeed = f"tableSpeed={tableSpeed}"
    
    outLines = (outHeader + outboardNum + outshutterInitSteps + outshutterRunSteps + outshutterDir + outshutterSpeed +
                outtableInitSteps + outtableRunSteps + outtableDir + outtableSpeed)

    with open(Dav.params_path, 'w') as outputFile:
        outputFile.write(outLines)
        print(f'Params saved as {Dav.params_path}')


#%% Code execution
try:
    MCC.d_config_port(board_num = Dav.boardNum, port = 0, direction = 'output')
    MCC.d_out(board_num = Dav.boardNum, port = 0, data = 0b11111111)
    # GUI setup
    root = tk.Tk()
    root.title("Motor and Sensor Calibration")
    MCC.d_config_port(board_num = Dav.boardNum, port = 1, direction = 'input')
    
    # Shutter control section
    shutterFrame = ttk.LabelFrame(root, text="Shutter Control")
    shutterFrame.grid(row=0, column=0, padx=10, pady=10)
    
    tk.Label(shutterFrame, text="Shutter Initial Steps:").grid(row=0, column=0, padx=10, pady=5)
    sInitEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterInitSteps))
    sInitEnt.grid(row=0, column=1, padx=10, pady=5)
    
    tk.Label(shutterFrame, text="Shutter Run Steps:").grid(row=1, column=0, padx=10, pady=5)
    sRunEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterRunSteps))
    sRunEnt.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(shutterFrame, text="Shutter Direction:").grid(row=2, column=0, padx=10, pady=5)
    sDirEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterDir))
    sDirEnt.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(shutterFrame, text="Shutter Step Delay:").grid(row=3, column=0, padx=10, pady=5)
    sSpdEnt = tk.Entry(shutterFrame, textvariable=tk.DoubleVar(value=Dav.shutterSpeed))
    sSpdEnt.grid(row=3, column=1, padx=10, pady=5)
    # Create buttons
    tk.Button(shutterFrame, text="Init", command=lambda: Dav.moveShutter(Init = True)).grid(row=4, column=0, padx=10, pady=10)
    tk.Button(shutterFrame, text="Open", command=lambda: Dav.moveShutter(Open = True)).grid(row=4, column=1, padx=10, pady=10)
    tk.Button(shutterFrame, text="Close", command=lambda: Dav.moveShutter(Open = False)).grid(row=4, column=2, padx=10, pady=10)
    
    
    # Table control section
    tableFrame = ttk.LabelFrame(root, text="Table Control")
    tableFrame.grid(row=2, column=0, padx=10, pady=10)

    tk.Label(tableFrame, text="Table Initial Steps:").grid(row=0, column=0, padx=10, pady=5)
    tInitEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableInitSteps))
    tInitEnt.grid(row=0, column=1, padx=10, pady=5)
    
    tk.Label(tableFrame, text="Table Run Steps:").grid(row=1, column=0, padx=10, pady=5)
    tRunEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableRunSteps))
    tRunEnt.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(tableFrame, text="Table Direction:").grid(row=2, column=0, padx=10, pady=5)
    tDirEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableDir))
    tDirEnt.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(tableFrame, text="Table Step Delay:").grid(row=3, column=0, padx=10, pady=5)
    tSpdEnt = tk.Entry(tableFrame, textvariable=tk.DoubleVar(value=Dav.tableSpeed))
    tSpdEnt.grid(row=3, column=1, padx=10, pady=5)
    # Create buttons
    tk.Button(tableFrame, text="Init", command=lambda: Dav.moveTable(Init = True)).grid(row=4, column=0, padx=10, pady=10)
    tk.Button(tableFrame, text="Next", command=lambda: Dav.moveTable(movePos = 1)).grid(row=4, column=1, padx=10, pady=10)
    tk.Button(tableFrame, text="Prev", command=lambda: Dav.moveTable(movePos = -1)).grid(row=4, column=2, padx=10, pady=10)
    
    tk.Button(root, text="Update Parameters", command=update_parameters).grid(row=1, column=1, padx=10, pady=10)
    
    # Sensor display section
    sensor_frame = ttk.LabelFrame(root, text="Sensor Readouts")
    sensor_frame.grid(row=0, column=1, padx=10, pady=10)
    
    # Create labels for sensors
    sensor_labels = {
        "Lick Sensor": ttk.Label(sensor_frame, text="Lick Sensor: ---"),
        "Shutter Mag Sensor": ttk.Label(sensor_frame, text="Shutter Mag Sensor: ---"),
        "Table Mag Sensor": ttk.Label(sensor_frame, text="Table Mag Sensor: ---"),
        "Read Delay": ttk.Label(sensor_frame, text="Read Delay: ---")
    }
    
    # Place each label in the grid
    for i, (sensor_name, label) in enumerate(sensor_labels.items()):
        label.grid(row=i, column=0, padx=5, pady=5)
    
    # Start updating the sensor display
    update_sensor_display(sensor_labels)
    
    root.mainloop()
finally:
    MCC.d_close_port()
