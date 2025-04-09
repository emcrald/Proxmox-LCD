# Proxmox LCD Screen
> Add an LCD screen to your server rack to monitor statistics

## Installation

Upload the .ino code to your Arduino of choice following the pinout below:

LCD Screen w/ I2C module
- GND -> GND
- VCC -> 5v
- SDA -> A4
- SCL -> A5

### API Key
> Create an API key

![image](https://github.com/user-attachments/assets/a4dc50cf-ff87-4f19-959c-c120a3d048d3)

> Give it the right permissions

![image](https://github.com/user-attachments/assets/eef52c7c-dc3e-43fc-91a0-e53795753634)


### Proxmox Shell

`nano /opt/lcd_display.py` 
> Paste in code

> Update config to suit your system

`nano /etc/systemd/system/lcd-display.service`
> Paste in code

`systemctl daemon-reload`

`systemctl enable lcd-display.service`

`systemctl restart lcd-display.service`
