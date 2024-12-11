import os
import time
import numpy as np
import pickle
import easygui
import json
import board
import sys
import argparse
import random
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk

#Currently unused modules
import digitalio
import busio
import atexit
import subprocess
import signal
from subprocess import Popen, PIPE
from pathlib import Path

#%% Local pi functions
sys.path.append('/home/test-pi/PhotoBAT/')
from bipolar_class import Motor
from bipolar_class import rotate_dir
from rgbled_class import RGBLed
from turn_motor import *
import CameraControl
import MCC_Setup; MCC = MCC_Setup.MCCInterface()

board_num = 0

if 1:
    def getBit(portType, channel, sensorState = None): #sensor_state
        if sensorState is None:
            sensorState = MCC.d_in(board_num, portType)
        return (sensorState >> channel) & 1

    def setBit(portType, channel, value):
        # Read the current state of the port
        current_state = MCC.d_in(board_num, portType)
        # Set the specific bit without altering others
        if value:
            new_state = current_state | (1 << channel) #set a channel High
        else:
            new_state = current_state & ~(1 << channel) #set a channel Low
        # Write the new state back to the port
        MCC.d_out(board_num, portType, new_state)

    # Function to read in values from params file and save them as int or None
    def intOrNone(value, factor=1):
        try:
            return int(value)*factor # If the value in a givin position is a numeral, convert to int
        except (ValueError, TypeError): # Otherwise return None
            return None

    # Function to allow flexible inputs for True in user-supplied strings
    isTrue = lambda x: str(str(x).lower() in {'1', 'true', 't'})

    # Motor control parameters and functions
    board_num = 0
    last_step_index = {} # Global variable to keep track of the last step index for each motor
    stop_motor = threading.Event()
    motor_stopped = threading.Event()

    shutterChannels = [0, 1, 2, 3]  # Motor 1 on channels A0-A3
    shutterMagChannel = 5 #Mag sensor on channel B5
    shutterInitSteps = -50 #The number of steps from the mag sensor to the "closed" position
    shutterRunSteps = 100 #The number of steps to open/close the shutter
    shutterDir = 1 #The base direction of the shutter
    shutterSpeed = 0.01

    tableChannels = [4, 5, 6, 7]  # Motor 2 on channels A4-A7
    tableMagChannel = 4 #Mag sensor on channel B4
    tableInitSteps = -17 #The number of steps from the mag sensor to the home position
    tableRunSteps = 125 #The number of steps between bottle positions
    tableDir = 0 #The base direction of the table
    tableSpeed = 0.005

    def step_motor(motor_channels, steps, delay=0.01, direction=0):
        global last_step_index
        global stop_motor
        motor_key = tuple(motor_channels)
        # Full-step sequence
        step_sequence = [
            #0b1110,  # Step 0.5
            0b1010,  # Step 1
            #0b1011,  # Step 1.5
            0b1001,  # Step 2
            #0b1101,  # Step 2.5
            0b0101,  # Step 3
            #0b0111,  # Step 3.5
            0b0110,  # Step 4
        ]

        # Reverse the sequence for backward direction
        if (steps < 0):
            steps = abs(steps)
            direction = not direction
        
        if direction:
            step_sequence = step_sequence[::-1]
            
        # Read in the current state of the output to avoid writing over the other motor
        current_state = MCC.d_in(board_num=board_num, port = 0)
        
        # Initialize last step index for the motor if not already set
        if motor_key not in last_step_index:
            last_step_index[motor_key] = 0  # Start at step 0 (step 1 in the sequence)

        # Start from the last step index
        current_step_index = last_step_index[motor_key]
        
        stepped = 0
        while (stepped < steps) and not stop_motor.is_set():
        #for _ in range(steps):
            #if stop_motor.is_set():
            #    break
            print(f'Steps: {stepped}, stop_motor: {stop_motor}')
            # Get the current step from the sequence
            step = step_sequence[current_step_index]

            # Clear the motor's 4 bits using a mask
            mask = ~(0b1111 << motor_channels[0])
            current_state &= mask  # Clears the 4 bits for the motor

            # Set the new 4-bit step sequence shifted to the motor channels
            new_state = current_state | (step << motor_channels[0])

            # Write the updated state to the port
            MCC.d_out(board_num = board_num, port = 0, data = new_state)
            time.sleep(delay)

            # Move to the next step in the sequence
            current_step_index = (current_step_index + 1) % len(step_sequence)
            stepped += 1
        motor_stopped.set()

        # Update the last step index for the motor
        last_step_index[motor_key] = current_step_index
        
        # Set motor to idle
        step = 0b1111
        mask = ~(0b1111 << motor_channels[0]) # Clear the motor's 4 bits using a mask
        current_state &= mask  # Clears the 4 bits for the motor
        new_state = current_state | (step << motor_channels[0]) # Set the new 4-bit step sequence shifted to the motor channels
        MCC.d_out(board_num = board_num, port = 0, data = new_state) # Write the updated state to the port
        stop_motor.clear()
        
    def moveShutter(Open = False, Init = False):
        global stop_motor
        if Init:
            print("Backing up...")
            if getBit(portType = 1, channel = shutterMagChannel):
                step_motor(motor_channels = shutterChannels, steps = 50, direction = shutterDir, delay=shutterSpeed)
            print("Done. Advancing to mag switch...")
            stop_motor.clear()
            motor_thread = threading.Thread(target=step_motor, args=(shutterChannels, 10000, shutterSpeed, not shutterDir))
            motor_thread.start()
            while not getBit(portType = 1, channel = shutterMagChannel):
                time.sleep(0.01)
            stop_motor.set()  # Stop the motor loop
            print(f'Main Loop Stop_Motor: {stop_motor}')
            if motor_thread.is_alive():
                motor_thread.join()
            stop_motor.clear()
            motor_stopped.clear()
            print("Done. Moving to home position...")
            step_motor(motor_channels = shutterChannels, steps = shutterInitSteps, direction = shutterDir)
            print("Done. Shutter initialized.")
        else:
            if Open:
                step_motor(motor_channels = shutterChannels, steps = shutterRunSteps, direction = shutterDir, delay = shutterSpeed)
            else:
                step_motor(motor_channels = shutterChannels, steps = shutterRunSteps, direction = not shutterDir, delay = shutterSpeed)

    def moveTable(movePos = 0, Init = False):
        global stop_motor
        if Init:
            print("Backing up...")
            step_motor(motor_channels = tableChannels, steps = 50, direction = tableDir, delay=tableSpeed)
            print("Done. Advancing to mag switch...")
            stop_motor.clear()
            motor_thread = threading.Thread(target=step_motor, args=(tableChannels, 10000, tableSpeed, not tableDir))
            motor_thread.start()
            while not getBit(portType = 1, channel = tableMagChannel):
                time.sleep(0.01)
            stop_motor.set()  # Stop the mtotor loop
            print(f'Main Loop Stop_Motor: {stop_motor}')
            if motor_thread.is_alive():
                motor_thread.join()
            stop_motor.clear()
            print("Done. Moving to home position...")
            step_motor(motor_channels = tableChannels, steps = tableInitSteps, direction = tableDir)
            print("Done. Table initialized.")
        else:
            if movePos > 0:
                step_motor(motor_channels = tableChannels, steps = movePos*tableRunSteps, direction = tableDir, delay = tableSpeed)
            else:
                step_motor(motor_channels = tableChannels, steps = abs(movePos)*tableRunSteps, direction = not tableDir, delay = tableSpeed)
    # Calibration Gui functions
    # Function to update sensor values
    def update_sensor_display(sensor_labels):
        readSens = MCC.d_in(0, 1)
        lSens = f"Lick Sensor: {getBit(portType=1, channel=7, sensorState=readSens)}"
        sMagSens = f"Shutter Mag: {getBit(portType=1, channel=5, sensorState=readSens)}"
        tMagSens = f"Table Mag: {getBit(portType=1, channel=4, sensorState=readSens)}"
        values = [lSens, sMagSens, tMagSens]
        
        # Update each label with the corresponding sensor value
        for label, value in zip(sensor_labels.values(), values):
            label.config(text=value)
        
        # Schedule the function to run again after 500ms
        root.after(100, update_sensor_display, sensor_labels)

    def update_parameters():
        # Example of retrieving values from the text boxes
        
        global shutterInitSteps; shutterInitSteps = float(sInitEnt.get()) #The number of steps from the mag sensor to the "closed" position
        global shutterRunSteps; shutterRunSteps = float(sRunEnt.get()) #The number of steps to open/close the shutter
        global shutterDir; shutterDir = float(sDirEnt.get()) #The base direction of the shutter
        global shutterSpeed; shutterSpeed = float(sSpdEnt.get())

        global tableInitSteps; tableInitSteps = float(tInitEnt.get()) #The number of steps from the mag sensor to the home position
        global tableRunSteps; tableRunSteps = float(tRunEnt.get()) #The number of steps between bottle positions
        global tableDir; tableDir = float(tDirEnt.get()) #The base direction of the table
        global tableSpeed; tableSpeed = float(tSpdEnt.get())

        print(f"Updated Parameters: shutterInitSteps={shutterInitSteps}, shutterRunSteps={shutterRunSteps}")


    try:
        MCC.d_config_port(board_num = 0, port = 0, direction = 'output')
        MCC.d_out(board_num = 0, port = 0, data = 0b11111111)
        # GUI setup
        root = tk.Tk()
        root.title("Motor and Sensor Calibration")
        MCC.d_config_port(board_num = 0, port = 1, direction = 'input')
        
        # Shutter control section
        shutterFrame = ttk.LabelFrame(root, text="Shutter Control")
        shutterFrame.grid(row=0, column=0, padx=10, pady=10)
        
        tk.Label(shutterFrame, text="Shutter Initial Steps:").grid(row=0, column=0, padx=10, pady=5)
        sInitEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=shutterInitSteps))
        sInitEnt.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Run Steps:").grid(row=1, column=0, padx=10, pady=5)
        sRunEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=shutterRunSteps))
        sRunEnt.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Direction:").grid(row=2, column=0, padx=10, pady=5)
        sDirEnt = tk.Entry(shutterFrame, textvariable=tk.IntVar(value=shutterDir))
        sDirEnt.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(shutterFrame, text="Shutter Step Delay:").grid(row=3, column=0, padx=10, pady=5)
        sSpdEnt = tk.Entry(shutterFrame, textvariable=tk.DoubleVar(value=shutterSpeed))
        sSpdEnt.grid(row=3, column=1, padx=10, pady=5)
        # Create buttons
        tk.Button(shutterFrame, text="Init", command=lambda: moveShutter(Init = True)).grid(row=4, column=0, padx=10, pady=10)
        tk.Button(shutterFrame, text="Open", command=lambda: moveShutter(Open = True)).grid(row=4, column=1, padx=10, pady=10)
        tk.Button(shutterFrame, text="Close", command=lambda: moveShutter(Open = False)).grid(row=4, column=2, padx=10, pady=10)
        
        
        # Table control section
        tableFrame = ttk.LabelFrame(root, text="Table Control")
        tableFrame.grid(row=2, column=0, padx=10, pady=10)

        tk.Label(tableFrame, text="Table Initial Steps:").grid(row=0, column=0, padx=10, pady=5)
        tInitEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=tableInitSteps))
        tInitEnt.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(tableFrame, text="Table Run Steps:").grid(row=1, column=0, padx=10, pady=5)
        tRunEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=tableRunSteps))
        tRunEnt.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(tableFrame, text="Table Direction:").grid(row=2, column=0, padx=10, pady=5)
        tDirEnt = tk.Entry(tableFrame, textvariable=tk.IntVar(value=tableDir))
        tDirEnt.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(tableFrame, text="Table Step Delay:").grid(row=3, column=0, padx=10, pady=5)
        tSpdEnt = tk.Entry(tableFrame, textvariable=tk.DoubleVar(value=tableSpeed))
        tSpdEnt.grid(row=3, column=1, padx=10, pady=5)
        # Create buttons
        tk.Button(tableFrame, text="Init", command=lambda: moveTable(Init = True)).grid(row=4, column=0, padx=10, pady=10)
        tk.Button(tableFrame, text="Next", command=lambda: moveTable(movePos = 1)).grid(row=4, column=1, padx=10, pady=10)
        tk.Button(tableFrame, text="Prev", command=lambda: moveTable(movePos = -1)).grid(row=4, column=2, padx=10, pady=10)
        
        tk.Button(root, text="Update Parameters", command=update_parameters).grid(row=1, column=1, padx=10, pady=10)
        
        # Sensor display section
        sensor_frame = ttk.LabelFrame(root, text="Sensor Readouts")
        sensor_frame.grid(row=0, column=1, padx=10, pady=10)
        
        # Create labels for sensors
        sensor_labels = {
            "Lick Sensor": ttk.Label(sensor_frame, text="Lick Sensor: ---"),
            "Shutter Mag Sensor": ttk.Label(sensor_frame, text="Shutter Mag Sensor: ---"),
            "Table Mag Sensor": ttk.Label(sensor_frame, text="Table Mag Sensor: ---")
        }
        
        # Place each label in the grid
        for i, (sensor_name, label) in enumerate(sensor_labels.items()):
            label.grid(row=i, column=0, padx=5, pady=5)
        
        # Start updating the sensor display
        update_sensor_display(sensor_labels)
        
        root.mainloop()
    finally:
        MCC.d_close_port()
