import subprocess
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flight data - moved from frontend
FLIGHT_DATA = [
    # Dataset 1 - Mix of Indian and International
    { 
        "id": 1, 
        "airline": "Air India", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Air-India-Logo.png",
        "time": "12:00", 
        "destination": "MUMBAI", 
        "destinationCode": "BOM",
        "flight": "AI 131", 
        "std": "12:00",
        "etd": "12:05",
        "gate": "A12", 
        "status": "Delayed",
        "statusClass": "status-delayed"
    },
    { 
        "id": 2, 
        "airline": "Emirates", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Emirates_logo.svg/200px-Emirates_logo.svg.png",
        "time": "12:05", 
        "destination": "DUBAI", 
        "destinationCode": "DXB",
        "flight": "EK 512", 
        "std": "12:05",
        "etd": "12:05",
        "gate": "B15", 
        "status": "Boarding",
        "statusClass": "status-boarding"
    },
    { 
        "id": 3, 
        "airline": "IndiGo", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/IndiGo_logo.svg/200px-IndiGo_logo.svg.png",
        "time": "12:10", 
        "destination": "DELHI", 
        "destinationCode": "DEL",
        "flight": "6E 2142", 
        "std": "12:10",
        "etd": "12:10",
        "gate": "C08", 
        "status": "On Time",
        "statusClass": "status-on-time"
    },
    { 
        "id": 4, 
        "airline": "Singapore Airlines", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Singapore-Airlines-Logo.png",
        "time": "12:15", 
        "destination": "SINGAPORE", 
        "destinationCode": "SIN",
        "flight": "SQ 518", 
        "std": "12:15",
        "etd": "12:15",
        "gate": "D22", 
        "status": "Gate Open",
        "statusClass": "status-gate-open"
    },
    { 
        "id": 5, 
        "airline": "SpiceJet", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/SpiceJet_Logo.svg/200px-SpiceJet_Logo.svg.png",
        "time": "12:20", 
        "destination": "BANGALORE", 
        "destinationCode": "BLR",
        "flight": "SG 8194", 
        "std": "12:20",
        "etd": "12:20",
        "gate": "A05", 
        "status": "Check-In",
        "statusClass": "status-check-in"
    },
    { 
        "id": 6, 
        "airline": "Lufthansa", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Lufthansa_Logo_2018.svg/200px-Lufthansa_Logo_2018.svg.png",
        "time": "12:25", 
        "destination": "FRANKFURT", 
        "destinationCode": "FRA",
        "flight": "LH 761", 
        "std": "12:25",
        "etd": "12:25",
        "gate": "E11", 
        "status": "Scheduled",
        "statusClass": "status-scheduled"
    },
    { 
        "id": 7, 
        "airline": "Vistara", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Vistara_Logo.svg/200px-Vistara_Logo.svg.png",
        "time": "12:30", 
        "destination": "CHENNAI", 
        "destinationCode": "MAA",
        "flight": "UK 889", 
        "std": "12:30",
        "etd": "12:35",
        "gate": "B07", 
        "status": "Final Call",
        "statusClass": "status-final-call"
    },
    { 
        "id": 8, 
        "airline": "Qatar Airways", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Qatar_Airways_Logo.svg/200px-Qatar_Airways_Logo.svg.png",
        "time": "12:35", 
        "destination": "DOHA", 
        "destinationCode": "DOH",
        "flight": "QR 614", 
        "std": "12:35",
        "etd": "12:35",
        "gate": "C19", 
        "status": "Now Boarding",
        "statusClass": "status-now-boarding"
    },
    { 
        "id": 9, 
        "airline": "GoAir", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Go_First_logo.svg/200px-Go_First_logo.svg.png",
        "time": "12:40", 
        "destination": "KOLKATA", 
        "destinationCode": "CCU",
        "flight": "G8 152", 
        "std": "12:40",
        "etd": "12:40",
        "gate": "A18", 
        "status": "Go to Gate",
        "statusClass": "status-go-to-gate"
    },
    { 
        "id": 10, 
        "airline": "British Airways", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/British_Airways_Logo.svg/200px-British_Airways_Logo.svg.png",
        "time": "12:45", 
        "destination": "LONDON", 
        "destinationCode": "LHR",
        "flight": "BA 142", 
        "std": "12:45",
        "etd": "13:15",
        "gate": "D14", 
        "status": "Delayed",
        "statusClass": "status-delayed"
    },
    # Dataset 2 - More flights
    { 
        "id": 11, 
        "airline": "IndiGo", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/IndiGo_logo.svg/200px-IndiGo_logo.svg.png",
        "time": "12:50", 
        "destination": "PUNE", 
        "destinationCode": "PNQ",
        "flight": "6E 6114", 
        "std": "12:50",
        "etd": "12:50",
        "gate": "B03", 
        "status": "Boarding",
        "statusClass": "status-boarding"
    },
    { 
        "id": 12, 
        "airline": "Thai Airways", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Thai_Airways_logo.svg/200px-Thai_Airways_logo.svg.png",
        "time": "12:55", 
        "destination": "BANGKOK", 
        "destinationCode": "BKK",
        "flight": "TG 315", 
        "std": "12:55",
        "etd": "12:55",
        "gate": "E09", 
        "status": "Last Call",
        "statusClass": "status-last-call"
    },
    { 
        "id": 13, 
        "airline": "Air India Express", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Air_India_Logo.svg/200px-Air_India_Logo.svg.png",
        "time": "13:00", 
        "destination": "KOCHI", 
        "destinationCode": "COK",
        "flight": "IX 384", 
        "std": "13:00",
        "etd": "13:00",
        "gate": "A09", 
        "status": "Gate Closed",
        "statusClass": "status-gate-closed"
    },
    { 
        "id": 14, 
        "airline": "American Airlines", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/American_Airlines_logo_2013.svg/200px-American_Airlines_logo_2013.svg.png",
        "time": "13:05", 
        "destination": "NEW YORK", 
        "destinationCode": "JFK",
        "flight": "AA 127", 
        "std": "13:05",
        "etd": "13:05",
        "gate": "D25", 
        "status": "Departed",
        "statusClass": "status-departed"
    },
    { 
        "id": 15, 
        "airline": "AirAsia India", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/AirAsia_New_Logo.svg/200px-AirAsia_New_Logo.svg.png",
        "time": "13:10", 
        "destination": "GOA", 
        "destinationCode": "GOI",
        "flight": "I5 719", 
        "std": "13:10",
        "etd": "13:10",
        "gate": "C06", 
        "status": "On Time",
        "statusClass": "status-on-time"
    },
    { 
        "id": 16, 
        "airline": "Air France", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Air_France_Logo.svg/200px-Air_France_Logo.svg.png",
        "time": "13:15", 
        "destination": "PARIS", 
        "destinationCode": "CDG",
        "flight": "AF 225", 
        "std": "13:15",
        "etd": "13:45",
        "gate": "E16", 
        "status": "New Time",
        "statusClass": "status-new-time"
    },
    { 
        "id": 17, 
        "airline": "Jet Airways", 
        "logo": "https://logos-world.net/wp-content/uploads/2021/02/Jet-Airways-Logo.png",
        "time": "13:20", 
        "destination": "AHMEDABAD", 
        "destinationCode": "AMD",
        "flight": "9W 469", 
        "std": "13:20",
        "etd": "13:20",
        "gate": "B12", 
        "status": "Cancelled",
        "statusClass": "status-cancelled"
    },
    { 
        "id": 18, 
        "airline": "KLM", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/KLM-Logo.png",
        "time": "13:25", 
        "destination": "AMSTERDAM", 
        "destinationCode": "AMS",
        "flight": "KL 872", 
        "std": "13:25",
        "etd": "13:25",
        "gate": "D18", 
        "status": "Check-In",
        "statusClass": "status-check-in"
    },
    { 
        "id": 19, 
        "airline": "Alliance Air", 
        "logo": "https://logos-world.net/wp-content/uploads/2023/01/Alliance-Air-Logo.png",
        "time": "13:30", 
        "destination": "JAIPUR", 
        "destinationCode": "JAI",
        "flight": "9I 624", 
        "std": "13:30",
        "etd": "13:30",
        "gate": "A15", 
        "status": "Diverted",
        "statusClass": "status-diverted"
    },
    { 
        "id": 20, 
        "airline": "Turkish Airlines", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Turkish-Airlines-Logo.png",
        "time": "13:35", 
        "destination": "ISTANBUL", 
        "destinationCode": "IST",
        "flight": "TK 714", 
        "std": "13:35",
        "etd": "13:35",
        "gate": "E21", 
        "status": "Gate Open",
        "statusClass": "status-gate-open"
    },
    # Dataset 3 - Additional flights
    { 
        "id": 21, 
        "airline": "IndiGo", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/IndiGo_logo.svg/200px-IndiGo_logo.svg.png",
        "time": "13:40", 
        "destination": "HYDERABAD", 
        "destinationCode": "HYD",
        "flight": "6E 7019", 
        "std": "13:40",
        "etd": "13:40",
        "gate": "C12", 
        "status": "Final Call",
        "statusClass": "status-final-call"
    },
    { 
        "id": 22, 
        "airline": "Japan Airlines", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Japan-Airlines-Logo.png",
        "time": "13:45", 
        "destination": "TOKYO", 
        "destinationCode": "NRT",
        "flight": "JL 748", 
        "std": "13:45",
        "etd": "13:45",
        "gate": "E08", 
        "status": "Boarding",
        "statusClass": "status-boarding"
    },
    { 
        "id": 23, 
        "airline": "SpiceJet", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/SpiceJet_Logo.svg/200px-SpiceJet_Logo.svg.png",
        "time": "13:50", 
        "destination": "SRINAGAR", 
        "destinationCode": "SXR",
        "flight": "SG 991", 
        "std": "13:50",
        "etd": "14:20",
        "gate": "A21", 
        "status": "Delayed",
        "statusClass": "status-delayed"
    },
    { 
        "id": 24, 
        "airline": "Cathay Pacific", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Cathay-Pacific-Logo.png",
        "time": "13:55", 
        "destination": "HONG KONG", 
        "destinationCode": "HKG",
        "flight": "CX 695", 
        "std": "13:55",
        "etd": "13:55",
        "gate": "D09", 
        "status": "Now Boarding",
        "statusClass": "status-now-boarding"
    },
    { 
        "id": 25, 
        "airline": "Air India", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Air_India_Logo.svg/200px-Air_India_Logo.svg.png",
        "time": "14:00", 
        "destination": "BHUBANESWAR", 
        "destinationCode": "BBI",
        "flight": "AI 406", 
        "std": "14:00",
        "etd": "14:00",
        "gate": "B09", 
        "status": "Gate Closed",
        "statusClass": "status-gate-closed"
    },
    { 
        "id": 26, 
        "airline": "Ethiopian Airlines", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Ethiopian-Airlines-Logo.png",
        "time": "14:05", 
        "destination": "ADDIS ABABA", 
        "destinationCode": "ADD",
        "flight": "ET 684", 
        "std": "14:05",
        "etd": "14:05",
        "gate": "E19", 
        "status": "Scheduled",
        "statusClass": "status-scheduled"
    },
    { 
        "id": 27, 
        "airline": "Vistara", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Vistara_Logo.svg/200px-Vistara_Logo.svg.png",
        "time": "14:10", 
        "destination": "LUCKNOW", 
        "destinationCode": "LKO",
        "flight": "UK 971", 
        "std": "14:10",
        "etd": "14:10",
        "gate": "C15", 
        "status": "On Time",
        "statusClass": "status-on-time"
    },
    { 
        "id": 28, 
        "airline": "Korean Air", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Korean-Air-Logo.png",
        "time": "14:15", 
        "destination": "SEOUL", 
        "destinationCode": "ICN",
        "flight": "KE 672", 
        "std": "14:15",
        "etd": "14:15",
        "gate": "D17", 
        "status": "Go to Gate",
        "statusClass": "status-go-to-gate"
    },
    { 
        "id": 29, 
        "airline": "GoAir", 
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Go_First_logo.svg/200px-Go_First_logo.svg.png",
        "time": "14:20", 
        "destination": "INDORE", 
        "destinationCode": "IDR",
        "flight": "G8 394", 
        "std": "14:20",
        "etd": "14:20",
        "gate": "A07", 
        "status": "Check-In",
        "statusClass": "status-check-in"
    },
    { 
        "id": 30, 
        "airline": "Malaysia Airlines", 
        "logo": "https://logos-world.net/wp-content/uploads/2020/03/Malaysia-Airlines-Logo.png",
        "time": "14:25", 
        "destination": "KUALA LUMPUR", 
        "destinationCode": "KUL",
        "flight": "MH 192", 
        "std": "14:25",
        "etd": "14:25",
        "gate": "E13", 
        "status": "Departed",
        "statusClass": "status-departed"
    }
]

@app.route('/api/flights', methods=['GET'])
def get_flights():
    """Get paginated flight data"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 50:
            per_page = 10
            
        # Calculate pagination
        total_flights = len(FLIGHT_DATA)
        total_pages = math.ceil(total_flights / per_page)
        
        # Handle page overflow - reset to page 1 if beyond total pages
        if page > total_pages:
            page = 1
            
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        
        # Get paginated data
        flights = FLIGHT_DATA[start_index:end_index]
        
        return jsonify({
            'success': True,
            'flights': flights,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_flights': total_flights,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'next_page': page + 1 if page < total_pages else 1,
                'prev_page': page - 1 if page > 1 else total_pages
            }
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid page or per_page parameter. Must be integers.',
            'message': 'Bad request'
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching flights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

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