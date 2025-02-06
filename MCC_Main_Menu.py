#Import Modules
import tkinter as tk
from tkinter import ttk
import tkintertable
import sys
import os
import easygui
import subprocess

#Import Scripts
from MakeParams import makeParams, readParameters

#%% Import Variables
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
rigParamsFile = os.path.join(base_path, 'MCC_params.txt')
with open(rigParamsFile, 'r') as params:
    paramsData = params.readlines()
paramsData = [line.rstrip('\n') for line in paramsData]
paramsData = [line.split('#')[0] for line in paramsData]
paramsData = [line.split('=') for line in paramsData]
paramsFile = ([line[1] for line in paramsData if 'paramsFile' in line[0]][0])
paramsFile = paramsFile.strip()
outputFolder = (([line[1] for line in paramsData if 'outputFolder' in line[0]][0]))
outputFolder = outputFolder.strip()


#%% Helper Functions
#Function to create a tkintertable that is read-only
class passiveTableCanvas(tkintertable.TableCanvas):
    def __init__(self, master=None, *args, **kw):
        super().__init__(master, *args, **kw)
        self.columnactions = {}

    def drawCellEntry(self, row, col):
        pass

# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a given position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

# Function to allow flexible inputs for True in user-supplied strings
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

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
        print(f"Updated `{keyword}` in {file_path} to `{new_value}`.")
    else:
        print(f"Keyword `{keyword}` not found in {file_path}.")

# Calibration Gui functions
# Function to update sensor values
def select_paramsFile():
    global paramsFile
    paramsFolder = os.path.join(base_path, 'params/*')
    tempFile = easygui.fileopenbox(msg="Select a params file, or cancel for manual entry", default=paramsFolder)
    if tempFile is not None:
        paramsFile = os.path.normpath(tempFile)
        paramLabel.config(text=paramsFile)
        update_line_in_file(file_path = rigParamsFile, keyword="paramsFile =", new_value=f'paramsFile = {paramsFile} #Path to last params file')
        updateVersion()

def create_paramsFile():
    global paramsFile
    tempFile = makeParams(str(sysIs.get()))
    if tempFile != False:
        paramsFile = tempFile
        paramLabel.config(text=paramsFile)
        update_line_in_file(file_path = rigParamsFile, keyword="paramsFile =", new_value=f'paramsFile = {paramsFile} #Path to last params file')
        updateVersion()

def display_parameters():
    version, trialData = readParameters(paramsFile=paramsFile)
    paramDisp = tk.Toplevel(root)
    paramDisp.title("Session Parameters")
    
    frame = tk.Frame(paramDisp)
    frame.grid(row=0, column=0, padx=10, pady=10)
    
    table_model = tkintertable.TableModel()
    table_model.importDict(trialData.to_dict(orient="index"))
    
    # Create and display the table
    table = passiveTableCanvas(frame, model=table_model)
    table.show()

    # Function to clean up bindings when window is closed
    def on_close():
        table.unbind_all("<Up>")
        table.unbind_all("<Down>")
        table.unbind_all("<Left>")
        table.unbind_all("<Right>")
        table.unbind_all("<Return>")
        table.unbind_all("<Delete>")
        table.unbind("<KP_Up>")
        table.unbind("<KP_Down>")
        table.unbind("<KP_Left>")
        table.unbind("<KP_Right>")
        paramDisp.destroy()
    
    paramDisp.protocol("WM_DELETE_WINDOW", on_close)

def updateVersion():
    version, trialData = readParameters(paramsFile=paramsFile)
    if version == 'Davis Rig':
        sysIs.set('Davis Rig')
    elif version == 'PhotoBAT':
        sysIs.set('PhotoBAT')
    elif version == "IOC":
        sysIs.set('IOC')
    else:
        easygui.msgbox(msg = "Is the correct hardware selected?", title="Version Check")

def updateFolder():
    global outputFolder
    outputTemp = outputEnt.get()
    if os.path.isdir(outputTemp):
        outputEnt.set(outputTemp)
        outputFolder = outputTemp
        update_line_in_file(file_path = rigParamsFile, keyword="outputFolder =", new_value=f'outputFolder = {outputFolder} #Path to last output directory')
    else:
        makeFolder = easygui.ccbox(msg=f"The folder {outputTemp} does not exist. Create it?", title="Make folder?")
        if makeFolder:
            os.mkdir(outputTemp)
            outputFolder = outputTemp
            update_line_in_file(file_path = rigParamsFile, keyword="outputFolder =", new_value=f'outputFolder = {outputFolder} #Path to last output directory')
        else:
            outputEnt.set(outputFolder)

def selectOutput():
    global outputFolder
    tempFolder = easygui.diropenbox(msg="Select an Output Directory", default=outputFolder)
    if tempFolder is not None:
        outputFolder = tempFolder
        outputEnt.set(outputFolder)
        update_line_in_file(file_path = rigParamsFile, keyword="outputFolder =", new_value=f'outputFolder = {outputFolder} #Path to last output directory')

