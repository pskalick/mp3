# Raspberry Pi MP3 App (Split Services)

This project is now split into separate services:

- `bluetooth_service.py` - keeps Bluetooth devices connected
- `playback_service.py` - scans `/media/music` and plays tracks
- `display_service.py` - renders app state to Waveshare 2.13" V4 e-paper
- `shared_state.py` - shared JSON state in `/tmp/mp3_state.json`

## Install on Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3 python3-pip vlc bluez pulseaudio pulseaudio-module-bluetooth
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Display dependencies:

```bash
python3 -m pip install pillow spidev gpiozero lgpio
git clone https://github.com/waveshare/e-Paper.git
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd .
```

Enable SPI:

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
sudo reboot
```

## Waveshare 2.13" V4 Wiring

- VCC -> 3.3V
- GND -> GND
- DIN -> MOSI (pin 19)
- CLK -> SCLK (pin 23)
- CS -> CE0 (pin 24)
- DC -> BCM25 (pin 22)
- RST -> BCM17 (pin 11)
- BUSY -> BCM24 (pin 18)

## Pair Bluetooth once

```bash
bluetoothctl
power on
agent on
default-agent
scan on
# put headphones in pairing mode
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
quit
```

## Run all services together

```bash
chmod +x run.sh
./run.sh
```

Optional fixed device:

```bash
./run.sh AA:BB:CC:DD:EE:FF
```

## Run services individually

```bash
python3 bluetooth_service.py
python3 playback_service.py --music-dir /media/music --shuffle --loop
python3 display_service.py
```

## Systemd (recommended for boot)

Create 3 units:

- `/etc/systemd/system/mp3-bluetooth.service`
- `/etc/systemd/system/mp3-playback.service`
- `/etc/systemd/system/mp3-display.service`

`mp3-bluetooth.service`:

```ini
[Unit]
Description=MP3 Bluetooth Service
After=bluetooth.target network.target

[Service]
Type=simple
WorkingDirectory=/home/pi/mp3
ExecStart=/usr/bin/python3 /home/pi/mp3/bluetooth_service.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

`mp3-playback.service`:

```ini
[Unit]
Description=MP3 Playback Service
After=sound.target mp3-bluetooth.service
Requires=mp3-bluetooth.service

[Service]
Type=simple
WorkingDirectory=/home/pi/mp3
ExecStart=/usr/bin/python3 /home/pi/mp3/playback_service.py --music-dir /media/music --shuffle --loop
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

`mp3-display.service`:

```ini
[Unit]
Description=MP3 E-Paper Display Service
After=mp3-playback.service mp3-bluetooth.service

[Service]
Type=simple
WorkingDirectory=/home/pi/mp3
ExecStart=/usr/bin/python3 /home/pi/mp3/display_service.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mp3-bluetooth.service mp3-playback.service mp3-display.service
sudo systemctl start mp3-bluetooth.service mp3-playback.service mp3-display.service
```
