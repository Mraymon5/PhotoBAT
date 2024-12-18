#%% Import Modules
import easygui
import numpy as np
import os
import sys
import random
import pandas
#%% Helper Functions
isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})
# Function to read in values from params file and save them as int or None
def intOrNone(value, factor=1):
    try:
        return int(value)*factor # If the value in a given position is a numeral, convert to int
    except (ValueError, TypeError): # Otherwise return None
        return None

#%% Get Parameters
def makeParams(davEnt=False):
    defaultVersion = "Davis Rig" if davEnt else "PhotoBAT"
    version = easygui.buttonbox(msg="What system are these parameters for?", title="Version Selection", choices=('PhotoBAT', "Davis Rig","IOC"),default_choice=defaultVersion)
    if version is None:
        print('Exiting')
        return(False)
    isDav=True if version == "Davis Rig" else False
    if version != "IOC":
        params = easygui.multenterbox('Please enter parameters for this experiment.\nPer-trial parameters may be set manually\nby editing the text of a params file.',
                                'Experiment Parameters',
                                ['0: Wait time before first trial to be delivered (30s)',
                                '1: Maximal wait time per trial (60s)',
                                '2: Number of trials per taste (10)',
                                '3: Minimum inter-trial interval (30s)',
                                '4: Maximum inter-trial interval (Same as min)',
                                '5: Maxiumum duration of session in minutes (90min)',
                                '6: Maximum lick time per trial (10s)',
                                '7: Maximum lick count per trial (None)',
                                '8: Use LED indicators? (T/F/Cue)',
                                '9: Use behavior camera? (T/F)',
                                '10: Param file Title'
                                ],
                                [30,60,10,30,None,90,10,None,False,False,'params'])
        if params is None:
            print('Exiting')
            return(False)
        
        #Read params
        initial_wait = int(params[0]) #30, initial_wait
        max_trial_time = int(params[1]) #60, max_trial_time
        trials_per_taste = int(params[2]) #10
        itiMin = int(params[3]) #30, iti
        itiMax = int(params[4]) if params[4] != '' else None #None, iti
        exp_dur = float(params[5]) * 60 #90, turn into seconds, exp_dur
        max_lick_time = int(params[6]) if params[6] != '' else None #10, max_lick_time
        max_lick_count = int(params[7]) if params[7] != '' else None #100
        useLED = params[8] #0
        useCamera = params[9] #0
        fileTitle = params[10]
        
        itiMax = itiMin if itiMax is None else int(itiMax)

        useLED = isTrue(useLED)
        useCamera = isTrue(useCamera)
        
        # Get tastes and their spout locations
        if isDav:
            bot_pos = ['']*16
            t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                        'Taste List',
                                        ['Spout {}'.format(i+1) for i in range(16)],
                                        values=bot_pos)
            taste_positions = [int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
        else:     
            bot_pos = ['Water', '', '', '']
            t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                        'Taste List',
                                        ['Spout {}'.format(i) for i in ['2, Yellow','4, Blue','6, Green','8, Red']],
                                        values=bot_pos)
            taste_positions = [2*int(i+1) for i in range(len(t_list)) if len(t_list[i]) > 0]
        if t_list is None:
            print('Exiting')
            return(False)
        
        # Setting up spouts for each trial
        tastes = [i for i in t_list if len(i) > 0]
        tasteLabel = ['Position {}: {}'.format(taste_positions[i], tastes[i]) for i in range(len(taste_positions))]
        
        concs = easygui.multenterbox('Please enter the concentration of each taste.',
                                    'Concentration List',
                                    tasteLabel,
                                    values=[None]*len(tastes))
        if concs is None:
            print('Exiting')
            return(False)

        concN = iter(concs)
        c_list = [next(concN) if x != '' else '' for x in t_list]
        
        trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(trials_per_taste)]
        trial_list = np.concatenate(trial_list)
        
        # Compute and Convert Session Variables
        NTrials = len(tastes)*trials_per_taste
        LickTime = [max_lick_time]*NTrials
        LickCount = [max_lick_count]*NTrials
        TubeSeq = trial_list
        if itiMax == itiMin:
            IPITimes = list(np.append(initial_wait,([itiMin]*(NTrials-1)))) #Make a list of IPIs with initial_wait as the first
            IPITimes = [round(trialN*1000) for trialN in IPITimes]
        else:
            IPITimes = [round(random.randrange(itiMin*1000,itiMax*1000)) for trialN in range(NTrials)]
        MaxWaitTime = [max_trial_time]*NTrials
        SessionTimeLimit = exp_dur
        nTubes = 16 if isDav else 4
        version = 'Davis' if isDav else 'BAT'
        #%% Create Output
        outTitle = "[Trial Parameters]\n"
        outNumTubes = f"NumberOfTubes={nTubes}\n"
        outSolutions = f"Solutions={','.join(map(str, t_list))}\n"
        outConcs = f"Concentrations={','.join(map(str, c_list))}\n"
        outNTrials = f"NumberOfPres={NTrials}\n"
        outLickTime = f"LickTime={','.join(map(str, [round(trialN*1000) for trialN in LickTime]))}\n"
        outLickCount = f"LickCount={','.join(map(str, [trialN if trialN is not None else '' for trialN in LickCount]))}\n"
        outTubeSeq = f"TubeSeq={','.join(map(str, TubeSeq))}\n"
        outIPITimes = f"IPITimes={','.join(map(str, IPITimes))}\n"
        outIPIMin = f"IPImin={round(itiMin*1000)}\n"
        outIPIMax = f"IPImax={round(itiMax*1000)}\n"
        outMaxWait = f"MaxWaitTime={','.join(map(str, [round(trialN*1000) for trialN in MaxWaitTime]))}\n"
        outVersion = f"Version={version}\n"
        outMaxReTries = "MaxReTries=0\n"
        outSessionTimeLimit = f"SessionTimeLimit={round(SessionTimeLimit*1000)}\n"
        outLED = f"UseLED={useLED}\n"
        outCam = f"UseCamera={useCamera}"
        if False: #isDav == 'True':
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
        
        outFile = os.path.normpath(os.path.join(proj_path, f'params/{fileTitle}.txt'))
        
        
        with open(outFile, 'w') as outputFile:
            outputFile.write(outLines)
            print(f'Params saved as {outFile}')
        
        return outFile
    else:
        params = easygui.multenterbox('Please enter parameters for this experiment.\nPer-trial parameters may be set manually\nby editing the text of a params file.',
                                'Experiment Parameters',
                                ['0: Number of trials per taste (10)',
                                '1: Minimum inter-trial interval (30s)',
                                '2: Maximum inter-trial interval (30s)',
                                '3: Use LED indicators? (T/F/Cue)',
                                '4: Use behavior camera? (T/F)',
                                '5: Param file Title'
                                ],
                                [10,30,30,False,False,'params'])
        if params is None:
            print('Exiting')
            return(False)
        
        #Read params
        trials_per_taste = int(params[0]) #10
        itiMin = int(params[1]) #30, iti
        itiMax = int(params[2]) #30, iti
        useLED = params[3] #0
        useCamera = params[4] #0
        fileTitle = params[5]
        
        useLED = isTrue(useLED)
        useCamera = isTrue(useCamera)
        
        # Get tastes and their spout locations
        bot_pos = ['']*8
        t_list = easygui.multenterbox('Please enter the taste to be used in each spout.',
                                    'Taste List',
                                    ['Spout {}'.format(i+1) for i in range(8)],
                                    values=bot_pos)
        taste_positions = [int(+i) for i in range(len(t_list)) if len(t_list[i]) > 0]
        if t_list is None:
            print('Exiting')
            return(False)
        
        # Setting up spouts for each trial
        tastes = [i for i in t_list if len(i) > 0]
        tasteLabel = ['Position {}: {}'.format(taste_positions[i], tastes[i]) for i in range(len(taste_positions))]

        concs = easygui.multenterbox('Please enter the concentration of each taste.',
                                    'Concentration List',
                                    tastes,
                                    values=['']*len(tastes))

        openTime = easygui.multenterbox('Please enter the open time for each valve.',
                                    'Open Time (sec):',
                                    tasteLabel,
                                    values=[0.01]*len(tastes))
        if openTime is None:
            print('Exiting')
            return(False)

        valveOut = easygui.multenterbox('Please enter the pi GPIO for each valve.',
                                    'GPIO Port:',
                                    tasteLabel,
                                    values=[None]*len(tastes))
        if valveOut is None:
            print('Exiting')
            return(False)

        intanOut = easygui.multenterbox('Please enter the pi GPIO for each Intan input.',
                                    'GPIO Port:',
                                    tasteLabel,
                                    values=[None]*len(tastes))
        if intanOut is None:
            print('Exiting')
            return(False)

        stimList = ['{} {}'.format(tastes[i], concs[i]) for i in range(len(tastes))]

        trial_list = [np.random.choice(taste_positions, size = len(tastes), replace=False) for i in range(trials_per_taste)]
        trial_list = np.concatenate(trial_list)
        
        # Compute and Convert Session Variables
        NTrials = len(tastes)*trials_per_taste
        TubeSeq = trial_list
        IPITimes = [random.randrange(itiMin*1000,itiMax*1000) for trialN in range(NTrials)] if itiMin < itiMax else [itiMin*1000]*NTrials
        version = 'IOC'

        #%% Create Output
        outTitle = "[Trial Parameters]\n"
        outSolutions = f"Solutions={','.join(map(str, stimList))}\n"
        outOpenTime = f"OpenTimes={','.join(map(str, openTime))}\n"
        outValvePin = f"ValvePins={','.join(map(str, valveOut))}\n"
        outIntanPin = f"IntanPins={','.join(map(str, intanOut))}\n"
        outNTrials = f"NumberOfPres={NTrials}\n"
        outTubeSeq = f"TubeSeq={','.join(map(str, TubeSeq))}\n"
        outIPITimes = f"IPITimes={','.join(map(str, [round(trialN*1000) for trialN in IPITimes]))}\n"
        outIPIMin = f"IPImin={round(itiMin*1000)}\n"
        outIPIMax = f"IPImax={round(itiMax*1000)}\n"
        outVersion = f"Version={version}\n"
        outLED = f"UseLED={useLED}\n"
        outCam = f"UseCamera={useCamera}"
        outLines = (outTitle + outSolutions + outOpenTime + outValvePin + outIntanPin + 
                    outNTrials + outTubeSeq + outIPITimes + outIPIMin + outIPIMax + outVersion + outLED + outCam)
        
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
        
        outFile = os.path.normpath(os.path.join(proj_path, f'params/{fileTitle}.txt'))
        
        
        with open(outFile, 'w') as outputFile:
            outputFile.write(outLines)
            print(f'Params saved as {outFile}')
        
        return outFile

