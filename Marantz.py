import threading
import telnetlib
import re
import sys

__author__ = 'Josh'


class IP():
    sources = ["TUNER", "DVD", "BD", "TV", "SAT", "SAT/CBL", "MPLAY", "GAME", "AUX1", "NET", "PANDORA", "SIRIUSXM",
               "LASTFM", "FLICKR", "FAVORITES", "IRADIO", "SERVER", "USB/IPOD", "USB", "IPD", "IRP", "FVP"]

    def __init__(self, ip):
        self.ip = ip
        self.timer = None  # threading.Timer(10, self.disconnect)
        self.conn = telnetlib.Telnet()

    def connect(self):
        try:
            print "Testing existing connection...",
            self.conn.write("PING\r")
            print "[CONNECTED]"
            self.reset_timer()
        except:
            print "[DISCONNECTED]"
            print "Connecting...",
            self.conn.open(self.ip, 23, 3)
            print "[CONNECTED]"
            self.start_timer()
        return self.conn

    def disconnect(self):
        print "Disconnecting...",
        self.conn.close()
        print "[DISCONNECTED]"

    def start_timer(self):
        self.timer = threading.Timer(10, self.disconnect)
        self.timer.start()

    def reset_timer(self):
        print "Resetting timer."
        self.timer.cancel()
        self.start_timer()

    def dispatch(self, action, *args, **kwargs):
        dispatcher = {"Power": self.set_power, "GetPower": self.get_power,
                      "Mute": self.set_mute, "GetMute": self.get_mute,
                      "Volume": self.set_volume, "GetVolume": self.get_volume,
                      "Input": self.set_source, "GetInput": self.get_source,
                      "Source": self.set_source, "GetSource": self.get_source,
                      "GetStatus": self.get_status
        }
        try:
            return dispatcher[action](*args, **kwargs)
        except KeyError:
            raise ValueError("Invalid key received. '%s' is not valid." % action)

    def query(self, commands, pattern=None):
        response = {}
        t = self.connect()
        # if we got a single item, let's wrap it in a list to satisfy the loop below
        if type(commands) not in [list, tuple]:
            commands = [commands]
        #loop through each command and build+send+parse it
        for command in commands:
            # if a pattern wasn't supplied, let's look for the standard format
            if command.endswith("?\r"):
                action = command[:-2]  # strip ?\r off: \r counts as one return character
            else:
                action = command
                command += "?\r"  # append the query characters ?\r

            if pattern is None:
                pattern = action+"([a-zA-Z0-9]*)\r"
            #send the command to the AVR
            print "Clearing previous buffer...", t.read_very_eager().encode("string_escape")
            print ("Sending: '%s'" % command).encode('string_escape')
            print ("Looking for: '%s'" % pattern).encode('string_escape')
            t.write(command)
            find = t.expect([pattern], 1)
            if find[1] is None:
                print >> sys.stderr, "[ERROR] Match failed. Trying one more time...Sending command again."
                t.write(command)
                find = t.expect([pattern], 1)
            print "Response:", (find[2]).encode("string_escape")
            matches = find[1]
            response[action] = matches.group(1)
            #reset the pattern for the next run
            pattern = None
            self.reset_timer()
        #t.close()

        return response

    def write_command(self, command):
        t = self.connect()
        t.write(command)
        #t.close()
        self.reset_timer()

    def get_status(self, *args):
        return self.query(["PW", "MU", "SI", "MV"])

    def get_source(self, *args):
        return self.query("SI?\r", "SI([^\r]+)\r")
        # 'SIBD\r@SRC:MM\rSVSOURCE\r'

    def set_source(self, source):
        self.write_command("SI" + source + "\r")
        # TODO: extend this to verify if the source changed to what we wanted
        # 'SIDVD\r@SRC:22\rCVFL 49\rCVFR 56\rCVC 52\rCVSW 43\rCVSL 47\rCVSR 455\rCVSBL 50\rCVSBR 50\rCVSB 50\rCVFHL 50\rCVFHR 50\rMVMAX 98\rMSSTEREO\rSDHDMI\r@INP:4\rSVSOURCE\rDCAUTO\r@DCM:3\rPSDCO OFF\rPSDRC AUTO\r'
        # 'SIBD\r@SRC:MM\rCVFL 49\rCVFR 56\rCVC 54\rCVSW 43\rCVSL 47\rCVSR 455\rCVSBL 50\rCVSBR 50\rCVSB 50\rCVFHL 50\rCVFHR 50\rMVMAX 98\rMSDTS NEO:6 M\rSDHDMI\r@INP:4\rSVSOURCE\rDCAUTO\r@DCM:3\rPSDCO OFF\rPSDRC AUTO\rPSLFE 00\rPSBAS 50\r@TOB:000\rPSTRE 50\r@TOT:000\r'

    def get_mute(self, *args):
        return self.query("MU?\r", "MU([^\r]+)\r")
        # 'MUOFF\r@AMT:1\r'

    def set_mute(self, onoff):
        if type(onoff) is not str:
            raise TypeError("Expecting 'ON' or 'OFF'. Received type: " + type(onoff))
        if onoff.upper() not in ["ON", "OFF"]:
            raise ValueError("Expecting 'ON' or 'OFF'. Received " + onoff)
        self.write_command("MU" + onoff.upper() + "\r")
        # 'MUON\r@AMT:2\r'
        # 'MUOFF\r@AMT:1\r'

    def get_power(self, *args):
        return self.query("PW?\r", "PW([^\r]+)\r")
        # 'PWON\r@PWR:2\r'
        # 'PWSTANDBY\r@PWR:1\r'


    def set_power(self, onoff, *args, **kwargs):
        if type(onoff) is not str:  # and type(onoff) is not unicode
            raise TypeError("Expecting 'ON' or 'OFF'. Received %s of type %s." % (str(onoff), str(type(onoff))))
        if onoff.upper() not in ["ON", "OFF"]:
            raise ValueError("Expecting 'ON' or 'OFF'. Received " + onoff)
        if onoff.upper() == "OFF":
            onoff = "STANDBY"
        self.write_command("PW" + onoff.upper() + "\r")
        # 'ZMOFF\r@PWR:1\rPWSTANDBY\r@PWR:1\r'
        # 'ZMON\r@PWR:2\rPWON\r@PWR:2\r'

    def get_volume(self, *args):
        return self.query("MV?\r", "MV([^\r]+)\r")

    def set_volume(self, updown):
        # TODO: extend this to allow values between 0-98
        if type(updown) is not str:
            raise TypeError("Expecting 'UP' or 'DOWN'. Received type: " + type(updown))
        if updown.upper() not in ["UP", "DOWN"]:
            raise ValueError("Expecting 'UP' or 'DOWN'. Received " + updown)
        self.write_command("MV" + updown.upper() + "\r")
        # MV005\r@VOL:-795\rMVMAX 98\r


    def test(self):
        nr = IP("192.168.1.29")
        nr.get_source()
        nr.get_mute()
        nr.set_source("DVD")
        nr.get_source()
        nr.set_source("BD")
        nr.get_source()
