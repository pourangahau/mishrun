from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure availability directory exists
AVAILABILITY_DIR = 'availability'
if not os.path.exists(AVAILABILITY_DIR):
    os.makedirs(AVAILABILITY_DIR)

def get_availability_file_path(year, month):
    """Generate file path for availability data"""
    return os.path.join(AVAILABILITY_DIR, f'availability_{year}_{month:02d}.json')

def load_availability_data(year, month):
    """Load availability data from JSON file"""
    file_path = get_availability_file_path(year, month)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"volunteers": {}}
    return {"volunteers": {}}

def save_availability_data(year, month, data):
    """Save availability data to JSON file"""
    file_path = get_availability_file_path(year, month)
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError:
        return False

@app.route('/api/availability/<int:year>/<int:month>', methods=['GET'])
def get_availability(year, month):
    """Get availability data for a specific month"""
    try:
        data = load_availability_data(year, month)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/availability/<int:year>/<int:month>', methods=['POST'])
def save_availability(year, month):
    """Save or update availability data for a specific month"""
    try:
        # Get the request data
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['name', 'type', 'dates', 'workload']
        for field in required_fields:
            if field not in request_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Load existing data
        data = load_availability_data(year, month)
        
        # Check if volunteer already exists
        volunteer_exists = request_data['name'] in data['volunteers']
        
        # Update volunteer data
        data['volunteers'][request_data['name']] = {
            'type': request_data['type'],
            'dates': request_data['dates'],
            'workload': request_data['workload'],
            'updated': datetime.now().isoformat()
        }
        
        # Save data
        if save_availability_data(year, month, data):
            return jsonify({
                "success": True,
                "volunteer_existed": volunteer_exists,
                "message": "Availability saved successfully"
            })
        else:
            return jsonify({"error": "Failed to save data"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/availability/<int:year>/<int:month>/check/<name>', methods=['GET'])
def check_volunteer_exists(year, month, name):
    """Check if a volunteer already has availability saved for this month"""
    try:
        data = load_availability_data(year, month)
        exists = name in data['volunteers']
        return jsonify({"exists": exists})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
