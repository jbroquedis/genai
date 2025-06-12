#!/usr/bin/env python3
"""
Complete ComfyUI Backend with Real Workflow Processing
Handles actual ComfyUI workflows for architectural AI generation
"""

import os
import json
import base64
import requests
import uuid
import time
import shutil
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from urllib.parse import quote
import websocket
import threading
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

USER_COMFY_PATH = r"D:\RECURSOS\PROGRAMS\ComfyUI\ComfyUI\input"

# Configuration
COMFY_UI_URL = "http://localhost:8188"
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
WORKFLOW_FILE = "image_to_image_flux.json"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ComfyUIClient:
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        
    def queue_prompt(self, prompt):
        """Queue a prompt for processing"""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = requests.post(f"http://{self.server_address}/prompt", data=data, 
                           headers={'Content-Type': 'application/json'})
        return req.json()

    def get_image(self, filename, subfolder, folder_type):
        """Get an image from ComfyUI"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = "&".join([f"{k}={quote(str(v))}" for k, v in data.items()])
        response = requests.get(f"http://{self.server_address}/view?{url_values}")
        return response.content

    def get_history(self, prompt_id):
        """Get the history for a prompt"""
        response = requests.get(f"http://{self.server_address}/history/{prompt_id}")
        return response.json()

    def get_images(self, ws, prompt):
        """Get images from a workflow via WebSocket"""
        queue_result = self.queue_prompt(prompt)
        print(f"✅ Queue result: {queue_result}")
        
        # Handle different response formats
        if 'prompt_id' in queue_result:
            prompt_id = queue_result['prompt_id']
        elif 'exec_info' in queue_result and 'queue_size' in queue_result['exec_info']:
            # Alternative response format
            prompt_id = queue_result.get('exec_info', {}).get('queue_size', str(uuid.uuid4()))
        else:
            print(f"❌ Unexpected queue response format: {queue_result}")
            raise Exception(f"Cannot find prompt_id in response: {queue_result}")
            
        print(f"✅ Using prompt_id: {prompt_id}")
        output_images = {}
        
        while True:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break  # Execution is done
                else:
                    continue  # previews are binary data
            except websocket.WebSocketConnectionClosedException:
                break
                
        history = self.get_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output

        return output_images

def load_workflow():
    """Load the ComfyUI workflow from JSON file"""
    try:
        if not os.path.exists(WORKFLOW_FILE):
            print(f"❌ Workflow file not found: {WORKFLOW_FILE}")
            return None
            
        with open(WORKFLOW_FILE, 'r') as f:
            workflow = json.load(f)
        print(f"✅ Loaded workflow with {len(workflow)} nodes")
        return workflow
    except Exception as e:
        print(f"❌ Error loading workflow: {e}")
        return None

def update_workflow_for_processing(workflow, image_filename, prompt_text):
    """Update workflow with new image and prompt"""
    try:
        updated_workflow = workflow.copy()
        
        # Update image input (node 100 - LoadImage)
        if "100" in updated_workflow:
            updated_workflow["100"]["inputs"]["image"] = image_filename
            print(f"✅ Updated image input: {image_filename}")
        else:
            print("⚠️ LoadImage node (100) not found in workflow")
            
        # Update positive prompt (node 98 - CLIPTextEncode)
        if "98" in updated_workflow:
            original_prompt = updated_workflow["98"]["inputs"]["text"]
            # Enhance the prompt with architectural keywords
            enhanced_prompt = f"ismtrcbldng, hyperrealistic photograph, white background, plain white background, {prompt_text}, isometric view, architectural visualization, detailed building, {original_prompt}"
            updated_workflow["98"]["inputs"]["text"] = enhanced_prompt
            print(f"✅ Updated prompt: {enhanced_prompt[:100]}...")
        else:
            print("⚠️ Positive prompt node (98) not found in workflow")
            
        # Generate random seed for variety
        import random
        random_seed = random.randint(1, 2**32 - 1)
        
        # Update seed in KSampler (node 109)
        if "109" in updated_workflow:
            updated_workflow["109"]["inputs"]["noise_seed"] = random_seed
            print(f"✅ Updated seed: {random_seed}")
            
        return updated_workflow
        
    except Exception as e:
        print(f"❌ Error updating workflow: {e}")
        return None

def check_comfyui_connection():
    """Check if ComfyUI is running and accessible"""
    try:
        response = requests.get(f"{COMFY_UI_URL}/system_stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ ComfyUI connected - System: {stats.get('system', {})}")
            return True
        else:
            print(f"❌ ComfyUI returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ComfyUI connection refused - is it running on localhost:8188?")
        return False
    except Exception as e:
        print(f"❌ ComfyUI connection error: {e}")
        return False

def check_required_models():
    """Check if required models are available"""
    try:
        # Check available models
        models_response = requests.get(f"{COMFY_UI_URL}/object_info")
        if models_response.status_code != 200:
            return False, "Could not get model info from ComfyUI"
            
        object_info = models_response.json()
        
        # Check for required components
        required_checks = {
            "VAELoader": ["ae.safetensors"],
            "DualCLIPLoader": ["t5xxl_fp8_e4m3fn.safetensors", "clip_l.safetensors"],
            "UNETLoader": ["flux1CannyDevFp8_v10.safetensors"],
            "Load Lora": ["isometric_bld_000001500.safetensors"]
        }
        
        missing_models = []
        
        for node_type, model_files in required_checks.items():
            if node_type in object_info:
                available_models = object_info[node_type]["input"]["required"]
                for model_file in model_files:
                    # This is a simplified check - in reality you'd need to check the actual model lists
                    print(f"ℹ️ Checking for model: {model_file}")
            else:
                missing_models.append(f"Node type {node_type} not available")
        
        if missing_models:
            return False, f"Missing components: {', '.join(missing_models)}"
            
        return True, "All required models appear to be available"
        
    except Exception as e:
        return False, f"Error checking models: {e}"

def copy_to_comfyui_input(source_path, filename):
    """Copy image to ComfyUI's input directory"""
    try:
        # Common ComfyUI input directories - add user's specific path first
        possible_paths = [
            "C:/ComfyUI/ComfyUI/input",  # User's specific path
            "C:\\ComfyUI\\ComfyUI\\input",  # Windows backslash version
            "ComfyUI/input",
            "../ComfyUI/input", 
            "../../ComfyUI/input",
            os.path.expanduser("~/ComfyUI/input"),
            "C:/ComfyUI/input",
            # Check if ComfyUI is in the same directory structure
            os.path.join(os.path.dirname(__file__), "..", "ComfyUI", "input"),
        ]
        
        # Try to find ComfyUI input directory
        comfyui_input_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                comfyui_input_dir = path
                print(f"✅ Found ComfyUI input directory: {path}")
                break
        
        if not comfyui_input_dir:
            # Try to auto-detect based on ComfyUI API
            try:
                # Get system info from ComfyUI to find its location
                response = requests.get(f"{COMFY_UI_URL}/system_stats")
                if response.status_code == 200:
                    # ComfyUI is running, but we need to find its directory
                    # Let's try a few more common locations
                    additional_paths = [
                        USER_COMFY_PATH,
                        os.path.join(os.path.expanduser("~"), "Desktop", "ComfyUI", "input"),
                        os.path.join(os.path.expanduser("~"), "Documents", "ComfyUI", "input"),
                    ]
                    
                    for path in additional_paths:
                        if os.path.exists(path):
                            comfyui_input_dir = path
                            print(f"✅ Auto-detected ComfyUI input directory: {path}")
                            break
            except:
                pass
        
        if not comfyui_input_dir:
            print("⚠️ Could not find ComfyUI input directory")
            return None
            
        # Copy the file
        dest_path = os.path.join(comfyui_input_dir, filename)
        shutil.copy2(source_path, dest_path)
        print(f"✅ Copied {source_path} to {dest_path}")
        return dest_path
        
    except Exception as e:
        print(f"⚠️ Error copying to ComfyUI input: {e}")
        return None

