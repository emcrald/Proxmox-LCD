import serial
import time
import subprocess
import psutil
import socket
import netifaces
import datetime
import os

def get_ip():
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        if iface == 'lo':
            continue
        try:
            addr = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
            if addr and not addr.startswith("127."):
                return addr
        except (KeyError, IndexError):
            continue
    return "IP not found"

def get_cpu_temp():
    try:
        temp = subprocess.getoutput("cat /sys/class/thermal/thermal_zone0/temp")
        return f"{int(temp)/1000:.1f}C" if temp.isdigit() else "N/A"
    except:
        return "Temp: N/A"

def get_uptime():
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
        return uptime_str.split('.')[0]
    except:
        return "Unknown"

def format_bytes(bytes_val):
    gb = bytes_val / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    mb = bytes_val / (1024 ** 2)
    return f"{mb:.0f} MB"

def get_network_stats():
    try:
        net_io = psutil.net_io_counters()
        sent = format_bytes(net_io.bytes_sent)
        recv = format_bytes(net_io.bytes_recv)
        return f"Up: {sent}", f"Dn: {recv}"
    except:
        return "Net:", "Error"

def get_stats():
    ip = get_ip()
    cpu = psutil.cpu_percent()
    temp = get_cpu_temp()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = get_uptime()
    net_up, net_down = get_network_stats()

    return [
        ("IP Address:", ip),
        ("CPU Usage:", f"{cpu}%"),
        ("CPU Temp:", temp),
        ("RAM Used:", f"{ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB"),
        ("Disk Used:", f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB"),
        ("Uptime:", uptime),
        (net_up, net_down)
    ]

# Your Arduino's serial device
serial_device = '/dev/arduino-lcd'

ser = serial.Serial(serial_device, 9600)
time.sleep(2)

while True:
    for line1, line2 in get_stats():
        line = f"{line1}|{line2}\n"
        ser.write(line.encode())
        time.sleep(4)