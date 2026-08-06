# 👻 BlueGhost - Anonymous Offline Bluetooth Chat

**BlueGhost** is a modern, anonymous, offline-first Bluetooth chat web application built with Python 3.12, Flask, Flask-SocketIO, SQLite, Bleak (Bluetooth Low Energy), and Vanilla JavaScript in a sleek **cyberpunk dark UI**.

---

## 🌟 Key Features

* 👻 **Random Ephemeral Identities**: Zero registration, accounts, or persistent logs. Each app launch generates a random ghost identity (e.g. `👻 Ghost_241`, `🌑 Shadow_73`, `🦊 Fox_102`).
* 📡 **Bluetooth Low Energy (Bleak Integration)**: Scans nearby BLE devices, calculates signal strength (RSSI) and estimated physical distance in meters.
* 🔒 **AES-256 Payload Encryption**: Encrypts all message payloads using temporary session keys before transmission over Bluetooth / WebSockets.
* ⏱️ **Self-Destruct Messages**: Configurable auto-destruct timers (10s, 30s, 1m, 5m, 24h) with real-time countdown badges and automated background database purging.
* 🖼️ **Image & File Attachments**: Supports sharing `.jpg`, `.png`, `.gif` with instant image previews, and `.pdf`, `.zip`, `.txt`, `.docx` file transfers with progress counters.
* 👻 **Haunting Typing Indicator**: Dynamic typing animation (`Ghost_X is haunting...`).
* 🔊 **Cyber Audio Feedback**: Built-in sound effects for `connected`, `disconnected`, `message_received`, `message_sent`, and `ghost_vanished`.
* 🔔 **Desktop Notifications**: Browser notifications when a ghost sends a message while the app is in the background.

---

## 📁 Project Structure

```
BlueGhost/
├── app.py                      # Flask app server & SocketIO event controllers
├── requirements.txt            # Python dependencies
├── bluetooth/
│   ├── __init__.py
│   ├── scanner.py              # Bleak BLE device scanner & RSSI distance calculator
│   ├── connection.py           # BLE connection lifecycle & auto-reconnect logic
│   └── messaging.py            # AES-256 message encryption & decryption engine
├── database/
│   ├── __init__.py
│   └── database.py             # SQLite helper for messages, devices, and self-destruct cleaner
├── templates/
│   ├── index.html              # Cyberpunk landing page
│   └── chat.html               # Scanner & real-time chat interface
├── static/
│   ├── css/
│   │   └── style.css           # Custom dark cyberpunk styling (#0b0b0b, #7c3aed, #22d3ee)
│   ├── js/
│   │   ├── app.js              # SocketIO client controller
│   │   ├── bluetooth.js        # Device list UI & RSSI indicators
│   │   ├── chat.js             # Message bubble renderer & countdown timers
│   │   ├── audio.js            # UI audio effects controller
│   │   ├── emoji.js            # Custom emoji picker
│   │   └── ui.js               # Desktop notifications & modals
│   ├── images/
│   └── sounds/
│       ├── connected.wav
│       ├── disconnected.wav
│       ├── message_received.wav
│       ├── message_sent.wav
│       └── ghost_vanished.wav
└── uploads/                    # Temporary file attachments directory
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Bluetooth adapter enabled on your operating system (Windows / macOS / Linux)

### 2. Clone / Download & Install Dependencies

```bash
cd "d:\bluetooth chat project"
pip install -r requirements.txt
```

---

## 🚀 Running BlueGhost

Start the Flask-SocketIO server:

```bash
python app.py
```

Then open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Bluetooth Permissions & BLE Setup

- **Windows**: Windows 10/11 natively supports BLE scanning via standard OS Bluetooth permissions. Ensure Bluetooth is toggled **ON** in Settings.
- **Linux**: Bleak requires `bluez` and appropriate permissions. Grant capability to python if needed:
  ```bash
  sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
  ```
- **Fallback Mode**: If Bluetooth hardware is unavailable or disabled, BlueGhost automatically engages a **Hybrid Simulator Mode** so you can test all features and message flows seamlessly.

---

## 🔮 Future Improvements

1. **Mesh Bluetooth Relay**: Multi-hop Bluetooth message routing across multiple ghost nodes.
2. **WebRTC Direct Peer-to-Peer DataChannels**: Zero-server direct P2P streaming for large media.
3. **Hardware BLE Beacons**: Custom ESP32 / Arduino BLE beacon firmware integration.
