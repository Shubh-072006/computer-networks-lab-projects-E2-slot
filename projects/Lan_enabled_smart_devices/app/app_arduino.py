from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging

# Import Arduino controller
from arduino_controller import get_arduino_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize Arduino controller (auto-detects port and auto-reconnects)
arduino = get_arduino_controller(auto_reconnect=True)

# Device model
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(10), default='OFF')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Device {self.name}: {self.status}>'

# Initialize database and add sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add sample devices if none exist
        if Device.query.count() == 0:
            sample_devices = [
                Device(name='Living Room Light', room='Living Room', device_type='light'),
                Device(name='Bedroom Fan', room='Bedroom', device_type='fan'),
                Device(name='Kitchen Outlet', room='Kitchen', device_type='outlet'),
                Device(name='Porch Light', room='Porch', device_type='light')
            ]
            
            for device in sample_devices:
                db.session.add(device)
            db.session.commit()
            print("Sample devices added!")

# Routes
@app.route('/')
def dashboard():
    devices = Device.query.all()
    # Get Arduino connection status
    arduino_status = arduino.get_status()
    return render_template('dashboard.html', 
                         devices=devices, 
                         arduino_connected=arduino_status['connected'])

@app.route('/toggle/<int:device_id>')
def toggle_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Toggle logic
    device.status = 'OFF' if device.status == 'ON' else 'ON'
    device.last_updated = datetime.utcnow()
    
    # Send to Arduino
    state = 1 if device.status == 'ON' else 0
    arduino_success = arduino.send_command(device_id, state)
    
    if arduino_success:
        logging.info(f"✅ Device {device.name} turned {device.status}")
        flash(f'{device.name} turned {device.status}', 'success')
    else:
        logging.warning(f"⚠️ Device {device.name} updated in database but Arduino command failed")
        flash(f'{device.name} turned {device.status} (Arduino not connected)', 'warning')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/api/toggle/<int:device_id>', methods=['POST'])
def api_toggle_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Toggle status
    device.status = 'OFF' if device.status == 'ON' else 'ON'
    device.last_updated = datetime.utcnow()
    
    # Send to Arduino
    state = 1 if device.status == 'ON' else 0
    arduino_success = arduino.send_command(device_id, state)
    
    logging.info(f"API: Device {device.name} turned {device.status}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'status': device.status,
        'last_updated': device.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
        'arduino_updated': arduino_success
    })

@app.route('/api/device/<int:device_id>/set', methods=['POST'])
def api_set_device(device_id):
    """Set device to specific state (not toggle)"""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    
    # Get desired state from request
    desired_state = data.get('state', 'OFF').upper()
    if desired_state not in ['ON', 'OFF']:
        return jsonify({'success': False, 'error': 'Invalid state'}), 400
    
    device.status = desired_state
    device.last_updated = datetime.utcnow()
    
    # Send to Arduino
    state = 1 if desired_state == 'ON' else 0
    arduino_success = arduino.send_command(device_id, state)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'status': device.status,
        'arduino_updated': arduino_success
    })

@app.route('/api/arduino/status')
def arduino_status_api():
    """Get Arduino connection status"""
    status = arduino.get_status()
    return jsonify(status)

@app.route('/api/arduino/reconnect', methods=['POST'])
def arduino_reconnect():
    """Force Arduino reconnection"""
    success = arduino.connect()
    return jsonify({
        'success': success,
        'status': arduino.get_status()
    })

@app.route('/api/devices/sync', methods=['POST'])
def sync_all_devices():
    """Sync all devices with Arduino (useful after Arduino reconnects)"""
    devices = Device.query.all()
    results = []
    
    for device in devices:
        state = 1 if device.status == 'ON' else 0
        success = arduino.send_command(device.id, state)
        results.append({
            'device_id': device.id,
            'name': device.name,
            'status': device.status,
            'synced': success
        })
    
    return jsonify({
        'success': True,
        'devices': results
    })

if __name__ == '__main__':
    init_db()  # Initialize database when running directly
    
    # Sync all devices with Arduino on startup
    with app.app_context():
        try:
            devices = Device.query.all()
            logging.info("🔄 Syncing devices with Arduino on startup...")
            for device in devices:
                state = 1 if device.status == 'ON' else 0
                arduino.send_command(device.id, state)
        except Exception as e:
            logging.error(f"⚠️ Could not sync devices on startup: {e}")
    
    app.run(debug=False, host='127.0.0.1', port=5001, threaded=True)
