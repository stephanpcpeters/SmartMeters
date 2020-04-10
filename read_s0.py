import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from influxdb import InfluxDBClient

GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.IN) 

def measure_pulses(seconds_to_measure:int) -> int:
    starttime = datetime.now()
    endtime = starttime + timedelta(seconds=seconds_to_measure)

    ticks, signals, previous_state = 0, 0, 0

    while datetime.now() < endtime:
        state = GPIO.input(14)

        if state != previous_state:
            previous_state = state

            if state == 1:
                signals += 1

        ticks += 1

    print("Ran for {0} seconds, at {1:.1f} ticks/sec and found {2} ticks".format(seconds_to_measure, ticks/seconds_to_measure, signals))
    return signals

def measure_kWh(seconds_to_measure:int) -> int:
    pulses_per_kWh = 2000 # pulses / kWh
    seconds_in_hour = 60*60

    number_of_pulses = measure_pulses(seconds_to_measure)

    power = number_of_pulses / pulses_per_kWh * (seconds_in_hour / seconds_to_measure)
    print('This equals a power of {0} kWh'.format(power))
    return power

def push_to_influxdb(power:int) -> None:
    json_body = [{'measurement': 'energy',
                  'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                  'fields': {'Solar panel production [kWh]': power}}]

    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'homeautomation')
    client.write_points(json_body)
    client.close()
    print("Saved to InfluxDB")
    return


power = measure_kWh(120)
push_to_influxdb(power)

