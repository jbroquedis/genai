#!/usr/bin/env python3
"""
Improved ComfyUI Backend with Better Error Handling
"""

import os
import json
import base64
import requests
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
COMFY_UI_URL = "http://localhost:8188"
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/api/process-base64', methods=['POST'])
def process_base64_image():
    """Process base64 image with detailed error handling"""
    try:
        print("🔍 API call received")
        
        # Get JSON data
        data = request.get_json()
        print(f"📋 Request data keys: {list(data.keys()) if data else 'None'}")
        
        if not data or 'image' not in data:
            print("❌ No image data in request")
            return jsonify({"error": "No image data provided"}), 400
        
        image_base64 = data['image']
        prompt = data.get('prompt', 'modern architectural building')
        print(f"📝 Prompt: {prompt}")
        print(f"🖼️ Image data length: {len(image_base64)} characters")
        
        # Check if ComfyUI is available
        print("🔗 Testing ComfyUI connection...")
        try:
            response = requests.get(f"{COMFY_UI_URL}/system_stats", timeout=5)
            if response.status_code != 200:
                print(f"⚠️ ComfyUI not responding: {response.status_code}")
                return jsonify({
                    "error": "ComfyUI not available",
                    "details": f"ComfyUI returned status {response.status_code}",
                    "suggestion": "Make sure ComfyUI is running on localhost:8188"
                }), 503
            print("✅ ComfyUI connection successful")
        except requests.exceptions.ConnectionError:
            print("❌ ComfyUI connection failed")
            return jsonify({
                "error": "Cannot connect to ComfyUI",
                "details": "Connection refused to localhost:8188",
                "suggestion": "Start ComfyUI with: python main.py"
            }), 503
        except Exception as e:
            print(f"❌ ComfyUI connection error: {e}")
            return jsonify({
                "error": "ComfyUI connection error",
                "details": str(e)
            }), 503
        
        # Save base64 image
        print("💾 Saving image...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"input_{timestamp}.png"
        
        try:
            # Remove data URL prefix if present
            if "data:image" in image_base64:
                image_base64 = image_base64.split(",")[1]
            
            # Decode and save
            image_data = base64.b64decode(image_base64)
            filepath = os.path.join(UPLOAD_DIR, input_filename)
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            print(f"✅ Image saved: {filepath} ({len(image_data)} bytes)")
            
        except Exception as e:
            print(f"❌ Image save error: {e}")
            return jsonify({
                "error": "Failed to save image",
                "details": str(e)
            }), 500
        
        # For now, return mock data since ComfyUI workflow is complex
        print("🎨 Generating mock AI result...")
        
        # Create a simple mock response
        mock_result = {
            "success": True,
            "output_image": image_base64,  # Return original as mock result
            "prompt": prompt,
            "processing_time": "completed",
            "output_filename": f"mock_output_{timestamp}.png",
            "note": "This is a mock result. Real AI processing requires ComfyUI workflow setup."
        }
        
        print("✅ Mock result generated successfully")
        return jsonify(mock_result)
        
    except Exception as e:
        # Detailed error logging
        error_details = {
            "error": "Server processing failed",
            "details": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        print("❌ DETAILED ERROR:")
        print(f"Error: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        
        return jsonify(error_details), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check"""
    try:
        # Test ComfyUI connection
        try:
            response = requests.get(f"{COMFY_UI_URL}/system_stats", timeout=5)
            comfy_status = "connected" if response.status_code == 200 else f"error_{response.status_code}"
        except requests.exceptions.ConnectionError:
            comfy_status = "connection_refused"
        except Exception as e:
            comfy_status = f"error_{str(e)}"
        
        return jsonify({
            "status": "healthy",
            "comfyui_status": comfy_status,
            "comfyui_url": COMFY_UI_URL,
            "upload_dir": UPLOAD_DIR,
            "output_dir": OUTPUT_DIR,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        "message": "Backend is working!",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting isOGen Backend (Debug Mode)")
    print("=" * 60)
    print(f"📡 ComfyUI URL: {COMFY_UI_URL}")
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("\n🌐 Available Endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/test - Simple test")
    print("  POST /api/process-base64 - Process image (with detailed logging)")
    print("\n🔧 Debug Features:")
    print("  - Detailed error logging")
    print("  - Mock AI results")
    print("  - Connection testing")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)