# Usage Instructions

1. Navigate to the directory containining the Marantz.py file
1. Open the Python Shell
1. Import the Marantz library
1. Instantiate a copy of the IP (control) class
1. Issue commands

**Example**

        import Marantz
        # setup the AVR object using your AVR IP
        avr = Marantz.IP("192.168.1.XX") # replace with your AVR IP
        # test connectivity
        avr.connect() # if you get an error, double check the IP
        # send a command
        avr.get_source()

Note: The `connect()` method does not need to be explicitly called. Each command should check its own connectivity.