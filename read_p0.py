import re
import serial
from influxdb import InfluxDBClient
from datetime import datetime

def get_serial() -> serial.Serial:
    ser = serial.Serial()


    ser.baudrate = 115200
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE

    ser.xonxoff = 0
    ser.rtscts = 0
    ser.timeout = 12
    ser.port = "/dev/ttyUSB0"
    ser.close()
    return ser


def grab_raw_info(ser : serial.Serial) -> list:
    dataset = []

    try:
        ser.open()
        checksum_found = False

        while not checksum_found:
            telegram_line = ser.readline()
            
            dataset.append(telegram_line.decode('ascii').strip())

            if re.match(b'(?=!)', telegram_line):
                checksum_found = True
    except Exception as e:
        print("Error reading data:", e)
    finally:
        ser.close()
    return [i for i in dataset if i.find(':')>0]


def make_timestamp(raw_data : list) -> str:
    raw_timestamp = [i.split('(')[-1][:-2] for i in raw_data if i.find('0-0:1.0.0')>-1][0]
    timestamp = datetime.strptime(raw_timestamp, '%y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
    return timestamp
    
def make_fields(raw_data : list) -> dict:
    
    translation = {
     '1-0:1.8.1': 'Total usage night [kWh]',
     '1-0:1.8.2': 'Total usage day [kWh]',
     '1-0:2.8.1': 'Total production night [kWh]',
     '1-0:2.8.2': 'Total production day [kWh]',
     '1-0:1.7.0': 'Current usage [kW]',
     '1-0:2.7.0': 'Current production [kW]',
     '0-1:24.2.1': 'Total gas usage [m3]'
    }

    fields = {translation[i.split('(')[0]] : float(i.split('(')[-1][:-1].split('*')[0])
         for i in raw_data 
         if i.split('(')[0] in translation.keys()}

    return fields


def make_payload(raw_data : list) -> list:

    timestamp = make_timestamp(raw_data)
    fields = make_fields(raw_data)
    
    json_body = [
        {
            "measurement": "energy",

            "time": timestamp,
            "fields": fields
        }
    ]
    return json_body


ser = get_serial()
raw_data = grab_raw_info(ser)
json_body = make_payload(raw_data)
print(json_body)

client = InfluxDBClient('localhost', 8086, 'root', 'root', 'homeautomation')
client.write_points(json_body)
client.close()
