import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
import logging
import math
import os
import pyodbc
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ef6c5b4b31266d534b7069822ec1b4eee82d014cab206dbd1cc5e73693db7604')

# Configure CORS based on environment
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('VERCEL_ENV'):
    # Production environment - allow your deployed frontend
    CORS(app, origins=[
        "https://fids-two.vercel.app",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.up.railway.app"
    ])
else:
    # Development environment
    CORS(app, origins="*")

# Initialize SocketIO with appropriate settings
# Initialize SocketIO with appropriate settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*" if not (os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('VERCEL_ENV')) else [
        "https://fids-two.vercel.app",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.up.railway.app"
    ],
    logger=False,  # Disable verbose logging in production
    engineio_logger=False,
    transports=['websocket', 'polling']  # Enable both transports for better compatibility
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    'server': os.getenv('SQL_SERVER_HOST', 'sqlserverdb.cgt0oi2i2k3f.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('SQL_SERVER_DATABASE', 'FIDS_DEV'),
    'username': os.getenv('SQL_SERVER_USERNAME', 'admin'),
    'password': os.getenv('SQL_SERVER_PASSWORD', 'Admin12345!'),
    'driver': '{ODBC Driver 18 for SQL Server}'
}

# SQLAlchemy setup
Base = declarative_base()

