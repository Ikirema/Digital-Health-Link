from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from PIL import Image
from ultralytics import YOLO  
import traceback
from flask_cors import CORS
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import logging 

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CORS(app,resources={
    r"/*": {
        "origins": ["http://127.0.0.1:5500", "http://localhost:5500", "*"],  
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})

# Configure the application
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:paul12wako@localhost/digitalhealthlink'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define database model
class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    detections = db.Column(db.Text, nullable=False) 
    sample_name = db.Column(db.String(100), nullable=False)
    patient_number = db.Column(db.String(50), nullable=False)
    timestamps = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load YOLO model
MODEL_PATH = 'best (7).pt'  
model = YOLO(MODEL_PATH)

# Add a simple test route
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'Server is running'}), 200

# Route to handle image upload and analysis
@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    # Handle preflight requests
    logger.debug(f"Received {request.method} request to /upload")
    logger.debug(f"Request headers: {dict(request.headers)}")

    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS request")
        response = jsonify({'message': 'OK'})
        return response

    
        

    try:
        logger.debug(f"Request form data: {request.form}")
        logger.debug(f"Request files: {request.files}")
        # Validate request data
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        sample_name = request.form.get('sample_name')
        patient_number = request.form.get('patient_number')

        if file.filename == '' or not sample_name or not patient_number:
            return jsonify({'error': 'Missing required fields'}), 400

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Validate image
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            os.remove(file_path)  # Clean up invalid file
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400

        # Process image with YOLO
        results = model(file_path)
        detections = []

        # Process YOLO results
        for result in results:
            if hasattr(result, 'boxes') and result.boxes:
                for box in result.boxes:
                    detection = {
                        'class': int(box.cls),
                        'confidence': float(box.conf),
                        'bbox': [float(coord) for coord in box.xyxy[0]]
                    }
                    detections.append(detection)
            else:
                detections.append({'message': 'No detections'})

        # Save to database
        result_entry = AnalysisResult(
            filename=filename,
            detections=str(detections),
            sample_name=sample_name,
            patient_number=patient_number
        )
        db.session.add(result_entry)
        db.session.commit()
        
        logger.debug("Processing completed successfully")
        # Prepare response
        response_data = {
            'success': True,
            'sample_name': sample_name,
            'patient_number': patient_number,
            'filename': filename,
            'detections': detections
        }

        
        # Create response with proper CORS headers
        response = jsonify(response_data)
        logger.debug('response to the user:',response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200

    except Exception as e:
        # Log the full error
        error_details = traceback.format_exc()
        print(f"Error in upload route: {error_details}")

        # Clean up on error
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

        # Return error response
        error_response = jsonify({
            'error': 'Server error occurred',
            'details': str(e)
        })
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/latest-record', methods=['GET'])
def get_latest_record():
    print("Fetching the latest record...")
    latest_record = (
        AnalysisResult.query.order_by(AnalysisResult.timestamps.desc()).first()
    )

    if not latest_record:
        print("No records found.")
        return jsonify({"message": "No records found."}), 404

    current_time = datetime.datetime.utcnow()
    print("Current time (UTC):", current_time)
    print("Latest record timestamp (UTC):", latest_record.timestamps)

    diff_in_minutes = (current_time - latest_record.timestamps).total_seconds() / 60
    print("Time difference in minutes:", diff_in_minutes)

    if diff_in_minutes > 3:
        print("No recent records available.")
        return jsonify({"message": "No recent records available."}), 200

    print("Returning the latest record.")
    return jsonify({
        "id": latest_record.id,
        "filename": latest_record.filename,
        "sample_name": latest_record.sample_name,
        "patient_number": latest_record.patient_number,
        "detections": latest_record.detections,
        "timestamps": latest_record.timestamps.isoformat()
    }), 200


# Route to fetch analysis history
@app.route('/history', methods=['GET'])
def history():
    results = (
        AnalysisResult.query.order_by(AnalysisResult.timestamps.desc())
        .limit(10)
        .all()
    )
    history = [
        {
            'id': r.id,
            'filename': r.filename,
            'detections': r.detections
        }
        for r in results
    ]
    return jsonify(history), 200

# Visualization route
@app.route('/analysis-visualizations', methods=['GET'])
def analysis_visualizations():
    try:
        # Fetch all analysis results from the database
        results = AnalysisResult.query.all()

        if not results:
            return jsonify({"message": "No data available for analysis."}), 404

        # Prepare data for visualization
        samples = [result.sample_name for result in results]
        detection_counts = [len(eval(result.detections)) for result in results]

        # Generate a bar chart
        plt.figure(figsize=(8, 6))
        plt.bar(samples, detection_counts, color='skyblue')
        plt.title('Detections per Sample')
        plt.xlabel('Sample Name')
        plt.ylabel('Number of Detections')
        plt.tight_layout()

        # Save the bar chart to a BytesIO buffer
        bar_chart_buffer = io.BytesIO()
        plt.savefig(bar_chart_buffer, format='png')
        bar_chart_buffer.seek(0)
        plt.close()

        # Generate a pie chart
        detection_summary = {}
        for result in results:
            detections = eval(result.detections)  
            for detection in detections:
                detection_class = detection.get('class', 'Unknown')
                detection_summary[detection_class] = detection_summary.get(detection_class, 0) + 1

        plt.figure(figsize=(8, 6))
        plt.pie(detection_summary.values(), labels=detection_summary.keys(), autopct='%1.1f%%', startangle=140)
        plt.title('Detections Distribution')
        plt.tight_layout()

        # Save the pie chart to a BytesIO buffer
        pie_chart_buffer = io.BytesIO()
        plt.savefig(pie_chart_buffer, format='png')
        pie_chart_buffer.seek(0)
        plt.close()

        # Encode images as base64
        bar_chart_base64 = base64.b64encode(bar_chart_buffer.getvalue()).decode('utf-8')
        pie_chart_base64 = base64.b64encode(pie_chart_buffer.getvalue()).decode('utf-8')

        return jsonify({
            "bar_chart": f"data:image/png;base64,{bar_chart_base64}",
            "pie_chart": f"data:image/png;base64,{pie_chart_base64}",
        })

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()

    # Run the application
    app.run(debug=True)
