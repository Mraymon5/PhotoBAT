#https://files.digilent.com/manuals/UL-Linux/python/index.html    #Library reference for Linux
#https://files.digilent.com/manuals/Mcculw_WebHelp/ULStart.htm    #library reference for Windows

import sys
import threading
import os
import time

#%% MCC Card Interface Functions
class MCCInterface:
    def __init__(self):
        if sys.platform.startswith('linux'):
            self.linux = True
            from uldaq import DaqDevice
            import uldaq as ul
            devices = ul.get_daq_device_inventory(ul.InterfaceType.ANY)
            # Ensure there's at least one device found
            if not devices:
                print("No DAQ devices found!")
            else:
                # Get the first device's descriptor
                device_descriptor = devices[0]  # Assuming the first device is what you want to use
            self.device = DaqDevice(device_descriptor) #TODO this is maybe part of a problem
            self.device.connect()
            self.dio_device = self.device.get_dio_device()
            self.ul = ul
            self.port_type = [ul.DigitalPortType.FIRSTPORTA,
                            ul.DigitalPortType.FIRSTPORTB,
                            ul.DigitalPortType.FIRSTPORTCL,
                            ul.DigitalPortType.FIRSTPORTCH]
        elif sys.platform.startswith('win'):
            self.linux = False
            from mcculw import ul
            from mcculw.enums import DigitalIODirection
            from mcculw.enums import DigitalPortType
            self.ul = ul
            self.Dir = DigitalIODirection
            self.port_type = [DigitalPortType.FIRSTPORTA,
                              DigitalPortType.FIRSTPORTB,
                              DigitalPortType.FIRSTPORTCL,
                              DigitalPortType.FIRSTPORTCH]

        else:
            raise OSError("Unsupported platform")

    def d_in(self, board_num, port):
        """ 
        d_in is used to read a byte (typically 8 bits) from the specified port of the MCC, reading the state of all channels on that port
        
        Parameters
        ----------
        board_num : int
            The address of the MCC board to be used. Almost certainly 0.
        port : int
            The address of the port to be read. 0=A, 1=B, 2=CL, 3=CH
        
        Returns
        -------
        A byte containing the state of all channels on the target port
        """
        if self.linux: #Linux
            return self.dio_device.d_in(self.port_type[port])
        else: #Windows
            return self.ul.d_in(board_num, self.port_type[port])

    def d_out(self, board_num, port, data):
        """ 
        d_out is used to set a byte (typically 8 bits) to the specified port of the MCC, writing the state of all channels on that port
        
        Parameters
        ----------
        board_num : int
            The address of the MCC board to be used. Almost certainly 0.
        port : int
            The address of the port to be written. 0=A, 1=B, 2=CL, 3=CH
        data
        
        Returns
        -------
        Nothing
        """
        if self.linux: #Linux
            self.dio_device.d_out(self.port_type[port], data)
        else: #Windows
            self.ul.d_out(board_num, self.port_type[port], data)
        
    def d_config_port(self, board_num, port, direction):
        """ 
        Configures the specified port for input or output.
        
        Parameters
        ----------
        board_num : int
            The address of the MCC board to be used. Almost certainly 0.
        port : int
            The address of the port to configure. 0=A, 1=B, 2=CL, 3=CH
        direction : str ['input','output']
            The direction to set the port; 'input' for reading in data, 'output' for writing data
        
        Returns
        -------
        Nothing
        """
        if self.linux: #Linux
            if direction == 'input':
                self.dio_device.d_config_port(self.port_type[port], self.ul.DigitalDirection.INPUT)
            elif direction == 'output':
                self.dio_device.d_config_port(self.port_type[port], self.ul.DigitalDirection.OUTPUT)
            else:
                print("Unacceptable direction argument; use 'input' or 'output'")
        else: #Windows
            if direction == 'input':
                self.ul.d_config_port(board_num, self.port_type[port], self.Dir.IN)
            elif direction == 'output':
                self.ul.d_config_port(board_num, self.port_type[port], self.Dir.OUT)
            else:
                print("Unacceptable direction argument; use 'input' or 'output'")

    def d_close_port(self):
        if self.linux: #Linux
            self.device.disconnect()
            self.device.release()
            
    def getBit(self, portType, channel, sensorState = None, board_num = 0): #sensor_state
        if sensorState is None:
            sensorState = self.d_in(board_num, portType)
        return (sensorState >> channel) & 1

    def setBit(self, portType, channel, value, board_num = 0):
        # Read the current state of the port
        current_state = self.d_in(board_num, portType)
        # Set the specific bit without altering others
        if value:
            new_state = current_state | (1 << channel) #set a channel High
        else:
            new_state = current_state & ~(1 << channel) #set a channel Low
        # Write the new state back to the port
        self.d_out(board_num, portType, new_state)


