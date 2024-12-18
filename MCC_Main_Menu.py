#Import Modules
import time
import tkinter as tk
from tkinter import ttk
import tkintertable
import sys
import os
import easygui
import random
import pandas
import subprocess

#Import Scripts
from MakeParams import makeParams, readParameters
from MCC_Calibrate import rigConfig #TODO:rename this probably

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
    tempFile = makeParams(bool(davEnt.get()))
    if tempFile != False:
        paramsFile = tempFile
        paramLabel.config(text=paramsFile)
        update_line_in_file(file_path = rigParamsFile, keyword="paramsFile =", new_value=f'paramsFile = {paramsFile} #Path to last params file')
        updateVersion()

def display_parameters():
    version,trialData = readParameters(paramsFile=paramsFile)
    paramDisp = tk.Toplevel(root)
    paramDisp.title("Session Parameters")
    frame = tk.Frame(paramDisp)
    frame.pack(fill="both", expand=True)
    table_model = tkintertable.TableModel()
    table_model.importDict(trialData.to_dict(orient="index"))
    
    # Create and display the table
    table = passiveTableCanvas(frame, model=table_model)
    table.show()

    paramDisp.mainloop()

def updateVersion():
    version, trialData = readParameters(paramsFile=paramsFile)
    if version == "Davis":
        davButton.select()
    elif version == "BAT":
        davButton.deselect()
    else:
        easygui.msgbox(msg = "Is the Davis Hardware toggle correct?", title="Version Check")

def updateFolder():
    global outputFolder
    outputFolder = outputEnt.get()
    outputLabel.config(text=outputFolder)
    
def selectOutput():
    global outputFolder
    tempFolder = easygui.diropenbox(msg="Select an Output Directory", default=outputFolder)
    if tempFolder is not None:
        outputFolder = tempFolder
        outputLabel.config(text=outputFolder)
        update_line_in_file(file_path = rigParamsFile, keyword="outputFolder =", new_value=f'outputFolder = {outputFolder} #Path to last output directory')

def runConfig():
    if bool(davEnt.get()):
        rigConfig()
    else:
        import rig_funcs
        rig_funcs.fine_align()

def runSession():
    if bool(davEnt.get()):
        targetScript = os.path.join(base_path, 'licking_MCC.py')
    elif bool(IOCEnt.get()):
        import rig_funcs
        root.destroy()
        passive() #TODO implement this code
    else:
        targetScript = os.path.join(base_path, 'licking_beambk_Camera.py')
    args = [str(ID_Ent.get()),
            "-p", paramsFile.strip(),
            "-o", outputFolder.strip()]
    root.destroy()
    result = subprocess.run(["python", targetScript] + args)
    #print("Session Run:")
    #print(result)

def featureWarn():
    easygui.msgbox(msg="This feature is not implemented", title="Warning")
    IOCButton.deselect()

#%% GUI Code
root = tk.Tk()
root.title("Session Setup")
ParamFrame = ttk.LabelFrame(root, text="Session Parameters")
ParamFrame.grid(row=0, column=0, padx=10, pady=10)
#Field showing param file. Autoload last?
tk.Label(ParamFrame, text="Parameters File:").grid(row=0, column=0, padx=10, pady=5)
paramLabel = tk.Label(ParamFrame, text=f"{paramsFile}")
paramLabel.grid(row=0, column=1, padx=10, pady=5)
#Button to open param file
tk.Button(ParamFrame, text="Select Params File", command=select_paramsFile).grid(row=1, column=0, padx=10, pady=10)
#Button to create param file
tk.Button(ParamFrame, text="Create Params File", command=create_paramsFile,).grid(row=1, column=1, padx=10, pady=10)
#Button to view parameters
tk.Button(ParamFrame, text="Display Params", command=display_parameters).grid(row=2, column=0, padx=10, pady=10)
#Field for animal ID
tk.Label(ParamFrame, text='Animal ID:').grid(row=3, column=0, padx=10, pady=5)
ID_Ent = tk.Entry(ParamFrame, textvariable=tk.IntVar(value='ID'))
ID_Ent.grid(row=3, column=1, padx=10, pady=5)

OutputFrame = ttk.LabelFrame(root, text="Output Folder")
OutputFrame.grid(row=1, column=0, padx=10, pady=10)
#Field showing output folder. Autoload last, save to machine params
tk.Label(OutputFrame, text="Output Folder:").grid(row=0, column=0, padx=10, pady=5)
outputLabel = tk.Label(OutputFrame, text=f"{outputFolder}")
outputLabel.grid(row=0, column=1, padx=10, pady=5)
#Field for entering new folder path
outputEnt = tk.Entry(OutputFrame, textvariable=tk.IntVar(value=outputFolder))
outputEnt.grid(row=1, column=0, padx=10, pady=5)
#Button to update output folder?
tk.Button(OutputFrame, text="Update Folder", command=updateFolder).grid(row=1, column=1, padx=10, pady=10)
#Button to open folder dialog
tk.Button(OutputFrame, text="Select Folder", command=selectOutput).grid(row=2, column=1, padx=10, pady=10)

RunFrame = ttk.LabelFrame(root, text="Hardware Control")
RunFrame.grid(row=2, column=0, padx=10, pady=10)
#Button to run config
tk.Button(RunFrame, text="Config Rig", command=runConfig).grid(row=1, column=0, padx=10, pady=10)
#Button to start session?
tk.Button(RunFrame, text="Run Session", command=runSession).grid(row=1, column=1, padx=10, pady=10)
#Button for whether this is a Davis Rig
davEnt = tk.IntVar()
davButton = tk.Checkbutton(RunFrame, text="Davis Hardware?", variable=davEnt, onvalue=True,offvalue=False)
davButton.grid(row = 0, column=0, padx=10, pady=5)
updateVersion()
IOCEnt = tk.IntVar()
IOCButton = tk.Checkbutton(RunFrame, text="IOC session?", variable=IOCEnt, onvalue=True,offvalue=False,command=featureWarn)
IOCButton.grid(row = 0, column=1, padx=10, pady=5)

#Run the GUI
root.mainloop()
