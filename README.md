# Proxmox LCD Screen
> Add an LCD screen to your server rack to monitor statistics

## Installation

Upload the .ino code to your Arduino of choice following the pinout below:

LCD Screen w/ I2C module
- GND -> GND
- VCC -> 5v
- SDA -> A4
- SCL -> A5

### Proxmox Shell

`nano /opt/lcd_display.py` 
> Paste in code
> Update config to suit your system

`nano /etc/systemd/system/lcd-display.service`
> Paste in code

`systemctl daemon-reload`

`systemctl enable lcd-display.service`

`systemctl restart lcd-display.service`