class Flight(Base):
    __tablename__ = 'flights'
    
    id = Column(Integer, primary_key=True)
    airline = Column(String(100), nullable=False)
    logo = Column(String(500))
    time = Column(String(10), nullable=False)
    destination = Column(String(100), nullable=False)
    destinationCode = Column(String(10), nullable=False)
    flight = Column(String(20), nullable=False)
    std = Column(String(10), nullable=False)
    etd = Column(String(10), nullable=False)
    gate = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)
    statusClass = Column(String(50), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

# Create database engine and session
def create_db_engine():
    try:
        # Build connection string for pyodbc with better timeout settings for Railway
        connection_string = (
            f"mssql+pyodbc://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['server']}/{DATABASE_CONFIG['database']}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
            f"&TrustServerCertificate=yes"
            f"&Connection+Timeout=30"
            f"&Login+Timeout=30"
            f"&timeout=30"
        )
        logger.info(f"Connecting to: {DATABASE_CONFIG['server']}/{DATABASE_CONFIG['database']}")
        
        # Create engine with connection pooling and timeout settings
        engine = create_engine(
            connection_string, 
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600  # Recycle connections every hour
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return engine
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        logger.error("Please check your .env file and ensure the database is accessible")
        return None

engine = create_db_engine()
Session = sessionmaker(bind=engine) if engine else None

# Global variables for CDC monitoring
cdc_thread = None
cdc_running = False

def init_database():
    """Initialize database tables"""
    if not engine:
        raise Exception("Database connection not available. Please check your SQL Server configuration.")
    
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise e

def get_flights_from_db(page=1, per_page=10):
    """Get paginated flights from database"""
    if not Session:
        raise Exception("Database connection not available. Please check your SQL Server configuration.")
    
    try:
        session = Session()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        total_flights = session.query(Flight).count()
        
        # Get paginated flights with ORDER BY (required for SQL Server OFFSET/LIMIT)
        flights = session.query(Flight).order_by(Flight.id).offset(offset).limit(per_page).all()
        
        # Convert to dict format
        flight_list = []
        for flight in flights:
            flight_dict = {
                'id': flight.id,
                'airline': flight.airline,
                'logo': flight.logo,
                'time': flight.time,
                'destination': flight.destination,
                'destinationCode': flight.destinationCode,
                'flight': flight.flight,
                'std': flight.std,
                'etd': flight.etd,
                'gate': flight.gate,
                'status': flight.status,
                'statusClass': flight.statusClass,
                'last_updated': flight.last_updated.isoformat() if flight.last_updated else None
            }
            flight_list.append(flight_dict)
        
        session.close()
        
        # Calculate pagination info
        total_pages = math.ceil(total_flights / per_page)
        
        return {
            'success': True,
            'flights': flight_list,
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
        }
    except Exception as e:
        logger.error(f"Error fetching flights from database: {str(e)}")
        raise e

def monitor_cdc_changes():
    """Monitor database changes using CDC (Change Data Capture)"""
    global cdc_running
    
    while cdc_running:
        try:
            session = Session()
            
            # Query for recent changes (last 5 seconds)
            recent_changes = session.query(Flight).filter(
                Flight.last_updated >= datetime.utcnow() - timedelta(seconds=5)
            ).all()
            
            if recent_changes:
                # Convert to dict format
                changed_flights = []
                for flight in recent_changes:
                    flight_dict = {
                        'id': flight.id,
                        'airline': flight.airline,
                        'logo': flight.logo,
                        'time': flight.time,
                        'destination': flight.destination,
                        'destinationCode': flight.destinationCode,
                        'flight': flight.flight,
                        'std': flight.std,
                        'etd': flight.etd,
                        'gate': flight.gate,
                        'status': flight.status,
                        'statusClass': flight.statusClass,
                        'last_updated': flight.last_updated.isoformat()
                    }
                    changed_flights.append(flight_dict)
                
                # Emit changes to all connected clients
                socketio.emit('flight_updates', {
                    'type': 'update',
                    'flights': changed_flights,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(f"Broadcasted {len(changed_flights)} flight updates via WebSocket")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error in CDC monitoring: {str(e)}")
        
        time.sleep(2)  # Check every 2 seconds

def start_cdc_monitoring():
    """Start CDC monitoring thread"""
    global cdc_thread, cdc_running
    
    if not cdc_running:
        cdc_running = True
        cdc_thread = threading.Thread(target=monitor_cdc_changes)
        cdc_thread.daemon = True
        cdc_thread.start()
        logger.info("CDC monitoring started")

def stop_cdc_monitoring():
    """Stop CDC monitoring thread"""
    global cdc_running
    cdc_running = False
    logger.info("CDC monitoring stopped")

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'message': 'Connected to FIDS real-time updates'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_flights')
def handle_request_flights(data):
    """Handle flight data request via WebSocket"""
    try:
        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        
        result = get_flights_from_db(page, per_page)
        emit('flight_data', result)
        
    except Exception as e:
        logger.error(f"Error handling flight request: {str(e)}")
        emit('error', {'message': str(e)})


@app.route('/api/flights', methods=['GET'])
def get_flights():
    """Get paginated flight data from database"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 50:
            per_page = 10
        
        # Get flights from database (no fallback)
        result = get_flights_from_db(page, per_page)
        return jsonify(result)
        
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
            'message': 'Database connection error. Please ensure SQL Server is accessible and tables are created.'
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
        'message': 'FIDS API with SQL Server and WebSocket support is running',
        'database': 'connected' if engine else 'disconnected',
        'websocket': 'enabled',
        'cdc_monitoring': 'active' if cdc_running else 'inactive'
    })

@app.route('/api/init-db', methods=['POST'])
def initialize_database():
    """Initialize database tables"""
    try:
        success = init_database()
        if success:
            return jsonify({
                'success': True,
                'message': 'Database tables created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create database tables'
            }), 500
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Database initialization failed'
        }), 500

@app.route('/api/update-flight', methods=['PUT'])
def update_flight():
    """Update a specific flight (triggers CDC)"""
    try:
        data = request.get_json()
        flight_id = data.get('id')
        
        if not flight_id:
            return jsonify({
                'success': False,
                'error': 'Flight ID is required'
            }), 400
        
        session = Session()
        flight = session.query(Flight).filter(Flight.id == flight_id).first()
        
        if not flight:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        # Update flight fields
        for field in ['airline', 'time', 'destination', 'destinationCode', 'flight', 'std', 'etd', 'gate', 'status', 'statusClass']:
            if field in data:
                setattr(flight, field, data[field])
        
        # Update timestamp to trigger CDC
        flight.last_updated = datetime.utcnow()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': f'Flight {flight_id} updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating flight: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Flight update failed'
        }), 500

@app.route('/api/cdc/start', methods=['POST'])
def start_cdc():
    """Start CDC monitoring"""
    try:
        start_cdc_monitoring()
        return jsonify({
            'success': True,
            'message': 'CDC monitoring started'
        })
    except Exception as e:
        logger.error(f"Error starting CDC: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to start CDC monitoring'
        }), 500

@app.route('/api/cdc/stop', methods=['POST'])
def stop_cdc():
    """Stop CDC monitoring"""
    try:
        stop_cdc_monitoring()
        return jsonify({
            'success': True,
            'message': 'CDC monitoring stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping CDC: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to stop CDC monitoring'
        }), 500

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

# Initialize database and start services based on environment
def initialize_services():
    """Initialize database and start services"""
    # Check database connection
    if not engine:
        logger.error("❌ Database connection failed!")
        logger.error("Please ensure:")
        logger.error("1. SQL Server is running and accessible")
        logger.error("2. Environment variables are correctly set in .env file")
        logger.error("3. Run the migration.sql script on your database first")
        if not os.getenv('VERCEL_ENV'):
            exit(1)
        return False
    
    try:
        # Initialize database on startup
        logger.info("Initializing database...")
        init_database()
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        logger.error("Please run the migration.sql script on your AWS SQL Server first")
        if not os.getenv('VERCEL_ENV'):
            exit(1)
        return False
    
    # Start CDC monitoring only if not on Vercel (serverless doesn't support background threads)
    if not os.getenv('VERCEL_ENV'):
        logger.info("Starting CDC monitoring...")
        start_cdc_monitoring()
        logger.info("🚀 Starting FIDS API server...")
        # Run the application with SocketIO
        socketio.run(app, debug=True, port=8000, host='0.0.0.0')
    else:
        logger.info("🚀 FIDS API ready for Vercel deployment")
    
    return True

# For Railway deployment, initialize services when imported
if os.getenv('RAILWAY_ENVIRONMENT'):
    initialize_services()

# Export app for gunicorn
application = app

# For local development
if __name__ == '__main__':
    initialize_services()