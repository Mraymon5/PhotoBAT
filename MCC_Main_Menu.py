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
from MakeParams import makeParams
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
outputFolder = (([line[1] for line in paramsData if 'outputFolder' in line[0]][0]))


#%% Helper Functions
# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a givin position is a numeral, convert to int
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
        paramsFile = tempFile
        paramLabel.config(text=paramsFile)
        update_line_in_file(file_path = rigParamsFile, keyword="paramsFile =", new_value=f'paramsFile = {paramsFile} #Path to last params file')

def create_paramsFile():
    global paramsFile
    paramsFile = makeParams()
    paramLabel.config(text=paramsFile)
    update_line_in_file(file_path = rigParamsFile, keyword="paramsFile =", new_value=f'paramsFile = {paramsFile} #Path to last params file')


def display_parameters():
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
        useLED = False
    try:
        useCamera = [line[1] for line in paramsData if 'UseCamera' in line[0]][0]
    except:
        useCamera = False
    
    tastes = [stimN for stimN in Solutions if len(stimN) > 0]
    taste_positions = [int(stimN+1) for stimN in range(len(Solutions)) if len(Solutions[stimN]) > 0]
    concs = [stimN for stimN in Concentrations if len(stimN) > 0]
    tasteList =  [Solutions[tubeN] for tubeN in TubeSeq]
    concList =  [Concentrations[tubeN] for tubeN in TubeSeq]
    stimList = [f'{concList[trialN]} {tasteList[trialN]}' for trialN in range(NTrials)]
    
    #Set Lick Time List
    if len(LickTime) < NTrials:
        LickTime = (LickTime * -(-NTrials//len(LickTime)))[:NTrials]
    if len(LickTime) > NTrials:
        LickTime = LickTime[:NTrials]
    #Set Lick Count List
    if len(LickCount) < NTrials:
        LickCount = (LickCount * -(-NTrials//len(LickCount)))[:NTrials]
    if len(LickCount) > NTrials:
        LickCount = LickCount[:NTrials]
    #Set Trial List
    if len(TubeSeq) < NTrials:
        TubeSeq = (TubeSeq * -(-NTrials//len(TubeSeq)))[:NTrials]
    if len(TubeSeq) > NTrials:
        TubeSeq = TubeSeq[:NTrials]
    #Set IPI List
    if len(IPITimes) == 0 and (len(IPImin) != 0 and len(IPImax) != 0 ):
        IPITimes = [f'random({IPImin}-{IPImax})' for trialN in range(NTrials)]
    if len(IPITimes) < NTrials:
        IPITimes = (IPITimes * -(-NTrials//len(IPITimes)))[:NTrials]
    if len(IPITimes) > NTrials:
        IPITimes = IPITimes[:NTrials]
    #Set Max Wait List
    if len(MaxWaitTime) < NTrials:
        MaxWaitTime = (MaxWaitTime * -(-NTrials//len(MaxWaitTime)))[:NTrials]
    if len(MaxWaitTime) > NTrials:
        MaxWaitTime = MaxWaitTime[:NTrials]
    
    
    if any(LickTime[trialN] is None and LickCount[trialN] is None for trialN in range(NTrials)):
        raise Exception("Both LickTime and LickCount are None for some trials")

    trialData = pandas.DataFrame({'Trial':range(NTrials), 'Tube':TubeSeq, 'Conc':concList, 'Stim':tasteList, 'LickTime':LickTime, 'LickCount':LickCount,
                                  'IPI':IPITimes,'MaxWait':MaxWaitTime})    
        
    paramDisp = tk.Tk()
    paramDisp.title("Session Parameters")
    frame = tk.Frame(paramDisp)
    frame.pack(fill="both", expand=True)
    table_model = tkintertable.TableModel()
    table_model.importDict(trialData.to_dict(orient="index"))
    
    # Create and display the table
    table = tkintertable.TableCanvas(frame, model=table_model, editable=False)
    table.show()

    paramDisp.mainloop()
    
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

def runSession():
    targetScript = "/home/ramartin/PhotoBAT-main/licking_MCC_test.py"
    args = [ID_Ent, f'-p {paramsFile}', f'-o {outputFolder}']
    root.destroy()
    result = subprocess.run(["python", targetScript] + args, capture_output=True,test=True)
    print("Session Run:")
    print(result)


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
tk.Button(RunFrame, text="Config Rig", command=rigConfig).grid(row=0, column=0, padx=10, pady=10)
#Button to start session?
tk.Button(RunFrame, text="Run Session", command=runSession).grid(row=0, column=1, padx=10, pady=10)

#Run the GUI
root.mainloop()
