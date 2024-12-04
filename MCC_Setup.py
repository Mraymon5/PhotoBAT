#https://files.digilent.com/manuals/UL-Linux/python/index.html    #Library reference for Linux
#https://files.digilent.com/manuals/Mcculw_WebHelp/ULStart.htm    #library reference for Windows

import sys

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
            self.device = DaqDevice(device_descriptor)
            self.device.connect()
            self.dio_device = self.device.get_dio_device()
        elif sys.platform.startswith('win'):
            self.linux = False
            from mcculw import ul
        else:
            raise OSError("Unsupported platform")
        self.ul = ul
        self.port_type = [ul.DigitalPortType.FIRSTPORTA,
                          ul.DigitalPortType.FIRSTPORTB,
                          ul.DigitalPortType.FIRSTPORTCL,
                          ul.DigitalPortType.FIRSTPORTCH]

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
            if direction == 'input': self.dio_device.d_config_port(self.port_type[port], self.ul.DigitalDirection.INPUT)
            if direction == 'output': self.dio_device.d_config_port(self.port_type[port], self.ul.DigitalDirection.OUTPUT)
        else: #Windows
            if direction == 'input': self.d_config_port(board_num, self.port_type[port], self.ul.DigitalIODirection.IN)
            if direction == 'output': self.d_config_port(board_num, self.port_type[port], self.ul.DigitalIODirection.OUT)

    def d_close_port(self):
        if self.linux: #Linux
            self.device.disconnect()
            self.device.release()

if(0):
    MCC = MCCInterface()
    MCC.d_config_port(0,0,'output')
    MCC.d_out(0,0,0)
    print(MCC.d_in(0,0))
    MCC.d_out(0,0,1)
    print(MCC.d_in(0,0))
    MCC.d_out(0,0,0)
    print(MCC.d_in(0,0))
