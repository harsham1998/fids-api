import subprocess
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/execute-adb', methods=['POST'])
def execute_adb():
    try:
        data = request.get_json()
        device_ip = data.get('deviceIP')
        target_page = data.get('targetPage', 'departures')
        base_url = data.get('baseURL', 'https://fids-two.vercel.app')
        
        if not device_ip:
            return jsonify({
                'success': False,
                'error': 'Device IP is required'
            }), 400
        
        # Construct the full URL
        full_url = f"{base_url}/{target_page}"
        
        # ADB command to open URL in browser
        adb_command = [
            'adb', 'shell', 'am', 'start',
            '-a', 'android.intent.action.VIEW',
            '-d', full_url
        ]
        
        logger.info(f"Executing ADB command: {' '.join(adb_command)}")
        
        # Execute the ADB command
        result = subprocess.run(
            adb_command,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'command': ' '.join(adb_command),
                'output': result.stdout,
                'device_ip': device_ip,
                'target_url': full_url,
                'message': f'Successfully sent command to device {device_ip}'
            })
        else:
            return jsonify({
                'success': False,
                'command': ' '.join(adb_command),
                'error': result.stderr,
                'device_ip': device_ip,
                'target_url': full_url,
                'message': f'Failed to execute command on device {device_ip}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Command timed out after 30 seconds',
            'message': 'ADB command execution timed out'
        }), 408
        
    except Exception as e:
        logger.error(f"Error executing ADB command: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

@app.route('/api/adb-devices', methods=['GET'])
def list_adb_devices():
    """List connected ADB devices"""
    try:
        result = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse ADB devices output
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = []
            
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]
                        devices.append({
                            'device_id': device_id,
                            'status': status
                        })
            
            return jsonify({
                'success': True,
                'devices': devices,
                'raw_output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr,
                'message': 'Failed to list ADB devices'
            }), 500
            
    except Exception as e:
        logger.error(f"Error listing ADB devices: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to list ADB devices'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'FIDS ADB API is running'
    })

@app.route('/api/adb-connect', methods=['POST'])
def connect_adb_device():
    """Connect to ADB device over network"""
    try:
        data = request.get_json()
        device_ip = data.get('deviceIP')
        port = data.get('port', '5555')  # Default ADB port
        
        if not device_ip:
            return jsonify({
                'success': False,
                'error': 'Device IP is required'
            }), 400
        
        # ADB connect command
        connect_command = ['adb', 'connect', f"{device_ip}:{port}"]
        
        logger.info(f"Connecting to ADB device: {' '.join(connect_command)}")
        
        result = subprocess.run(
            connect_command,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'command': ' '.join(connect_command),
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None,
            'device_ip': device_ip,
            'port': port
        })
        
    except Exception as e:
        logger.error(f"Error connecting to ADB device: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to connect to ADB device'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)