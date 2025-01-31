import os
import sys
import time
import easygui
import atexit
import warnings
try:
    import RPi.GPIO as GPIO
    from bipolar_class import Motor
except:
    print('Could not import Pi-Specific Modules')

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
    
    rigParams = {'tableTotalSteps':tableTotalSteps, 'tableTotalPositions':tableTotalPositions, 'tableStepMode':tableStepMode, 'tableInitSteps':tableInitSteps, 'tableSpeed':tableSpeed,
                 'stepPin':stepPin, 'directionPin':directionPin, 'enablePin':enablePin, 'msPins':msPins, 'hallPin':hallPin, 'lickBeamPin':lickBeamPin,
                 'laserPin':laserPin, 'lickLEDPin':lickLEDPin, 'cueLEDPins':cueLEDPins, 'intanBeamPin':intanBeamPin, 'intanTrialPin':intanTrialPin, 'intanSpoutPins':intanSpoutPins}
    
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
               rotate='clockwise', he_inport = hallPin, adjust_steps=initSteps): 
    motora = Motor(step,direction,enable,ms1,ms2,ms3)
    motora.init()
    revolution = motora.setStepSize(stepMode)
    print(revolution)
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
            motora.turn(1, Motor.CLOCKWISE)
        elif rotate == 'anticlockwise':
            motora.turn(1, Motor.ANTICLOCKWISE)
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
    steps360 = motora.setStepSize(stepMode) #TODO 01-30-25
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
    

