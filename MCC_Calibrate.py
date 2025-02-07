#%% Import Modules
import time
import tkinter as tk
from tkinter import ttk

#%% Import Local Functions
import MCC_Setup

def rigConfig():
    MCC = MCC_Setup.MCCInterface(); Dav = MCC_Setup.DavRun()
    #%% Helper Functions
    # Function to read in values from params file and save them as int or None
    def intOrNone(value, factor=1):
        try:
            return int(value)*factor # If the value in a given position is a numeral, convert to int
        except (ValueError, TypeError): # Otherwise return None
            return None
    
    # Function to allow flexible inputs for True in user-supplied strings
    isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})
    
    # Calibration Gui functions
    # Function to update sensor values
    def update_sensor_display(sensorData):
        readTime = time.time()
        readSens = MCC.d_in(0, 1)
        readDelay = f"{round(time.time() - readTime, 4):.3f}"
        lSens = f"{MCC.getBit(portType=1, channel=7, sensorState=readSens)}"
        sMagSens = f"{MCC.getBit(portType=1, channel=5, sensorState=readSens)}"
        tMagSens = f"{MCC.getBit(portType=1, channel=4, sensorState=readSens)}"
        values = [lSens, sMagSens, tMagSens, readDelay]
        
        # Update each label with the corresponding sensor value
        for label, value in zip(sensorData.values(), values):
            label.config(text=value)
        
        # Schedule the function to run again after 500ms
        calibrateGUI.after(10, update_sensor_display, sensorData)
    
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
        
        outHeader = "#Davis Rig Hardware Parameters. You probably don't want to edit this manually; try MCC_Main_Menu.py instead.\n"
        outboardNum = f"boardNum = {Dav.boardNum}\n"
        outshutterInitSteps = f"shutterInitSteps = {shutterInitSteps}\n"
        outshutterRunSteps = f"shutterRunSteps = {shutterRunSteps}\n"
        outshutterDir = f"shutterDir = {shutterDir}\n"
        outshutterSpeed = f"shutterSpeed = {shutterSpeed}\n"
        outtableInitSteps = f"tableInitSteps = {tableInitSteps}\n"
        outtableRunSteps = f"tableRunSteps = {tableRunSteps}\n"
        outtableDir = f"tableDir = {tableDir}\n"
        outtableSpeed = f"tableSpeed = {tableSpeed}"
        
        outLines = (outHeader + outboardNum + outshutterInitSteps + outshutterRunSteps + outshutterDir + outshutterSpeed +
                    outtableInitSteps + outtableRunSteps + outtableDir + outtableSpeed)
    
        with open(Dav.params_path, 'w') as outputFile:
            outputFile.write(outLines)
            print(f'Params saved as {Dav.params_path}')
    
    
    #%% Code execution
    try:
        MCC.d_config_port(board_num = Dav.boardNum, port = 0, direction = 'output')
        MCC.d_config_port(board_num = Dav.boardNum, port = 1, direction = 'input')
        MCC.d_out(board_num = Dav.boardNum, port = 0, data = 0b11111111)
        Dav.moveShutter(Init=True)
        Dav.moveTable(Init=True)
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
        
        boxPadX = 0
        # Shutter control section
        shutterFrame = ttk.LabelFrame(calibrateGUI, text="Shutter Control")
        shutterFrame.grid(row=0, column=0, padx=10, pady=10, sticky='nwe')
        
        tk.Label(shutterFrame, text="Shutter Initial Steps:").grid(row=0, column=0, padx=10, pady=5, sticky='ne')
        sInitEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterInitSteps))
        sInitEnt.grid(row=0, column=1, padx=boxPadX, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Run Steps:").grid(row=1, column=0, padx=10, pady=5, sticky='ne')
        sRunEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterRunSteps))
        sRunEnt.grid(row=1, column=1, padx=boxPadX, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Direction:").grid(row=2, column=0, padx=10, pady=5, sticky='ne')
        sDirEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=Dav.shutterDir))
        sDirEnt.grid(row=2, column=1, padx=boxPadX, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Step Delay:").grid(row=3, column=0, padx=10, pady=5, sticky='ne')
        sSpdEnt = tk.Entry(shutterFrame, textvariable=tk.DoubleVar(value=Dav.shutterSpeed))
        sSpdEnt.grid(row=3, column=1, padx=boxPadX, pady=5)
        # Create buttons
        tk.Button(shutterFrame, text="Init", command=lambda: Dav.moveShutter(Init = True)).grid(row=4, column=0, padx=10, pady=10)
        tk.Button(shutterFrame, text="Open", command=lambda: Dav.moveShutter(Open = True)).grid(row=4, column=1, padx=10, pady=10)
        tk.Button(shutterFrame, text="Close", command=lambda: Dav.moveShutter(Open = False)).grid(row=4, column=2, padx=10, pady=10)
        
        
        # Table control section
        tableFrame = ttk.LabelFrame(calibrateGUI, text="Table Control")
        tableFrame.grid(row=1, column=0, padx=10, pady=10, sticky='nwe')
    
        tk.Label(tableFrame, text="Table Initial Steps:").grid(row=0, column=0, padx=10, pady=5, sticky='ne')
        tInitEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableInitSteps))
        tInitEnt.grid(row=0, column=1, padx=boxPadX, pady=5)
        
        tk.Label(tableFrame, text="Table Run Steps:").grid(row=1, column=0, padx=10, pady=5, sticky='ne')
        tRunEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableRunSteps))
        tRunEnt.grid(row=1, column=1, padx=boxPadX, pady=5)
        
        tk.Label(tableFrame, text="Table Direction:").grid(row=2, column=0, padx=10, pady=5, sticky='ne')
        tDirEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=Dav.tableDir))
        tDirEnt.grid(row=2, column=1, padx=boxPadX, pady=5)
        
        tk.Label(tableFrame, text="Table Step Delay:").grid(row=3, column=0, padx=10, pady=5, sticky='ne')
        tSpdEnt = tk.Entry(tableFrame, textvariable=tk.DoubleVar(value=Dav.tableSpeed))
        tSpdEnt.grid(row=3, column=1, padx=boxPadX, pady=5)
        # Create buttons
        tk.Button(tableFrame, text="Init", command=lambda: Dav.moveTable(Init = True)).grid(row=4, column=0, padx=10, pady=10)
        tk.Button(tableFrame, text="Next", command=lambda: Dav.moveTable(movePos = 1)).grid(row=4, column=1, padx=10, pady=10)
        tk.Button(tableFrame, text="Prev", command=lambda: Dav.moveTable(movePos = -1)).grid(row=4, column=2, padx=10, pady=10)
        
        tk.Button(calibrateGUI, text="Update Parameters", command=update_parameters).grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        
        # Sensor display section
        sensor_frame = ttk.LabelFrame(calibrateGUI, text="Sensor Readouts")
        sensor_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        
        # Create labels for sensors
        lickLab = ttk.Label(sensor_frame, text="Lick Sensor:").grid(row=0, column=0, padx=5, pady=5, sticky='ne')
        sMagLab = ttk.Label(sensor_frame, text="Shutter Mag Sensor:").grid(row=1, column=0, padx=5, pady=5, sticky='ne')
        tMagLab = ttk.Label(sensor_frame, text="Table Mag Sensor:").grid(row=2, column=0, padx=5, pady=5, sticky='ne')
        delayLab = ttk.Label(sensor_frame, text="Read Delay:").grid(row=3, column=0, padx=5, pady=5, sticky='ne')

        sensorData = {
            "Lick Sensor": ttk.Label(sensor_frame, text="---", anchor='e',width=6, borderwidth=1, relief="solid"),#, background='white'
            "Shutter Mag Sensor": ttk.Label(sensor_frame, text="---", anchor='e',width=6, borderwidth=1, relief="solid"),#, background='white'
            "Table Mag Sensor": ttk.Label(sensor_frame, text="---", anchor='e',width=6, borderwidth=1, relief="solid"),#, background='white'
            "Read Delay": ttk.Label(sensor_frame, text="---", anchor='e',width=6, borderwidth=1, relief="solid")#, background='white'
        }
        
        # Place each label in the grid
        for i, (sensor_name, label) in enumerate(sensorData.items()):
            label.grid(row=i, column=1, padx=5, pady=5,sticky='nw')
        
        # Start updating the sensor display
        update_sensor_display(sensorData)

        calibrateGUI.mainloop()
    finally:
        MCC.d_close_port()
#%% Run the function
if __name__ == "__main__":
    rigConfig()
