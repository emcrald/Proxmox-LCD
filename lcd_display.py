import serial
import time
import psutil
import socket
import netifaces
import datetime
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === CONFIG ===
PROXMOX_HOST = "https://192.168.0.125:8006" # Your Proxmox host IP
USERNAME = "root@pam"
PASSWORD = "your_password"  # Your Proxmox password
NODE_NAME = "proxmox"  # Run `pvesh get /nodes` to get this
VERIFY_SSL = False
SERIAL_PORT = "/dev/arduino-lcd" # Your serial port for the arduino

session = requests.Session()
session.verify = VERIFY_SSL

API_TOKEN_ID = "root@pam!lcdstats"  # Your full user + token ID
API_TOKEN_SECRET = "0154b0ba-8424-4145-a7fc-245528e3cda9"  # The long token string

def get_ip():
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        if iface == 'lo':
            continue
        try:
            addr = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
            if addr and not addr.startswith("127."):
                return addr
        except:
            continue
    return "IP not found"

def get_cpu_temp():
    try:
        temp = subprocess.getoutput("cat /sys/class/thermal/thermal_zone0/temp")
        return f"{int(temp)/1000:.1f}C" if temp.isdigit() else "N/A"
    except:
        return "N/A"

def get_uptime():
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        return str(datetime.timedelta(seconds=int(uptime_seconds))).split('.')[0]
    except:
        return "Unknown"

def format_bytes(bytes_val):
    gb = bytes_val / (1024 ** 3)
    return f"{gb:.1f} GB"

def get_network_stats():
    try:
        net_io = psutil.net_io_counters()
        sent = format_bytes(net_io.bytes_sent)
        recv = format_bytes(net_io.bytes_recv)
        return f"Up: {sent}", f"Dn: {recv}"
    except:
        return "Net:", "Error"

def get_proxmox_stats():
    headers = {
        "Authorization": f"PVEAPIToken={API_TOKEN_ID}={API_TOKEN_SECRET}"
    }
    stats = []
    try:
        # Get all nodes
        resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes", headers=headers)
        if resp.status_code == 200:
            nodes = resp.json().get("data", [])
            print("Nodes Response:", resp.json())
        else:
            raise Exception(f"Nodes API error: {resp.status_code} - {resp.text}")
        
        if not nodes:
            stats.append(("Proxmox Error", "No nodes found"))
            return stats

        for node in nodes:
            node_name = node["node"]
            # Get node stats
            resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes/{node_name}/status", headers=headers)
            if resp.status_code == 200:
                node_stats = resp.json().get("data", {})
                print(f"Node {node_name} Status Response:", resp.json())
            else:
                raise Exception(f"Node status error: {resp.status_code} - {resp.text}")

            if not node_stats:  # If no node stats, handle it gracefully
                stats.append((f"Node {node_name} Error", "No stats available"))
                continue

            cpu = round(node_stats.get("cpu", 0) * 100, 1)
            mem_used = node_stats.get("mem", 0) / (1024**3)
            mem_total = node_stats.get("maxmem", 1) / (1024**3)
            stats.append((f"Node: {node_name}", f"{cpu}% {mem_used:.1f}/{mem_total:.1f}G"))

            # Get LXC containers
            resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes/{node_name}/lxc", headers=headers)
            if resp.status_code == 200:
                containers = resp.json().get("data", [])
                print(f"LXC Containers for {node_name}:", resp.json())  # Debugging: print container data
            else:
                raise Exception(f"LXC containers API error: {resp.status_code} - {resp.text}")

            for ct in containers:
                vmid = ct["vmid"]
                name = ct.get("name", f"LXC {vmid}")
                resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes/{node_name}/lxc/{vmid}/status/current", headers=headers)
                if resp.status_code == 200:
                    ct_stats = resp.json().get("data", {})
                    print(f"Container {vmid} Stats:", resp.json())  # Debugging: print container stats
                else:
                    raise Exception(f"LXC container stats error: {resp.status_code} - {resp.text}")

                cpu = round(ct_stats.get("cpu", 0) * 100, 1)
                mem_used = ct_stats.get("mem", 0) / (1024**3)
                mem_total = ct_stats.get("maxmem", 1) / (1024**3)
                stats.append((name, f"{cpu}% {mem_used:.1f}/{mem_total:.1f}G"))

            # Get QEMU VMs
            resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes/{node_name}/qemu", headers=headers)
            if resp.status_code == 200:
                vms = resp.json().get("data", [])
                print(f"QEMU VMs for {node_name}:", resp.json())  # Debugging: print VM data
            else:
                raise Exception(f"QEMU VMs API error: {resp.status_code} - {resp.text}")

            for vm in vms:
                vmid = vm["vmid"]
                name = vm.get("name", f"VM {vmid}")
                resp = session.get(f"{PROXMOX_HOST}/api2/json/nodes/{node_name}/qemu/{vmid}/status/current", headers=headers)
                if resp.status_code == 200:
                    vm_stats = resp.json().get("data", {})
                    print(f"VM {vmid} Stats:", resp.json())  # Debugging: print VM stats
                else:
                    raise Exception(f"VM stats error: {resp.status_code} - {resp.text}")

                cpu = round(vm_stats.get("cpu", 0) * 100, 1)
                mem_used = vm_stats.get("mem", 0) / (1024**3)
                mem_total = vm_stats.get("maxmem", 1) / (1024**3)
                stats.append((name, f"{cpu}% {mem_used:.1f}/{mem_total:.1f}G"))
    except Exception as e:
        stats.append(("Proxmox Error", str(e)))
        print("Proxmox API error:", e)

    return stats

def get_stats():
    ip = get_ip()
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = get_uptime()
    net_up, net_down = get_network_stats()

    system_stats = [
        ("IP Address:", ip),
        ("CPU Usage:", f"{cpu}%"),
        ("RAM Used:", f"{ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB"),
        ("Disk Used:", f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB"),
        ("Uptime:", uptime),
        (net_up, net_down)
    ]
    
    return system_stats + get_proxmox_stats()

ser = serial.Serial(SERIAL_PORT, 9600)
time.sleep(2)

while True:
    for line1, line2 in get_stats():
        try:
            line = f"{line1}|{line2}\n"
            ser.write(line.encode())
            time.sleep(4)
        except Exception as e:
            print("Write error:", e)