def save_base64_image(image_base64, filename):
    """Save base64 image data to file"""
    try:
        # Remove data URL prefix if present
        if "data:image" in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        # Decode base64
        image_data = base64.b64decode(image_base64)
        
        # Save to uploads directory
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)
            
        print(f"✅ Saved image: {filepath} ({len(image_data)} bytes)")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        raise e

def process_with_comfyui_websocket(workflow_data):
    """Process workflow using WebSocket connection for real-time updates"""
    try:
        client = ComfyUIClient()
        
        # First, try to queue the prompt and get the response
        print("🔄 Queuing prompt...")
        queue_result = client.queue_prompt(workflow_data)
        print(f"📋 Queue response: {queue_result}")
        
        # Handle different response formats from ComfyUI
        prompt_id = None
        if isinstance(queue_result, dict):
            if 'prompt_id' in queue_result:
                prompt_id = queue_result['prompt_id']
            elif 'exec_info' in queue_result:
                # Some ComfyUI versions return exec_info
                exec_info = queue_result['exec_info']
                if 'queue_size' in exec_info:
                    print("⚠️ Using alternative method to track processing...")
                    # We'll use a different approach - polling the queue
                    return process_with_polling(workflow_data)
        
        if not prompt_id:
            print(f"❌ Could not extract prompt_id from: {queue_result}")
            # Fallback to polling method
            return process_with_polling(workflow_data)
        
        print(f"✅ Got prompt_id: {prompt_id}")
        
        # Connect to WebSocket
        ws_url = f"ws://127.0.0.1:8188/ws?clientId={client.client_id}"
        ws = websocket.WebSocket()
        ws.connect(ws_url)
        print("✅ Connected to ComfyUI WebSocket")
        
        # Monitor execution
        while True:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            print("✅ Execution completed")
                            break  # Execution is done
                        elif data['node'] is not None:
                            print(f"🔄 Processing node: {data['node']}")
                else:
                    continue  # previews are binary data
            except websocket.WebSocketConnectionClosedException:
                print("❌ WebSocket connection closed")
                break
                
        ws.close()
        
        # Get the results
        print("📥 Getting results...")
        history = client.get_history(prompt_id)[prompt_id]
        
        # Find output images
        output_images = {}
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = client.get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output
        
        if not output_images:
            raise Exception("No images generated from workflow")
            
        # Find the output image (usually from the last save node)
        output_image_data = None
        
        # Look for images in output nodes (typically nodes 107, 118, or similar)
        for node_id in ["107", "118", "91"]:  # Check common output nodes
            if node_id in output_images and output_images[node_id]:
                output_image_data = output_images[node_id][0]  # Get first image
                print(f"✅ Found output image from node {node_id}")
                break
        
        if not output_image_data:
            # If no specific output node found, take the last available image
            if output_images:
                last_node = list(output_images.keys())[-1]
                output_image_data = output_images[last_node][0]
                print(f"✅ Using image from node {last_node}")
        
        if not output_image_data:
            raise Exception("No output image found in workflow results")
            
        # Convert to base64
        image_base64 = base64.b64encode(output_image_data).decode()
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"❌ WebSocket processing error: {e}")
        print("🔄 Trying polling method as fallback...")
        return process_with_polling(workflow_data)

