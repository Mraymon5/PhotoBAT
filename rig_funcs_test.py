import sys
import time
import RPi.GPIO as GPIO
import easygui
import atexit
from bipolar_class import Motor

# 40 pin header for newer Raspberry Pi's  (BPhysicals location, BCM locations)
board_nums = [38,40,22,12,10,8]
BCM_nums = [24,23,20,18,15,14]
step, direction, enable, ms1, ms2, ms3 = BCM_nums
# step = 38 #21
# direction = 40 #20
# enable = 22 #25     # Not required - leave unconnected
# ms1 = 12 #18
# ms2 = 10 #15
# ms3 = 8 #14

hall_e = 16 #11

def turn_clockwise(step,direction,enable,ms1,ms2,ms3, degree=45, rotate='clockwise'):
    motora = Motor(step,direction,enable,ms1,ms2,ms3)
    motora.init()
    
    #revolution = motora.setStepSize(Motor.EIGHTH)
    #revolution = motora.setStepSize(Motor.SIXTEENTH)
    revolution = motora.setStepSize(Motor.HALF)
    #revolution = motora.setStepSize(Motor.FULL)


    print(revolution)
    rotate_pt = int(360/degree)
    if rotate == 'clockwise':
        motora.turn(revolution/rotate_pt, Motor.CLOCKWISE)
    elif rotate == 'anticlockwise':
        motora.turn(revolution/rotate_pt, Motor.ANTICLOCKWISE)
    motora.reset()

def detect_magnet(he_inport = hall_e, wait = 0.5):
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
    
def align_zero(step,direction,enable,ms1,ms2,ms3, rotate='clockwise', he_inport = None, adjust_steps=None): 
    motora = Motor(step,direction,enable,ms1,ms2,ms3)
    motora.init()
    revolution = motora.setStepSize(Motor.SIXTEENTH)
    print(revolution)
    inport = he_inport
    GPIO.setup(inport, GPIO.IN)
    n = 0 # stop the motor is 
    
    while GPIO.input(inport) and n < revolution:
        if rotate == 'clockwise':
            motora.turn(1, Motor.CLOCKWISE)
        elif rotate == 'anticlockwise':
            motora.turn(1, Motor.ANTICLOCKWISE)
            n = n + 1
        time.sleep(0.0007)
    
    if rotate == 'clockwise':
        motora.turn(adjust_steps, Motor.CLOCKWISE)
    elif rotate == 'anticlockwise':
        motora.turn(adjust_steps, Motor.ANTICLOCKWISE)

    motora.reset()
    if  n == revolution:
        print('Hall effecty sensor is NOT aligned to magnet~ Please adjust')
        
    print('Align to initial position!')

def align_zero1(step,direction,enable,ms1,ms2,ms3, he_inport = None, adjust_steps=None):
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    # rotate motor to move spout outside licking hole
    revolution = motora.setStepSize(Motor.SIXTEENTH)
    cur_time = time.time()
    
    motora.home(he_pin = he_inport, adjust_steps=adjust_steps)
    motora.reset()
    print('Please check if the Motor aligned to initial position!')

def fine_align(step,direction,enable,ms1,ms2,ms3, adjust_steps=None, stay=False):
    motora = Motor(step, direction, enable, ms1, ms2, ms3)
    motora.init()
    # rotate motor to move spout outside licking hole
    
    turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                   degree=45, rotate='anticlockwise')
    
    while True:
        rotate_degrees = easygui.multenterbox('Fine Adjustment of initial spout position',
                              '# of Rotating Degrees (integer number)',
                              ['[0]Number of rotating degrees (>0:colockwise; <0:counter-clockwise',
                              ],
                              [1])
        rotate_deg = int(rotate_degrees[0])
        #print(rotate_deg)
        if rotate_deg != 0:
            if rotate_deg > 0:
                turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=rotate_deg, rotate='clockwise')
            elif rotate_deg < 0:
                turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=-rotate_deg, rotate='anticlockwise')
        else:
            break
            
    if not stay:
        turn_clockwise(step,direction,enable,ms1,ms2,ms3,
                       degree=45, rotate='clockwise')
    motora.reset()
