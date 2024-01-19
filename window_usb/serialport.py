import sys
import time
import serial
import serial.tools.list_ports as stl

def list_serialports(vid = None, pid = None):
    info_list = []

    def __is_port(port):
        if vid == None and pid == None:
            return True
        elif vid == None:
            return (port.pid == vid)
        elif pid == None:
            return (port.pid == pid)
        return (port.vid == vid and port.pid == pid)
    ports = [port for port in stl.comports() if __is_port(port)]
    for port in ports:
        info_list.append(port.device)

    if sys.platform.startswith("win"):
        from window_usb.winusb import list_winusb_paths
        path_list = list_winusb_paths()
        for index, value in enumerate(path_list):
            info_list.append(value)

    return info_list

class SerialPort():
    SERIAL_MODE_COMPORT = 1
    SERIAL_WINUSB = 2

    def __init__(self, port=None, baudrate=921600, timeout=0.2, write_timeout=None):
        self.type = self.SERIAL_MODE_COMPORT
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._write_timeout = write_timeout

        self.serial_port = None
        self._is_open = False

        if self._port is not None:
            self.open(self._port)

    def open(self, port):
        self._port = port

        if sys.platform.startswith("win"):
            from window_usb.winusb import WinUsbComPort, list_winusb_paths
            if port in list_winusb_paths():
                self.type = self.SERIAL_WINUSB
                winusb = WinUsbComPort(path=self._port, baudrate=self._baudrate, timeout=self._timeout)
                self.serial_port = winusb
            else:
                ser = serial.Serial(port=self._port, baudrate=self._baudrate, timeout=self._timeout, write_timeout=self._write_timeout, exclusive=True)
                self.serial_port = ser
        else:
            ser = serial.Serial(port=self._port, baudrate=self._baudrate, timeout=self._timeout, write_timeout=self._write_timeout, exclusive=True)
            self.serial_port = ser

        self.is_open = True

    def close(self):
        if self.is_open:
            self.serial_port.close()

    def write(self, data):
        if not self.is_open:
            raise Exception("serialport is not opened")
        if type(data) is str:
            data = data.encode("utf8")
        self.serial_port.write(data)

    def read(self, size=1):
        if not self.is_open:
            raise Exception("serialport is not opened")
        if size == None and self.type == self.SERIAL_MODE_COMPORT:
            size = 1
        return self.serial_port.read(size)

    def read_until(self, expected=b"\x0A", size=None):
        if not self.is_open:
            raise Exception("serialport is not opened")

        lenterm = len(expected)
        line = bytearray()
        timeout = self.Timeout(self._timeout)
        while True:
            c = self.read(1)
            if c:
                line += c
                if line[-lenterm:] == expected:
                    break
                if size is not None and len(line) >= size:
                    break
            else:
                break
            if timeout.expired():
                break
        return bytes(line)

    def read_all(self):
        if not self.is_open:
            raise Exception("serialport is not opened")
        return self.serial_port.read_all()

    def flush(self):
        if not self.is_open:
            raise Exception("serialport is not opened")
        self.serial_port.flush()

    def flushInput(self):
        if not self.is_open:
            raise Exception("serialport is not opened")
        self.serial_port.flushInput()

    def flushOutput(self):
        if not self.is_open:
            raise Exception("serialport is not opened")
        self.serial_port.flushOutput()

    def setDTR(self, state):
        if not self.is_open:
            raise Exception("serialport is not opened")
        self.serial_port.setDTR(state)

    def setRTS(self, state):
        if not self.is_open:
            raise Exception("serialport is not opened")
        self.serial_port.setRTS(state)

    def inWaiting(self):
        if not self.is_open:
            raise Exception("serialport is not opened")

        waiting = None
        if self.type == self.SERIAL_MODE_COMPORT:
            waiting = self.serial_port.inWaiting()
        return waiting

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value
        self.serial_port.port = value

    @property
    def baudrate(self):
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value):
        self._baudrate = value
        self.serial_port.baudrate = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        self.serial_port.timeout = value

    @property
    def write_timeout(self):
        return self._write_timeout

    @write_timeout.setter
    def write_timeout(self, value):
        self._write_timeout = value
        self.serial_port.write_timeout = value

    @property
    def dtr(self):
        if self.type == self.SERIAL_MODE_COMPORT:
            return self.serial_port.dtr
        else:
            return False

    class Timeout(object):
        """\
        Abstraction for timeout operations. Using time.monotonic() if available
        or time.time() in all other cases.

        The class can also be initialized with 0 or None, in order to support
        non-blocking and fully blocking I/O operations. The attributes
        is_non_blocking and is_infinite are set accordingly.
        """
        if hasattr(time, 'monotonic'):
            # Timeout implementation with time.monotonic(). This function is only
            # supported by Python 3.3 and above. It returns a time in seconds
            # (float) just as time.time(), but is not affected by system clock
            # adjustments.
            TIME = time.monotonic
        else:
            # Timeout implementation with time.time(). This is compatible with all
            # Python versions but has issues if the clock is adjusted while the
            # timeout is running.
            TIME = time.time

        def __init__(self, duration):
            """Initialize a timeout with given duration"""
            self.is_infinite = (duration is None)
            self.is_non_blocking = (duration == 0)
            self.duration = duration
            if duration is not None:
                self.target_time = self.TIME() + duration
            else:
                self.target_time = None

        def expired(self):
            """Return a boolean, telling if the timeout has expired"""
            return self.target_time is not None and self.time_left() <= 0

        def time_left(self):
            """Return how many seconds are left until the timeout expires"""
            if self.is_non_blocking:
                return 0
            elif self.is_infinite:
                return None
            else:
                delta = self.target_time - self.TIME()
                if delta > self.duration:
                    # clock jumped, recalculate
                    self.target_time = self.TIME() + self.duration
                    return self.duration
                else:
                    return max(0, delta)

        def restart(self, duration):
            """\
            Restart a timeout, only supported if a timeout was already set up
            before.
            """
            self.duration = duration
            self.target_time = self.TIME() + duration

# main
if __name__ == "__main__":
    stop = False

    def handle_received(serialport):
        global stop

        while not stop:
            init = time.time()
            recv = serialport.read_until(b"}")
            dt = time.time() - init
            if recv == None:
                print("disconnected")
                stop = True
                break

            print(f"dt: {int(dt * 1000.0)}ms - {recv}")
            time.sleep(0.001)

        serialport.close()

    import threading
    info_list = list_serialports()

    if not info_list:
        raise Exception("No device is connected")

    serialport = SerialPort(info_list[0])
    threading.Thread(target=handle_received, daemon=True, args=(serialport, )).start()

    print("To exit the program, enter 'exit'.")
    while not stop:
        input_data = input()

        if input_data == "exit":
            stop = True
            break

    serialport.close()