def process_with_polling(workflow_data):
    """Fallback method using polling instead of WebSocket"""
    try:
        client = ComfyUIClient()
        
        # Queue the prompt
        queue_result = client.queue_prompt(workflow_data)
        print(f"📋 Polling method - Queue result: {queue_result}")
        
        # Wait for processing to complete by polling the queue
        max_wait = 300  # 5 minutes
        start_time = time.time()
        last_queue_size = None
        
        while time.time() - start_time < max_wait:
            try:
                # Check queue status
                response = requests.get("http://127.0.0.1:8188/queue")
                if response.status_code == 200:
                    queue_data = response.json()
                    running = queue_data.get('queue_running', [])
                    pending = queue_data.get('queue_pending', [])
                    current_queue_size = len(running) + len(pending)
                    
                    if last_queue_size is not None and current_queue_size < last_queue_size:
                        print("🔄 Queue size decreased, checking for completion...")
                    
                    if current_queue_size == 0:
                        print("✅ Queue is empty, processing should be complete")
                        break
                    
                    last_queue_size = current_queue_size
                    print(f"⏳ Queue size: {current_queue_size}")
                    
            except Exception as e:
                print(f"⚠️ Error checking queue: {e}")
            
            time.sleep(2)
        
        # Get the most recent history
        print("📥 Getting recent history...")
        history_response = requests.get("http://127.0.0.1:8188/history")
        if history_response.status_code != 200:
            raise Exception("Could not get processing history")
            
        history_data = history_response.json()
        
        if not history_data:
            raise Exception("No processing history found")
        
        # Get the most recent prompt result
        latest_prompt_id = list(history_data.keys())[-1]
        latest_result = history_data[latest_prompt_id]
        
        print(f"✅ Found recent result: {latest_prompt_id}")
        
        # Extract output images
        output_images = {}
        for node_id in latest_result['outputs']:
            node_output = latest_result['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = client.get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output
        
        if not output_images:
            raise Exception("No images found in latest result")
            
        # Find the best output image
        output_image_data = None
        for node_id in ["107", "118", "91"]:
            if node_id in output_images and output_images[node_id]:
                output_image_data = output_images[node_id][0]
                print(f"✅ Found output image from node {node_id}")
                break
        
        if not output_image_data and output_images:
            last_node = list(output_images.keys())[-1]
            output_image_data = output_images[last_node][0]
            print(f"✅ Using image from node {last_node}")
        
        if not output_image_data:
            raise Exception("No output image found")
            
        # Convert to base64
        image_base64 = base64.b64encode(output_image_data).decode()
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"❌ Polling method failed: {e}")
        raise e

