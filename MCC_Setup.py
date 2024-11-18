import sys

class MCCInterface:
    def __init__(self):
        if sys.platform == 'linux':
            from uldaq import DaqDevice
            import uldaq as ul
            self.device = DaqDevice()
            self.dio_device = self.device.get_dio_device()
        elif sys.platform == 'win32':
            from mcculw import ul
        self.port_type = [ul.DigitalPortType.FIRSTPORTA,
                          ul.DigitalPortType.FIRSTPORTB,
                          ul.DigitalPortType.FIRSTPORTCL,
                          ul.DigitalPortType.FIRSTPORTCH]
        self.ul = ul

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
        if sys.platform == 'linux':
            return self.dio_device.d_in(self.port_type[port])
        elif sys.platform == 'win32':
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
        if sys.platform == 'linux':
            self.dio_device.d_out(self.port_type[port], data)
        elif sys.platform == 'win32':
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
        if sys.platform == 'linux':
            if direction == 'input': self.dio_device.d_config_port(self.port_type[port], self.ul.Direction.OUTPUT)
            if direction == 'output': self.dio_device.d_config_port(self.port_type[port], self.ul.Direction.INPUT)
        elif sys.platform == 'win32':
            if direction == 'input': self.d_config_port(board_num, self.port_type[port], self.ul.DigitalIODirection.OUT)
            if direction == 'output': self.d_config_port(board_num, self.port_type[port], self.ul.DigitalIODirection.IN)
        

mcc = MCCInterface()
result = mcc.d_in(board_num = 0, port = 0)
