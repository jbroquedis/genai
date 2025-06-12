import gradio as gr
import json
import base64
from datetime import datetime

# COLOR CONFIGURATION - EDIT THESE VARIABLES TO CHANGE THE INTERFACE COLORS
COLORS = {
    # Main backgrounds
    'main_background': '#fafafa',
    'canvas_background': 'white',
    
    # Button colors
    'button_background': 'white',
    'button_border': '#e0e0e0',
    'button_text': '#333',
    'button_hover_bg': '#f5f5f5',
    'button_hover_border': '#d0d0d0',
    
    # Special buttons
    'color_button_bg': '#f8f9fa',
    'color_button_text': '#666',
    'color_button_hover': '#e9ecef',
    
    # Input fields
    'input_background': '#f8f9fa',
    'input_border': '#e0e0e0',
    'input_text': '#666',
    'input_placeholder': '#999',
    
    # Text colors
    'primary_text': '#333',
    'secondary_text': '#666',
    'muted_text': '#999',
    
    # Color picker
    'colorpicker_bg': '#f8f9fa',
    'colorpicker_border': '#e0e0e0',
    
    # Status elements (hidden but configurable)
    'status_bg': 'white',
    'status_border': '#e0e0e0',
    'status_text': '#666'
}

# Custom HTML component that embeds the Three.js application
def create_threejs_html():
    return """
    <iframe 
        src="http://localhost:5174"
        width="100%" 
        height="600px" 
        frameborder="0" 
        style="border: 1px solid #e0e0e0; border-radius: 8px;">
    </iframe>
    """


# Button action functions
def clean_grid():
    return "<script>window.cleanGrid && window.cleanGrid();</script>", "Grid cleaned!"

def set_voxel_color(color):
    return f"<script>window.setVoxelColor && window.setVoxelColor('{color}');</script>", f"Voxel color set to {color}"

def toggle_arctic_mode():
    return "<script>const isArctic = window.toggleArcticMode && window.toggleArcticMode(); document.getElementById('arctic-status').textContent = isArctic ? 'Arctic Mode: ON' : 'Arctic Mode: OFF';</script>", "Arctic mode toggled!"

def download_3d():
    return "<script>window.download3D && window.download3D();</script>", "3D model download initiated!"

def download_image():
    return "<script>window.downloadImage && window.downloadImage();</script>", "Image download initiated!"

def process_prompt(prompt):
    # Here you could add AI processing of the prompt to modify the 3D scene
    # For now, just return the prompt as confirmation
    return f"Processed prompt: {prompt}"

