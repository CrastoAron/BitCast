# Bitcast

**Your desktop, down to 1 bit.**

Bitcast is a tiny wireless video streaming project that captures a selected region of a computer screen, converts it into a 128×64 monochrome bitmap, and streams it over Wi-Fi to an ESP32 connected to an OLED display.

The idea is simple: take a video playing on your laptop and watch it on a tiny, low-resolution OLED. Bitcast explores real-time screen capture, image processing, UDP networking, and embedded display rendering.

## Features

- **Live screen capture** — Select a specific region of your desktop.
- **Monochrome conversion** — Resize captured frames to 128×64 pixels and convert them to black and white.
- **Wireless streaming** — Transmit frames from the laptop to the ESP32 over UDP.
- **Real-time playback** — Targets 30 FPS for miniature video playback.
- **Lightweight receiver** — The ESP32 receives bitmap frames and renders them on the OLED.
- **Linux-friendly backend** — Python handles screen capture and image processing.

## How It Works

```text
┌──────────────────────────────┐
│            Laptop            │
│                              │
│  Screen Region Capture       │
│            ↓                 │
│  Resize to 128 × 64          │
│            ↓                 │
│  Monochrome Conversion       │
│            ↓                 │
│  Pack Pixels into Bitmap     │
└──────────────┬───────────────┘
               │
               │ UDP over Wi-Fi
               │
               ▼
┌──────────────────────────────┐
│             ESP32            │
│                              │
│  Receive Frame               │
│            ↓                 │
│  Decode Bitmap               │
│            ↓                 │
│  Update OLED                 │
└──────────────┬───────────────┘
               │ I²C
               ▼
┌──────────────────────────────┐
│         128 × 64 OLED        │
│       Monochrome Video       │
└──────────────────────────────┘
```

## Hardware

| Component | Specification |
|---|---|
| Microcontroller | ESP32 DevKit (ESP-WROOM-32) |
| Display | 128×64 monochrome OLED |
| Display interface | I²C |
| Wireless communication | Wi-Fi |
| Frame transport | UDP |

### OLED Wiring

For a typical SSD1306-compatible I²C OLED:

| OLED Pin | ESP32 Pin |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

These connections assume a standard ESP32 DevKit and an SSD1306-compatible display.

## Software Stack

### Laptop

- Python
- [MSS](https://python-mss.readthedocs.io/) — Screen capture
- [Pillow](https://pillow.readthedocs.io/) — Image resizing and conversion
- [NumPy](https://numpy.org/) — Bitmap packing
- Python sockets — UDP transmission
- Tkinter — Screen-region selection

### ESP32

- Arduino framework
- Wi-Fi and UDP libraries
- [U8g2](https://github.com/olikraus/u8g2) — OLED rendering
- I²C — Display communication

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/bitcast.git
cd bitcast
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Set Up the Python Environment

On Arch Linux or EndeavourOS:

```bash
sudo pacman -S --needed python python-pip tk
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install mss pillow numpy
```

### 3. Configure the ESP32

1. Open the receiver sketch in Arduino IDE.
2. Install the U8g2 library through Library Manager.
3. Enter your Wi-Fi SSID and password in the firmware.
4. Select your ESP32 board and serial port.
5. Upload the firmware.
6. Open Serial Monitor at **115200 baud** and note the ESP32's IP address.

### 4. Start Streaming

Run the Python sender with your ESP32's IP address:

```bash
python stream.py <ESP32_IP> --fps 30
```

Example:

```bash
python stream.py 192.168.1.123 --fps 30
```

Drag over the part of the screen you want to capture. Bitcast will begin transmitting the selected region to the OLED.

Both devices must be reachable on the same local network, and UDP port `4210` must be available.

## Frame Format

Each captured frame is converted into a 1-bit monochrome bitmap.

| Property | Value |
|---|---:|
| Resolution | 128 × 64 |
| Total pixels | 8,192 |
| Bits per pixel | 1 |
| Bitmap size | 1,024 bytes |
| Target frame rate | 30 FPS |
| Raw bitmap throughput at 30 FPS | 30,720 bytes/sec |
| UDP payload per frame | 1,028 bytes |

The sender prepends a four-byte sequence number to each 1,024-byte bitmap.

UDP is used because this is a real-time display experiment: receiving the latest frame is more useful than retransmitting an old one.

## Current Status

**Working prototype**

- [x] ESP32 Wi-Fi connection
- [x] OLED initialization and rendering
- [x] Laptop-to-ESP32 UDP communication
- [x] Desktop-region selection
- [x] Real-time monochrome frame conversion
- [x] Video streaming at a target of 30 FPS

Image conversion and readability are still being explored. Different thresholding and dithering techniques affect text legibility, contrast, and perceived noise on a 128×64 display.

## Roadmap

- [ ] Improve monochrome conversion and text readability
- [ ] Add selectable image-processing modes
- [ ] Measure end-to-end frame rate and latency
- [ ] Improve capture-region handling
- [ ] Build a compact desktop control interface
- [ ] Experiment with music artwork and visualizations
- [ ] Add physical buttons for playback controls

## Why Bitcast?

Bitcast combines two ideas: **bits**, the individual pixels that make up each frame, and **casting**, the wireless transmission of those frames to another device.

The result is a miniature video display built from a laptop, an ESP32, and a small OLED.

## License

This project is currently under development.
