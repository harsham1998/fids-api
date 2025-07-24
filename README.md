# FIDS ADB API

Python Flask API for executing ADB commands remotely to control Android devices displaying the FIDS application.

## Features

- **Execute ADB Commands**: Send commands to open specific pages on Android devices
- **Device Management**: List and connect to ADB devices
- **CORS Enabled**: Works with web frontends
- **Error Handling**: Comprehensive error handling and logging

## API Endpoints

### POST /api/execute-adb
Execute ADB command to open a URL on an Android device.

**Request Body:**
```json
{
  "deviceIP": "192.168.1.100",
  "targetPage": "departures",
  "baseURL": "https://fids-two.vercel.app"
}
```

**Response:**
```json
{
  "success": true,
  "command": "adb shell am start -a android.intent.action.VIEW -d https://fids-two.vercel.app/departures",
  "output": "Starting: Intent { act=android.intent.action.VIEW dat=https://fids-two.vercel.app/departures }",
  "device_ip": "192.168.1.100",
  "target_url": "https://fids-two.vercel.app/departures",
  "message": "Successfully sent command to device 192.168.1.100"
}
```

### GET /api/adb-devices
List all connected ADB devices.

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "192.168.1.100:5555",
      "status": "device"
    }
  ],
  "raw_output": "List of devices attached\n192.168.1.100:5555\tdevice\n"
}
```

### POST /api/adb-connect
Connect to an ADB device over network.

**Request Body:**
```json
{
  "deviceIP": "192.168.1.100",
  "port": "5555"
}
```

### GET /api/health
Health check endpoint.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

Server runs on `http://localhost:8000`

## Vercel Deployment

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel --prod
```

## Prerequisites

- ADB (Android Debug Bridge) must be installed on the server
- Android devices must have USB debugging enabled
- For network ADB: `adb connect <device-ip>:5555` must be run first

## Environment Setup

Make sure ADB is accessible in the system PATH. On most systems:
- **Windows**: Add Android SDK platform-tools to PATH
- **macOS**: `brew install android-platform-tools`
- **Linux**: `sudo apt install adb` or similar

## Security Notes

- This API executes system commands - use in trusted environments only
- Consider adding authentication for production use
- Ensure proper network security when using network ADB connections