# Create the Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), css="""
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;600&display=swap');
    
    * {
        font-family: 'Noto Sans', sans-serif !important;
    }
    
    .main-container { background: """ + COLORS['main_background'] + """ !important; }
    .gradio-container { background: """ + COLORS['main_background'] + """ !important; max-width: 100% !important; }
    .block { background: """ + COLORS['main_background'] + """ !important; border: none !important; }
    .form { background: """ + COLORS['main_background'] + """ !important; }
    .container { max-width: 100% !important; }
    #threejs-canvas { width: 100vw !important; max-width: 100% !important; }
    
    button { 
        background: """ + COLORS['button_background'] + """ !important; 
        border: 1px solid """ + COLORS['button_border'] + """ !important; 
        color: """ + COLORS['button_text'] + """ !important;
        border-radius: 6px !important;
        font-weight: 400 !important;
        padding: 6px 12px !important;
        height: 32px !important;
        font-size: 13px !important;
        min-height: 32px !important;
        font-family: 'Noto Sans', sans-serif !important;
    }
    button:hover { 
        background: """ + COLORS['button_hover_bg'] + """ !important; 
        border-color: """ + COLORS['button_hover_border'] + """ !important;
    }
    
    .textbox { 
        background: """ + COLORS['input_background'] + """ !important; 
        border: 1px solid """ + COLORS['input_border'] + """ !important;
        font-family: 'Noto Sans', sans-serif !important;
        color: """ + COLORS['input_text'] + """ !important;
    }
    
    .prompt-bar input {
        background: """ + COLORS['input_background'] + """ !important;
        color: """ + COLORS['input_text'] + """ !important;
        border: 1px solid """ + COLORS['input_border'] + """ !important;
    }
    
    .prompt-bar textarea {
        background: """ + COLORS['input_background'] + """ !important;
        color: """ + COLORS['input_text'] + """ !important;
        border: 1px solid """ + COLORS['input_border'] + """ !important;
    }
    
    input[type="text"] {
        background: """ + COLORS['input_background'] + """ !important;
        color: """ + COLORS['input_text'] + """ !important;
    }
    
    textarea {
        background: """ + COLORS['input_background'] + """ !important;
        color: """ + COLORS['input_text'] + """ !important;
    }
    
    .colorpicker { 
        border: 1px solid """ + COLORS['colorpicker_border'] + """ !important; 
        border-radius: 6px !important;
        height: 32px !important;
        min-height: 32px !important;
        background: """ + COLORS['colorpicker_bg'] + """ !important;
        width: 40px !important;
        max-width: 40px !important;
    }
    
    .inline-color-group {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    .inline-color-picker {
        flex-shrink: 0 !important;
    }
    
    .color-button {
        background: """ + COLORS['color_button_bg'] + """ !important;
        color: """ + COLORS['color_button_text'] + """ !important;
        border: 1px solid """ + COLORS['button_border'] + """ !important;
        flex-shrink: 0 !important;
    }
    
    .color-button:hover {
        background: """ + COLORS['color_button_hover'] + """ !important;
    }
    
    .gradio-row { width: 100% !important; }
    
    /* Hide the unwanted status/output areas */
    .output-class { display: none !important; }
    .status-output { display: none !important; }
    
    /* Force all text elements to use Noto Sans and proper colors */
    h1, h2, h3, h4, h5, h6 { 
        font-family: 'Noto Sans', sans-serif !important;
        color: """ + COLORS['primary_text'] + """ !important;
    }
    
    p, span, div, label { 
        font-family: 'Noto Sans', sans-serif !important;
        color: """ + COLORS['secondary_text'] + """ !important;
    }
    
    input {
        font-family: 'Noto Sans', sans-serif !important;
        color: """ + COLORS['input_text'] + """ !important;
    }
    
    /* Status output styling (hidden but configurable) */
    .status-output {
        background: """ + COLORS['status_bg'] + """ !important;
        border: 1px solid """ + COLORS['status_border'] + """ !important;
        font-family: 'Noto Sans', sans-serif !important;
        color: """ + COLORS['status_text'] + """ !important;
    }
    
    /* Placeholder text color */
    input::placeholder, textarea::placeholder {
        color: """ + COLORS['input_placeholder'] + """ !important;
    }
""") as demo:
    
    gr.Markdown("# isOGen", elem_classes="main-header")
    
    # Main 3D canvas area (full width)
    with gr.Row():
        canvas = gr.HTML(
            value=create_threejs_html(), 
            elem_id="threejs-canvas",
            show_label=False
        )
    
    # Prompt bar (screen wide)
    with gr.Row():
        prompt_input = gr.Textbox(
            placeholder="Enter your prompt to modify the generated building...",
            show_label=False,
            scale=4,
            elem_classes="prompt-bar"
        )
        process_btn = gr.Button("Process", scale=1)
    
    # Button row - Clean and evenly distributed
    with gr.Row(equal_height=True):
        clean_btn = gr.Button("Clean Grid", variant="secondary")
        arctic_btn = gr.Button("Arctic Mode", variant="secondary")
        download_3d_btn = gr.Button("Download 3D", variant="secondary")
        download_img_btn = gr.Button("Download Image", variant="secondary")
    
    # Status area (hidden but kept for functionality)
    with gr.Row(visible=False):
        status_output = gr.Textbox(label="Status", interactive=False, show_label=False, elem_classes="status-output")
        arctic_status = gr.HTML("<div id='arctic-status' style='font-family: Noto Sans, sans-serif; display: none;'>Arctic Mode: OFF</div>")
    
    # Event handlers
    clean_btn.click(
        clean_grid, 
        outputs=[canvas, status_output]
    )
    
    arctic_btn.click(
        toggle_arctic_mode,
        outputs=[canvas, status_output]
    )
    
    download_3d_btn.click(
        download_3d,
        outputs=[canvas, status_output]
    )
    
    download_img_btn.click(
        download_image,
        outputs=[canvas, status_output]
    )
    
    process_btn.click(
        process_prompt,
        inputs=[prompt_input],
        outputs=[status_output]
    )

# Launch the interface
if __name__ == "__main__":
    demo.launch(share=False, show_error=True)
