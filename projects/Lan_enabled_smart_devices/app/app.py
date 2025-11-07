from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    return render_template('dashboard.html', devices=devices)

@app.route('/toggle/<int:device_id>')
def toggle_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Toggle logic
    device.status = 'OFF' if device.status == 'ON' else 'ON'
    device.last_updated = datetime.utcnow()
    
    # Here you would send signal to Arduino
    # arduino_control(device_id, device.status)
    print(f"Device {device.name} turned {device.status}")
    
    db.session.commit()
    flash(f'{device.name} turned {device.status}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/toggle/<int:device_id>', methods=['POST'])
def api_toggle_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    device.status = 'OFF' if device.status == 'ON' else 'ON'
    device.last_updated = datetime.utcnow()
    
    # Arduino control would go here
    # arduino_control(device_id, device.status)
    print(f"API: Device {device.name} turned {device.status}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'status': device.status,
        'last_updated': device.last_updated.strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    init_db()  # Initialize database when running directly
    app.run(debug=True, host='0.0.0.0',port=5001)