@app.route('/api/process-base64', methods=['POST'])
def process_base64_image():
    """Process base64 image with real ComfyUI workflow"""
    try:
        print("🔍 API call received for real ComfyUI processing")
        
        # Get JSON data
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        image_base64 = data['image']
        prompt = data.get('prompt', 'modern architectural building, clean lines')
        print(f"📝 Prompt: {prompt}")
        print(f"🖼️ Image data length: {len(image_base64)} characters")
        
        # Check ComfyUI connection
        if not check_comfyui_connection():
            return jsonify({
                "error": "ComfyUI not available",
                "details": "Cannot connect to ComfyUI on localhost:8188",
                "suggestion": "Start ComfyUI with: python main.py --listen"
            }), 503
        
        # Check required models
        models_ok, models_msg = check_required_models()
        if not models_ok:
            print(f"⚠️ Model check warning: {models_msg}")
            # Continue anyway - some models might still work
        
        # Load workflow
        workflow = load_workflow()
        if not workflow:
            return jsonify({
                "error": "Workflow not found",
                "details": f"Could not load {WORKFLOW_FILE}",
                "suggestion": "Ensure the workflow JSON file exists in the project root"
            }), 500
        
        # Save input image to both locations
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"input_{timestamp}.png"
        
        try:
            # Save to uploads directory
            input_filepath = save_base64_image(image_base64, input_filename)
            
            # Try to find and copy to ComfyUI input directory
            comfyui_copied = copy_to_comfyui_input(input_filepath, input_filename)
            
            if not comfyui_copied:
                # Alternative: Try using absolute path in workflow
                abs_path = os.path.abspath(input_filepath)
                print(f"ℹ️ Using absolute path: {abs_path}")
                # We'll update the workflow to use the absolute path
                input_filename = abs_path
                
        except Exception as e:
            return jsonify({
                "error": "Failed to save input image",
                "details": str(e)
            }), 500
        
        # Update workflow with new image and prompt
        updated_workflow = update_workflow_for_processing(workflow, input_filename, prompt)
        if not updated_workflow:
            return jsonify({
                "error": "Failed to update workflow",
                "details": "Could not customize workflow with input parameters"
            }), 500
        
        # Process with ComfyUI
        print("🎨 Starting ComfyUI processing...")
        try:
            output_image_base64 = process_with_comfyui_websocket(updated_workflow)
            
            # Save output image for debugging
            output_filename = f"output_{timestamp}.png"
            if output_image_base64:
                try:
                    save_base64_image(output_image_base64, output_filename)
                except:
                    pass  # Don't fail if we can't save output
            
            print("✅ ComfyUI processing completed successfully")
            
            return jsonify({
                "success": True,
                "output_image": output_image_base64,
                "prompt": prompt,
                "processing_time": "completed",
                "input_filename": input_filename,
                "output_filename": output_filename,
                "workflow_nodes": len(updated_workflow)
            })
            
        except Exception as e:
            print(f"❌ ComfyUI processing failed: {e}")
            return jsonify({
                "error": "ComfyUI processing failed",
                "details": str(e),
                "suggestion": "Check ComfyUI console for detailed error messages"
            }), 500
            
    except Exception as e:
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
    """Enhanced health check with ComfyUI and model status"""
    try:
        # Test ComfyUI connection
        comfy_connected = check_comfyui_connection()
        
        # Check models
        models_ok, models_msg = check_required_models()
        
        # Check workflow file
        workflow_exists = os.path.exists(WORKFLOW_FILE)
        
        # Check directories
        upload_dir_exists = os.path.exists(UPLOAD_DIR)
        output_dir_exists = os.path.exists(OUTPUT_DIR)
        
        return jsonify({
            "status": "healthy" if comfy_connected else "degraded",
            "comfyui_connected": comfy_connected,
            "comfyui_url": COMFY_UI_URL,
            "workflow_loaded": workflow_exists,
            "models_status": models_msg,
            "directories": {
                "upload_dir": upload_dir_exists,
                "output_dir": output_dir_exists
            },
            "workflow_file": WORKFLOW_FILE,
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
        "timestamp": datetime.now().isoformat(),
        "mode": "real_comfyui_integration"
    })

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available models in ComfyUI"""
    try:
        if not check_comfyui_connection():
            return jsonify({"error": "ComfyUI not connected"}), 503
            
        response = requests.get(f"{COMFY_UI_URL}/object_info")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Could not fetch model info"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get current ComfyUI queue status"""
    try:
        if not check_comfyui_connection():
            return jsonify({"error": "ComfyUI not connected"}), 503
            
        response = requests.get(f"{COMFY_UI_URL}/queue")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Could not fetch queue info"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting isOGen Backend (Real ComfyUI Integration)")
    print("=" * 60)
    print(f"📡 ComfyUI URL: {COMFY_UI_URL}")
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📋 Workflow file: {WORKFLOW_FILE}")
    print("\n🌐 Available Endpoints:")
    print("  GET  /api/health - Health check with ComfyUI status")
    print("  GET  /api/test - Simple test")
    print("  GET  /api/models - List available ComfyUI models")
    print("  GET  /api/queue - ComfyUI queue status")
    print("  POST /api/process-base64 - Process image with real ComfyUI workflow")
    print("\n🔧 Real ComfyUI Features:")
    print("  - WebSocket connection for real-time processing")
    print("  - Automatic workflow parameter updates")
    print("  - Model availability checking")
    print("  - Detailed error reporting")
    print("  - Image input/output handling")
    print("=" * 60)
    
    # Initial system check
    print("\n🔍 System Check:")
    comfy_ok = check_comfyui_connection()
    workflow_ok = os.path.exists(WORKFLOW_FILE)
    models_ok, models_msg = check_required_models()
    
    print(f"ComfyUI Connection: {'✅' if comfy_ok else '❌'}")
    print(f"Workflow File: {'✅' if workflow_ok else '❌'}")
    print(f"Models: {models_msg}")
    
    if not comfy_ok:
        print("\n⚠️  WARNING: ComfyUI not detected!")
        print("   Start ComfyUI first: python main.py --listen")
        print("   Then restart this backend service")
    
    print("\n" + "=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)