#%% Davis Rig Control Functions
class DavRun:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.params_path = os.path.join(script_dir, 'MCC_params.txt')
        self.MCC = MCCInterface()
        
        with open(self.params_path, 'r') as params:
            paramsData = params.readlines()
        paramsData = [line.rstrip('\n') for line in paramsData]
        paramsData = [line.split('#')[0] for line in paramsData]
        paramsData = [line.split('=') for line in paramsData]
        
        # Settings imported from device parameters
        self.boardNum = int([line[1] for line in paramsData if 'boardNum' in line[0]][0])
        self.shutterInitSteps = round(float([line[1] for line in paramsData if 'shutterInitSteps' in line[0]][0]))
        self.shutterRunSteps = int([line[1] for line in paramsData if 'shutterRunSteps' in line[0]][0])
        self.shutterDir = int([line[1] for line in paramsData if 'shutterDir' in line[0]][0])
        self.shutterSpeed = float([line[1] for line in paramsData if 'shutterSpeed' in line[0]][0])
        self.tableInitSteps = round(float([line[1] for line in paramsData if 'tableInitSteps' in line[0]][0]))
        self.tableRunSteps = int([line[1] for line in paramsData if 'tableRunSteps' in line[0]][0])
        self.tableDir = int([line[1] for line in paramsData if 'tableDir' in line[0]][0])
        self.tableSpeed = float([line[1] for line in paramsData if 'tableSpeed' in line[0]][0])

        # Static settings
        self.last_step_index = {} # Global variable to keep track of the last step index for each motor
        self.stop_motor = threading.Event()
        self.motor_stopped = threading.Event()
        self.shutterChannels = [0, 1, 2, 3]  # Motor 1 on channels A0-A3
        self.shutterMagChannel = 5 #Mag sensor on channel B5
        self.tableChannels = [4, 5, 6, 7]  # Motor 2 on channels A4-A7
        self.tableMagChannel = 4 #Mag sensor on channel B4
        self.lickSensor = [1, 7] # setup input for beam break detection, port B, channel 7

    def step_motor(self, motor_channels, steps, delay=0.01, direction=0):
        #global last_step_index
        #global stop_motor
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
        current_state = self.MCC.d_in(board_num=self.boardNum, port = 0)
        
        # Initialize last step index for the motor if not already set
        if motor_key not in self.last_step_index:
            self.last_step_index[motor_key] = 0  # Start at step 0 (step 1 in the sequence)

        # Start from the last step index
        current_step_index = self.last_step_index[motor_key]
        
        stepped = 0
        while (stepped < steps) and not self.stop_motor.is_set():
        #for _ in range(steps):
            #if stop_motor.is_set(): #Redundant check of stop_motor
            #    break
            #print(f'Steps: {stepped}, stop_motor: {stop_motor}') #diagnostic
            # Get the current step from the sequence
            step = step_sequence[current_step_index]

            # Clear the motor's 4 bits using a mask
            mask = ~(0b1111 << motor_channels[0])
            current_state &= mask  # Clears the 4 bits for the motor

            # Set the new 4-bit step sequence shifted to the motor channels
            new_state = current_state | (step << motor_channels[0])

            # Write the updated state to the port
            self.MCC.d_out(board_num = self.boardNum, port = 0, data = new_state)
            time.sleep(delay)

            # Move to the next step in the sequence
            current_step_index = (current_step_index + 1) % len(step_sequence)
            stepped += 1
        self.motor_stopped.set()

        # Update the last step index for the motor
        self.last_step_index[motor_key] = current_step_index
        
        # Set motor to idle
        step = 0b1111
        mask = ~(0b1111 << motor_channels[0]) # Clear the motor's 4 bits using a mask
        current_state &= mask  # Clears the 4 bits for the motor
        new_state = current_state | (step << motor_channels[0]) # Set the new 4-bit step sequence shifted to the motor channels
        self.MCC.d_out(board_num = self.boardNum, port = 0, data = new_state) # Write the updated state to the port
        self.stop_motor.clear()
        
    def moveShutter(self, Open = False, Init = False):
        #global stop_motor
        if Init:
            print("Backing up...")
            if self.MCC.getBit(portType = 1, channel = self.shutterMagChannel):
                self.step_motor(motor_channels = self.shutterChannels, steps = 50, direction = self.shutterDir, delay = self.shutterSpeed)
            print("Done. Advancing to mag switch...")
            self.stop_motor.clear()
            motor_thread = threading.Thread(target= self.step_motor, args=(self.shutterChannels, 10000, self.shutterSpeed, not self.shutterDir))
            motor_thread.start()
            while not self.MCC.getBit(portType = 1, channel = self.shutterMagChannel):
                time.sleep(0.01)
            self.stop_motor.set()  # Stop the motor loop
            print(f'Main Loop Stop_Motor: {self.stop_motor}')
            if motor_thread.is_alive():
                motor_thread.join()
            self.stop_motor.clear()
            self.motor_stopped.clear()
            print("Done. Moving to home position...")
            self.step_motor(motor_channels = self.shutterChannels, steps = self.shutterInitSteps, direction = self.shutterDir)
            print("Done. Shutter initialized.")
        else:
            if Open:
                self.step_motor(motor_channels = self.shutterChannels, steps = self.shutterRunSteps, direction = self.shutterDir, delay = self.shutterSpeed)
            else:
                self.step_motor(motor_channels = self.shutterChannels, steps = self.shutterRunSteps, direction = not self.shutterDir, delay = self.shutterSpeed)

    def moveTable(self, movePos = 0, Init = False):
        global stop_motor
        if Init:
            print("Backing up...")
            self.step_motor(motor_channels = self.tableChannels, steps = 50, direction = self.tableDir, delay = self.tableSpeed)
            print("Done. Advancing to mag switch...")
            self.stop_motor.clear()
            motor_thread = threading.Thread(target=self.step_motor, args=(self.tableChannels, 10000, self.tableSpeed, not self.tableDir))
            motor_thread.start()
            while not self.MCC.getBit(portType = 1, channel = self.tableMagChannel):
                time.sleep(0.01)
            self.stop_motor.set()  # Stop the mtotor loop
            print(f'Main Loop Stop_Motor: {stop_motor}')
            if motor_thread.is_alive():
                motor_thread.join()
            self.stop_motor.clear()
            print("Done. Moving to home position...")
            self.step_motor(motor_channels = self.tableChannels, steps = self.tableInitSteps, direction = self.tableDir)
            print("Done. Table initialized.")
        else:
            if movePos > 0:
                self.step_motor(motor_channels = self.tableChannels, steps = movePos*self.tableRunSteps, direction = self.tableDir, delay = self.tableSpeed)
            else:
                self.step_motor(motor_channels = self.tableChannels, steps = abs(movePos)*self.tableRunSteps, direction = not self.tableDir, delay = self.tableSpeed)



if(0):
    MCC = MCCInterface()
    MCC.d_config_port(0,0,'output')
    MCC.d_out(0,0,0)
    print(MCC.d_in(0,0))
    MCC.d_out(0,0,1)
    print(MCC.d_in(0,0))
    MCC.d_out(0,0,0)
    print(MCC.d_in(0,0))