def readParameters(paramsFile):
    try:
        with open(paramsFile, 'r') as params:
            paramsData = params.readlines()
    except:
        print("Invalid paramsFile path")
        return(None,None)
    paramsData = [line.rstrip('\n') for line in paramsData]
    paramsData = [line.split('#')[0] for line in paramsData]
    paramsData = [line.split('=') for line in paramsData]
    
    NTrials = int([line[1] for line in paramsData if 'NumberOfPres' in line[0]][0])
    Version = ([line[1] for line in paramsData if 'Version' in line[0]][0])
    Solutions = [line[1].split(',') for line in paramsData if 'Solutions' in line[0]][0]
    if Version != 'IOC':
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
        tasteList =  [Solutions[tubeN-1] for tubeN in TubeSeq]
        concList =  [Concentrations[tubeN-1] for tubeN in TubeSeq]
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

        trialData = pandas.DataFrame({'Trial':range(1,NTrials+1), 'Tube':TubeSeq, 'Conc':concList, 'Stim':tasteList, 'LickTime':LickTime, 'LickCount':LickCount,
                                    'IPI':IPITimes,'MaxWait':MaxWaitTime})    
        return(Version,trialData)
    else:
        OpenTimes = [line[1].split(',') for line in paramsData if 'OpenTimes' in line[0]][0]
        OpenTimes = [float(trialN) for trialN in OpenTimes]
        ValvePins = [line[1].split(',') for line in paramsData if 'ValvePins' in line[0]][0]
        ValvePins = [int(trialN) for trialN in ValvePins]
        IntanPins = [line[1].split(',') for line in paramsData if 'IntanPins' in line[0]][0]
        IntanPins = [int(trialN) for trialN in IntanPins]
        TubeSeq = [line[1].split(',') for line in paramsData if 'TubeSeq' in line[0]][0]
        TubeSeq = [int(trialN) for trialN in TubeSeq]
        IPITimes = [line[1].split(',') for line in paramsData if 'IPITimes' in line[0]][0]
        IPITimes = [int(trialN)/1000 for trialN in IPITimes if len(trialN) != 0]
        IPImin = [int(line[1]) for line in paramsData if 'IPImin' in line[0]][0]
        IPImax = [int(line[1]) for line in paramsData if 'IPImax' in line[0]][0]
        try:
            useLED = [line[1] for line in paramsData if 'UseLED' in line[0]][0]
        except:
            useLED = False
        try:
            useCamera = [line[1] for line in paramsData if 'UseCamera' in line[0]][0]
        except:
            useCamera = False

        tasteList =  [Solutions[tubeN] for tubeN in TubeSeq]
        openList =  [OpenTimes[tubeN] for tubeN in TubeSeq]
        valveList =  [ValvePins[tubeN] for tubeN in TubeSeq]
        intanList =  [IntanPins[tubeN] for tubeN in TubeSeq]
        minList =  [IPImin for tubeN in TubeSeq]
        maxList =  [IPImax for tubeN in TubeSeq]

        #This would be the display for a program where the session is param'd in advance
        #trialData = pandas.DataFrame({'Trial':range(1,NTrials+1), 'Tube':TubeSeq,'Stim':tasteList, 'OpenTime':openList, 'ValvePin':valveList,
        #                            'IntanPin':intanList,'minIPI':minList,'maxIPI':maxList})    
        #This is the display for just giving basic parameters to the IOC program
        trialData = pandas.DataFrame({'Stim':Solutions, 'OpenTime':OpenTimes, 'ValvePin':ValvePins,
                                    'IntanPin':IntanPins,'minIPI':[IPImin]*len(Solutions),'maxIPI':[IPImax]*len(Solutions)})    
        return(Version,trialData)

#%% Run the function
if __name__ == "__main__":
    makeParams()