def runConfig():
    if sysIs.get() == 'Davis Rig':
        from MCC_Calibrate import rigConfig
        rigConfig()
    elif sysIs.get() == 'PhotoBAT':
        targetScript = os.path.join(base_path, 'BAT_Calibrate.py')
        subprocess.run(["python", targetScript])
    elif sysIs.get() == 'IOC':
        easygui.msgbox(msg = 'IOC not implemented', title="Version Check")
    else:
        easygui.msgbox(msg = 'Select hardware', title="Version Check")

def runSession():
    if str(sysIs.get()) == 'Davis Rig':
        targetScript = os.path.join(base_path, 'licking_MCC.py')
    elif str(sysIs.get()) == 'PhotoBAT':
        targetScript = os.path.join(base_path, 'licking_beambk_Camera.py')
    elif str(sysIs.get()) == 'IOC':
        targetScript = None
        easygui.msgbox(msg = 'IOC not implemented', title="Version Check")
        import pi_rig
        root.destroy()
        pi_rig.passive() #TODO implement this code
    else:
        targetScript = None
        easygui.msgbox(msg = 'Select hardware', title="Version Check")
    if targetScript is not None:
        args = [str(ID_Ent.get()),
                "-p", paramsFile.strip(),
                "-o", outputFolder.strip()]
        root.destroy()
        subprocess.run(["python", targetScript] + args)

def featureWarn():
    easygui.msgbox(msg="This feature is not implemented", title="Warning")

#%% GUI Code
root = tk.Tk()
root.title("Session Setup")
ParamFrame = ttk.LabelFrame(root, text="Session Parameters")
ParamFrame.grid(row=0, column=0, padx=10, pady=10, sticky='nwe')
#Field showing param file. Autoload last?
tk.Label(ParamFrame, text="Parameters File:").grid(row=0, column=0, padx=10, pady=5, sticky='ne')
paramLabel = tk.Label(ParamFrame, text=f"{paramsFile}")
paramLabel.grid(row=0, column=1, padx=10, pady=5, sticky='nw', columnspan=2)
#Button to open param file
tk.Button(ParamFrame, text="Select Params File", command=select_paramsFile, width=15).grid(row=1, column=0, padx=10, pady=10)
#Button to create param file
tk.Button(ParamFrame, text="Create Params File", command=create_paramsFile, width=15).grid(row=1, column=1, padx=10, pady=10, sticky='nw')
#Button to view parameters
tk.Button(ParamFrame, text="Display Params", command=display_parameters, width=15).grid(row=1, column=2, padx=10, pady=10)
#Field for animal ID
tk.Label(ParamFrame, text='Animal ID:').grid(row=2, column=0, padx=10, pady=5,sticky='ne')
ID_Ent = tk.Entry(ParamFrame, textvariable=tk.IntVar(value='ID'), width=15)
ID_Ent.grid(row=2, column=1, padx=10, pady=5, sticky='nw')

OutputFrame = ttk.LabelFrame(root, text="Output Folder")
OutputFrame.grid(row=1, column=0, padx=10, pady=10, sticky='nwe')
#Field showing output folder. Autoload last, save to machine params
tk.Label(OutputFrame, text="Output Folder:").grid(row=0, column=0, padx=10, pady=5, sticky='ne')
outputEnt = tk.StringVar()
outputEnt.set(outputFolder)
#Field for entering new folder path
outputEntBox = tk.Entry(OutputFrame, textvariable=outputEnt, width=40)
outputEntBox.grid(row=0, column=1, padx=10, pady=5, columnspan=2)
#Button to update output folder?
tk.Button(OutputFrame, text="Update Folder", command=updateFolder, width=15).grid(row=1, column=0, padx=10, pady=10)
#Button to open folder dialog
tk.Button(OutputFrame, text="Select Folder", command=selectOutput, width=15).grid(row=1, column=1, padx=10, pady=10, sticky='nw')

RunFrame = ttk.LabelFrame(root, text="Hardware Control")
RunFrame.grid(row=2, column=0, padx=10, pady=10, sticky='nw')
#Button to run config
tk.Button(RunFrame, text="Config Rig", command=runConfig,width=15).grid(row=1, column=0, padx=10, pady=10)
#Button to start session?
tk.Button(RunFrame, text="Run Session", command=runSession,width=15).grid(row=1, column=1, padx=10, pady=10)
#Button for whether this is a Davis Rig
sysLabel = tk.Label(RunFrame, text="Hardware Version:")
sysLabel.grid(row = 0, column=0, padx=10, pady=5, sticky='ne')
sysOptions = ['PhotoBAT', 'Davis Rig', 'IOC']
sysIs = tk.StringVar()
sysIs.set('Select Hardware')
sysList = tk.OptionMenu(RunFrame,sysIs, *sysOptions)
sysList.config(width=13)
sysList.grid(row = 0, column=1, padx=10, pady=5)
updateVersion()

#Run the GUI
root.mainloop()
