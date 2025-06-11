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
    # Convert canvas background color to hex for Three.js
    canvas_bg = COLORS['canvas_background']
    if canvas_bg.startswith('#'):
        canvas_bg_hex = canvas_bg[1:]  # Remove the #
    else:
        # Handle named colors - convert to hex
        color_map = {'white': 'ffffff', 'black': '000000', 'gray': '808080', 'grey': '808080'}
        canvas_bg_hex = color_map.get(canvas_bg.lower(), 'fafafa')
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>3D Voxel Grid</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <style>
    body {
      margin: 0;
      padding: 0;
      background: """ + COLORS['main_background'] + """;
      font-family: Arial, sans-serif;
    }
    
    #canvas-container {
      width: 100%;
      height: 600px;
      border: 1px solid """ + COLORS['input_border'] + """;
      border-radius: 8px;
      background: """ + COLORS['canvas_background'] + """;
      position: relative;
      overflow: hidden;
      margin: 0;
      box-sizing: border-box;
    }
    
    .preview-cube {
      position: absolute;
      pointer-events: none;
      z-index: 1000;
    }
  </style>
</head>
<body>
  <div id="canvas-container"></div>
  
  <script>
    let scene, camera, renderer, raycaster, mouse;
    let gridObject, points = [], lines = [];
    let cellsMap = {};
    let gridSize = 10;
    let cellColor = '#4285f4';
    let arcticMode = false;
    let previewCube = null;
    let arcticMesh = null;
    
    // Initialize Three.js scene
    function initThree() {
      const container = document.getElementById('canvas-container');
      
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x""" + canvas_bg_hex + """);
      
      // Create orthographic camera for isometric view
      const aspect = container.clientWidth / container.clientHeight;
      const frustumSize = 10;
      
      camera = new THREE.OrthographicCamera(
        (frustumSize * aspect) / -2,
        (frustumSize * aspect) / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.1,
        1000
      );
      
      // Position camera for isometric view
      const distance = 15;
      camera.position.set(
        distance * Math.cos(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2))),
        distance * Math.sin(Math.atan(1/Math.sqrt(2))),
        distance * Math.sin(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2)))
      );
      camera.lookAt(0, 0, 0);
      
      renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
      renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(renderer.domElement);
      
      // Add lights
      const ambientLight = new THREE.AmbientLight(0x606060, 0.8);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(1, 1, 1);
      scene.add(directionalLight);
      
      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2();
      
      createGrid();
      createPreviewCube();
      
      // Event listeners
      renderer.domElement.addEventListener('click', onMouseClick);
      renderer.domElement.addEventListener('contextmenu', onContextMenu);
      renderer.domElement.addEventListener('mousemove', onMouseMove);
      
      animate();
    }
    
    function createGrid() {
      if (gridObject) {
        scene.remove(gridObject);
        points = [];
        lines = [];
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh && cell.mesh.parent) {
            cell.mesh.parent.remove(cell.mesh);
          }
        });
        cellsMap = {};
      }
      
      gridObject = new THREE.Group();
      scene.add(gridObject);
      
      const size = gridSize;
      const spacing = 1;
      const halfSize = (size - 1) * spacing / 2;
      
      // Create points
      for (let i = 0; i < size; i++) {
        for (let j = 0; j < size; j++) {
          const geometry = new THREE.SphereGeometry(0.05, 16, 16);
          const material = new THREE.MeshPhongMaterial({ color: 0x156289 });
          const sphere = new THREE.Mesh(geometry, material);
          
          sphere.position.set(
            i * spacing - halfSize,
            0,
            j * spacing - halfSize
          );
          
          sphere.userData = { gridX: i, gridZ: j };
          gridObject.add(sphere);
          points.push(sphere);
        }
      }
      
      // Create lines
      createGridLines(size, spacing);
    }
    
    function createGridLines(size, spacing) {
      const halfSize = (size - 1) * spacing / 2;
      
      // Horizontal lines
      for (let i = 0; i < size; i++) {
        for (let j = 0; j < size - 1; j++) {
          const pointA = points[i * size + j];
          const pointB = points[i * size + j + 1];
          createLine(pointA, pointB);
        }
      }
      
      // Vertical lines
      for (let i = 0; i < size - 1; i++) {
        for (let j = 0; j < size; j++) {
          const pointA = points[i * size + j];
          const pointB = points[(i + 1) * size + j];
          createLine(pointA, pointB);
        }
      }
    }
    
    function createLine(pointA, pointB) {
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array([
        pointA.position.x, pointA.position.y, pointA.position.z,
        pointB.position.x, pointB.position.y, pointB.position.z
      ]);
      
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const material = new THREE.LineBasicMaterial({ color: 0x888888 });
      const line = new THREE.Line(geometry, material);
      
      gridObject.add(line);
      lines.push({ line, pointA, pointB });
    }
    
    function createPreviewCube() {
      previewCube = new THREE.Group();
      
      const geometry = new THREE.BoxGeometry(0.85, 0.55, 0.85);
      const edges = new THREE.EdgesGeometry(geometry);
      const material = new THREE.LineBasicMaterial({
        color: 0xcccccc,
        transparent: true,
        opacity: 0.9,
        linewidth: 2,
        depthTest: false
      });
      
      const wireframe = new THREE.LineSegments(edges, material);
      previewCube.add(wireframe);
      
      previewCube.visible = false;
      scene.add(previewCube);
    }
    
    function onMouseMove(event) {
      updatePreview(event.clientX, event.clientY);
    }
    
    function updatePreview(clientX, clientY) {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, camera);
      
      // Check for voxel stacking
      const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
      let intersects = raycaster.intersectObjects(cellMeshes);
      
      if (intersects.length > 0) {
        const hitObject = intersects[0].object;
        for (const cell of Object.values(cellsMap)) {
          if (cell.mesh === hitObject) {
            const previewY = cell.worldPosition.y + 0.5 + 0.25;
            const newVoxelBaseY = cell.worldPosition.y + 0.5;
            const checkPos = new THREE.Vector3(cell.worldPosition.x, newVoxelBaseY, cell.worldPosition.z);
            
            if (!findCellAtPosition(checkPos)) {
              previewCube.position.set(
                cell.worldPosition.x,
                previewY,
                cell.worldPosition.z
              );
              previewCube.visible = true;
              return;
            }
            break;
          }
        }
      }
      
      // Check for ground placement
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
      const intersection = new THREE.Vector3();
      
      if (raycaster.ray.intersectPlane(groundPlane, intersection)) {
        const gridSpacing = 1;
        const halfSize = (gridSize - 1) * gridSpacing / 2;
        
        const cellI = Math.floor((intersection.x + halfSize + gridSpacing/2) / gridSpacing);
        const cellJ = Math.floor((intersection.z + halfSize + gridSpacing/2) / gridSpacing);
        
        if (cellI >= 0 && cellI < gridSize - 1 && cellJ >= 0 && cellJ < gridSize - 1) {
          const cellCenterX = (cellI * gridSpacing) - halfSize + (gridSpacing / 2);
          const cellCenterZ = (cellJ * gridSpacing) - halfSize + (gridSpacing / 2);
          
          const groundPos = new THREE.Vector3(cellCenterX, 0, cellCenterZ);
          
          if (!findCellAtPosition(groundPos)) {
            previewCube.position.set(cellCenterX, 0.25, cellCenterZ);
            previewCube.visible = true;
            return;
          }
        }
      }
      
      previewCube.visible = false;
    }
    
    function onMouseClick(event) {
      if (event.button !== 0) return;
      
      if (previewCube.visible) {
        const targetPos = new THREE.Vector3(
          previewCube.position.x,
          previewCube.position.y - 0.25,
          previewCube.position.z
        );
        createVoxel(targetPos);
      }
    }
    
    function onContextMenu(event) {
      event.preventDefault();
      
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, camera);
      const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
      const intersects = raycaster.intersectObjects(cellMeshes);
      
      if (intersects.length > 0) {
        const hitObject = intersects[0].object;
        for (const [key, cell] of Object.entries(cellsMap)) {
          if (cell.mesh === hitObject) {
            scene.remove(cell.mesh);
            delete cellsMap[key];
            if (arcticMode) {
              updateArcticMesh();
            }
            break;
          }
        }
      }
    }
    
    function createVoxel(position) {
      const gridPos = worldToGridPosition(position);
      if (!gridPos) return;
      
      const height = Math.round(position.y * 2) / 2;
      const key = `${gridPos.gridX},${gridPos.gridZ},${height}`;
      
      if (cellsMap[key]) return;
      
      const geometry = createCellGeometry(gridPos.corners, height);
      const color = new THREE.Color(cellColor);
      const material = new THREE.MeshPhongMaterial({
        color: color,
        transparent: true,
        opacity: 0.7
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      if (arcticMode) {
        mesh.visible = false;
      }
      
      cellsMap[key] = {
        gridPosition: gridPos,
        worldPosition: new THREE.Vector3(position.x, height, position.z),
        mesh,
        height
      };
      
      if (arcticMode) {
        updateArcticMesh();
      }
    }
    
    function createCellGeometry(corners, height) {
      const cellHeight = 0.5;
      const p1 = corners[0].position;
      const p2 = corners[1].position;
      const p3 = corners[2].position;
      const p4 = corners[3].position;
      
      const vertices = [
        p1.x, height, p1.z,
        p2.x, height, p2.z,
        p4.x, height, p4.z,
        p3.x, height, p3.z,
        
        p1.x, height + cellHeight, p1.z,
        p2.x, height + cellHeight, p2.z,
        p4.x, height + cellHeight, p4.z,
        p3.x, height + cellHeight, p3.z
      ];
      
      const indices = [
        0, 1, 2, 0, 2, 3,
        4, 6, 5, 4, 7, 6,
        0, 4, 1, 1, 4, 5,
        1, 5, 2, 2, 5, 6,
        2, 6, 3, 3, 6, 7,
        3, 7, 0, 0, 7, 4
      ];
      
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.setIndex(indices);
      geometry.computeVertexNormals();
      
      return geometry;
    }
    
    function findGridCell(worldX, worldZ) {
      const size = gridSize;
      
      for (let i = 0; i < size - 1; i++) {
        for (let j = 0; j < size - 1; j++) {
          const p1 = points[i * size + j];
          const p2 = points[i * size + (j + 1)];
          const p3 = points[(i + 1) * size + j];
          const p4 = points[(i + 1) * size + (j + 1)];
          
          const minX = Math.min(p1.position.x, p2.position.x, p3.position.x, p4.position.x);
          const maxX = Math.max(p1.position.x, p2.position.x, p3.position.x, p4.position.x);
          const minZ = Math.min(p1.position.z, p2.position.z, p3.position.z, p4.position.z);
          const maxZ = Math.max(p1.position.z, p2.position.z, p3.position.z, p4.position.z);
          
          if (worldX >= minX && worldX <= maxX && worldZ >= minZ && worldZ <= maxZ) {
            return { i, j, p1, p2, p3, p4 };
          }
        }
      }
      
      return null;
    }
    
    function worldToGridPosition(position) {
      const cellInfo = findGridCell(position.x, position.z);
      
      if (!cellInfo) return null;
      
      const { i, j, p1, p2, p3, p4 } = cellInfo;
      
      return {
        gridX: i,
        gridZ: j,
        localX: position.x,
        localY: position.y,
        localZ: position.z,
        corners: [p1, p2, p3, p4]
      };
    }
    
    function findCellAtPosition(position) {
      const tolerance = 0.1;
      for (const cell of Object.values(cellsMap)) {
        if (cell.worldPosition.distanceTo(position) < tolerance) {
          return cell;
        }
      }
      return null;
    }
    
    function updateArcticMesh() {
      if (!arcticMode) return;
      
      if (arcticMesh) {
        scene.remove(arcticMesh);
        arcticMesh.geometry.dispose();
        arcticMesh.material.dispose();
        arcticMesh = null;
      }
      
      const unifiedGeometry = createUnifiedGeometry();
      if (unifiedGeometry) {
        const arcticMaterial = new THREE.MeshLambertMaterial({
          color: 0xffffff,
          transparent: false,
          side: THREE.DoubleSide,
          flatShading: false
        });
        
        arcticMesh = new THREE.Mesh(unifiedGeometry, arcticMaterial);
        scene.add(arcticMesh);
      }
    }
    
    function createUnifiedGeometry() {
      if (Object.keys(cellsMap).length === 0) return null;
      
      const vertices = [];
      const indices = [];
      let vertexIndex = 0;
      
      Object.values(cellsMap).forEach(cell => {
        const positions = cell.mesh.geometry.attributes.position.array;
        const cellIndices = cell.mesh.geometry.index.array;
        
        for (let i = 0; i < positions.length; i += 3) {
          vertices.push(
            positions[i] + cell.mesh.position.x,
            positions[i + 1] + cell.mesh.position.y,
            positions[i + 2] + cell.mesh.position.z
          );
        }
        
        for (let i = 0; i < cellIndices.length; i++) {
          indices.push(cellIndices[i] + vertexIndex);
        }
        
        vertexIndex += positions.length / 3;
      });
      
      if (vertices.length === 0) return null;
      
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.setIndex(indices);
      geometry.computeVertexNormals();
      
      return geometry;
    }
    
    function animate() {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    }
    
    // Global functions for Gradio interface
    window.cleanGrid = function() {
      Object.values(cellsMap).forEach(cell => {
        if (cell.mesh) {
          scene.remove(cell.mesh);
        }
      });
      cellsMap = {};
      
      if (arcticMesh) {
        scene.remove(arcticMesh);
        arcticMesh = null;
      }
      
      if (arcticMode) {
        toggleArcticMode();
      }
    };
    
    window.setVoxelColor = function(color) {
      cellColor = color;
      const threeColor = new THREE.Color(color);
      Object.values(cellsMap).forEach(cell => {
        if (cell.mesh && cell.mesh.material) {
          cell.mesh.material.color = threeColor;
        }
      });
    };
    
    window.toggleArcticMode = function() {
      arcticMode = !arcticMode;
      
      if (arcticMode) {
        updateArcticMesh();
        
        if (gridObject) gridObject.visible = false;
        if (previewCube) previewCube.visible = false;
        
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh) cell.mesh.visible = false;
        });
        
        scene.background = new THREE.Color(0xf8fbff);
        
      } else {
        if (arcticMesh) {
          scene.remove(arcticMesh);
          arcticMesh.geometry.dispose();
          arcticMesh.material.dispose();
          arcticMesh = null;
        }
        
        if (gridObject) gridObject.visible = true;
        
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh) cell.mesh.visible = true;
        });
        
        scene.background = new THREE.Color(0x""" + canvas_bg_hex + """);
      }
      
      return arcticMode;
    };
    
    window.downloadImage = function() {
      const link = document.createElement('a');
      link.download = `voxel-model-${Date.now()}.png`;
      link.href = renderer.domElement.toDataURL();
      link.click();
      return "Image downloaded!";
    };
    
    window.download3D = function() {
      // Simple OBJ export
      let objContent = "# Voxel Model Export\\n";
      let vertexIndex = 1;
      
      Object.values(cellsMap).forEach(cell => {
        const positions = cell.mesh.geometry.attributes.position.array;
        const indices = cell.mesh.geometry.index.array;
        
        // Add vertices
        for (let i = 0; i < positions.length; i += 3) {
          objContent += `v ${positions[i]} ${positions[i + 1]} ${positions[i + 2]}\\n`;
        }
        
        // Add faces
        for (let i = 0; i < indices.length; i += 3) {
          const f1 = indices[i] + vertexIndex;
          const f2 = indices[i + 1] + vertexIndex;
          const f3 = indices[i + 2] + vertexIndex;
          objContent += `f ${f1} ${f2} ${f3}\\n`;
        }
        
        vertexIndex += positions.length / 3;
      });
      
      const blob = new Blob([objContent], { type: 'text/plain' });
      const link = document.createElement('a');
      link.download = `voxel-model-${Date.now()}.obj`;
      link.href = URL.createObjectURL(blob);
      link.click();
      return "3D model downloaded!";
    };
    
    // Initialize when page loads
    window.addEventListener('load', initThree);
  </script>
</body>
</html>
"""
    return html_content

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
    demo.launch(share=False, show_error=True, server_name="127.0.0.1", server_port=7860)