#%% Import Modules
import easygui
import numpy as np
import os
import sys

#%% Helper Functions
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

#%% Get Parameters
params = easygui.multenterbox('Please enter parameters for this experiment.\nPer-trial parameters may be set manually\nby editing the text of a params file.',
                          'Experiment Parameters',
                          ['0: Wait time before first trial to be delivered (30s)',
                           '1: Maximal wait time per trial (60s)',
                           '2: Number of trials per taste (10)',
                           '3: Enter inter-trial interval (30s)',
                           '4: Maxiumum duration of session in minutes (90min)',
                           '5: Maximum lick time per trial (10s)',
                           '6: Maximum lick count per trial (None)',
                           '7: Use LED indicators? (T/F/Cue)',
                           '8: Use behavior camera? (T/F)',
                           '9: Param file Title',
                           '10: Davis Rig file? (T/F)'
                          ],
                          [30,60,10,30,90,10,None,False,False,'params','False'])
if params is None:
    print('Exiting')
    sys.exit()

#Read params
initial_wait = int(params[0]) #30, initial_wait
max_trial_time = int(params[1]) #60, max_trial_time
trials_per_taste = int(params[2]) #10
iti = int(params[3]) #30, iti
exp_dur = float(params[4]) * 60 #90, turn into seconds, exp_dur
max_lick_time = int(params[5]) if params[5] != '' else None #10, max_lick_time
max_lick_count = int(params[6]) if params[6] != '' else None #100
useLED = params[7] #0
useCamera = params[8] #0
fileTitle = params[9]
isDav = params[10]

useLED = isTrue(useLED)
useCamera = isTrue(useCamera)
isDav = isTrue(isDav)

# Get tastes and their spout locations
if isDav == 'True':
    bot_pos = ['']*16
    t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                  'Taste List',
                                  ['Spout {}'.format(i+1) for i in range(16)],
                                  values=bot_pos)
else:     
    bot_pos = ['Water', '', '', '']
    t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                  'Taste List',
                                  ['Spout {}'.format(i) for i in ['2, Yellow','4, Blue','6, Green','8, Red']],
                                  values=bot_pos)
if t_list is None:
    print('Exiting')
    sys.exit()

# Setting up spouts for each trial
tastes = [i for i in t_list if len(i) > 0]
taste_positions = [2*int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]

concs = easygui.multenterbox('Please enter the concentration of each taste.',
                              'Concentration List',
                              tastes,
                              values=[None]*len(tastes))
if concs is None:
    print('Exiting')
    sys.exit()

c_list = [next(iter(concs)) if x != '' else '' for x in t_list]


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

#%% Create Output
outTitle = "[Trial Parameters]\n"
outNumTubes = "NumberOfTubes=4\n"
outSolutions = f"Solutions={','.join(map(str, t_list))}\n"
outConcs = f"Concentrations={','.join(map(str, c_list))}\n"
outNTrials = f"NumberOfPres={NTrials}\n"
outLickTime = f"LickTime={','.join(map(str, [trialN*1000 for trialN in LickTime]))}\n"
outLickCount = f"LickCount={','.join(map(str, [trialN if trialN is not None else '' for trialN in LickCount]))}\n"
outTubeSeq = f"TubeSeq={','.join(map(str, TubeSeq))}\n"
outIPITimes = f"IPITimes={','.join(map(str, [trialN*1000 for trialN in IPITimes]))}\n"
outIPIMin = f"IPImin={IPITimes[0]*1000}\n"
outIPIMax = f"IPImax={IPITimes[0]*1000}\n"
outMaxWait = f"MaxWaitTime={','.join(map(str, [trialN*1000 for trialN in MaxWaitTime]))}\n"
outVersion = "Version=5.90\n"
outMaxReTries = "MaxReTries=0\n"
outSessionTimeLimit = f"SessionTimeLimit={round(SessionTimeLimit*1000)}\n"
outLED = f"UseLED={useLED}\n"
outCam = f"UseCamera={useCamera}"
if isDav == 'True':
    outLines = (outTitle + outNumTubes + outSolutions + outConcs + outNTrials + outLickTime + 
                outTubeSeq + outIPITimes + outIPIMin + outIPIMax + outMaxWait + 
                outVersion + outMaxReTries + outSessionTimeLimit)
else:    
    outLines = (outTitle + outNumTubes + outSolutions + outConcs + outNTrials + outLickTime + 
                outLickCount + outTubeSeq + outIPITimes + outIPIMin + outIPIMax + outMaxWait + 
                outVersion + outMaxReTries + outSessionTimeLimit + outLED + outCam)

#%%
proj_path = os.getcwd() #'/home/rig337-testpi/Desktop/katz_lickometer'

try:
    os.mkdir(os.path.join(proj_path, 'params'))
    print("No params folder, making one")
except:
    if os.path.isdir(os.path.join(proj_path, 'params')):
        print("Params folder found")
    else:
        print("Could not find or create params folder, can't save data")

outFile = os.path.join(proj_path, f'params/{fileTitle}.txt')


with open(outFile, 'w') as outputFile:
    outputFile.write(outLines)
    print(f'Params saved as {outFile}')
