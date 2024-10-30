#!/usr/bin/env python3
#
# $Id: bipolar_class.py,v 1.6 2023/05/23 09:20:03 bob Exp $
# Raspberry Pi bipolar Stepper Motor Driver Class
# Hardware Nema17 12 Volt Stepper High Torque Motor
# Gear Reduction Ratio: 1/64 
# Uses the A4988 H-bridge circuit driver board.
#
# Author : Jian-You Lin
# Site   : jianyoulin@gmail.com
#

import numpy as np

# # assuming total spout + rest site is 8
# tot_pos = 8 # 4 spouts and 4 resting positions

def get_cw_steps(cur_pos, dest_pos, tot_pos = None):
    """ count number of steps needed to the destination in clockwise direction"""
    seq = np.arange(cur_pos, cur_pos+tot_pos)
    seq[seq > tot_pos] = seq[seq > tot_pos] - tot_pos
#    print(seq)
    steps_to_dest = np.where(seq == dest_pos)[0] - \
                    np.where(seq == cur_pos)[0]
    return int(steps_to_dest)

def get_ccw_steps(cur_pos, dest_pos, tot_pos = None):
    """ count number of steps needed to the destination in counter-clockwise direction"""
    seq = np.arange(cur_pos+tot_pos, cur_pos, -1)
    seq[seq > tot_pos] = seq[seq > tot_pos] - tot_pos
#    print(seq)
    steps_to_dest = np.where(seq == dest_pos)[0] - \
                    np.where(seq == cur_pos)[0]
    return int(steps_to_dest)

def rotate_dir(cur_pos, dest_pos, tot_pos = 8):
    """determine the steps and rotation direction"""
    cw_steps = get_cw_steps(cur_pos, dest_pos, tot_pos = tot_pos)
    ccw_steps = get_ccw_steps(cur_pos, dest_pos, tot_pos = tot_pos)
#    print(f'cw_steps={cw_steps}; ccw_steps={ccw_steps}')
    if cw_steps <= ccw_steps:
        return 1, cw_steps 
    else:
        return -1, ccw_steps 

# for i in range(1):
#     trial_pos_list = np.random.choice([2, 4, 6, 8], size=4, replace=False)

#     init_rest_pos, trial1_lick_pos = 1, trial_pos_list[0]
#     cur_pos, dest_pos = init_rest_pos, trial1_lick_pos
#     for t in range(len(trial_pos_list)): #, trial in enumerate([4, 8, 2, 6]):

#         print(f'Trial {t}')
#         print(f'from {cur_pos} to {dest_pos} (rest to lick)')
        
#         # from rest to lick spout (cur_rest, lick_spout)
#         direction, steps = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
#         rotate = 'Clockwise' if direction == 1 else 'CounterClockwise'
#         print(rotate + f' destination {dest_pos}')
#         # define next cur_ and dest_pos
#         if t < len(trial_pos_list) - 1:
#             rest_dir, _ = rotate_dir(trial_pos_list[t], trial_pos_list[t+1], tot_pos = 8)
#         else:
#             rest_dir = -1
#         cur_pos = trial_pos_list[t]
#         dest_pos = cur_pos + rest_dir
#         dest_pos = dest_pos if dest_pos<=8 else dest_pos-8
#         print(f'from {cur_pos} to {dest_pos} (lick to rest)')

#         # from lick spout to rest position (cur_lick, next_lick)
#         direction, _ = rotate_dir(cur_pos, dest_pos, tot_pos = 8)
#         rotate = 'Clockwise' if direction == 1 else 'CounterClockwise'
#         print(rotate)
#         # define next cur_ and dest_pos
#         if t < len(trial_pos_list) - 1:
#             cur_pos, dest_pos = dest_pos, trial_pos_list[t+1]
#         else:
#             pass
#         print('*********************************')
    

