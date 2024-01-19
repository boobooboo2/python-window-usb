from window_usb.serialport import SerialPort, list_serialports
import threading
import time

serial_port = None
stop_signal = False

def handle_received(self):
    while not stop_signal:
        if not serial_port.is_open:
            stop_signal = True
            break
        
        print(serial_port.read())
        time.sleep(0.01)

if __name__== '__main__':
    port_list = list_serialports()

    if len(port_list) == 0:
        print("Not found ports")
        exit()
    elif len(port_list) == 1:
        port = port_list[0]
    else:
        print("scan.....")
        for index, name in enumerate(port_list):
            print(index, name)
        print("select: ", end="")

        input_data = input()
        index = int(input_data)

        port = port_list[index]

    serial_port = SerialPort(port=port, baudrate=921600, timeout=0.1, write_timeout=0)

    if serial_port is None:
        exit()

    stop_signal = False
    threading.Thread(target=handle_received, daemon=True).start()
    
    while stop_signal:
        input_data = input()
        serial_port.write(input_data)