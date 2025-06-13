<template>
  <div class="grid-container">
    <!-- Main 3D Canvas -->
    <div id="canvas-container" ref="canvasContainer" v-show="currentView === 'editor'"></div>

    <!-- Comparison View -->
    <div v-if="currentView === 'comparison'" class="comparison-container">
      <ComparisonSlider 
        :before-image="currentSnapshot" 
        :after-image="generatedImage"
        @back-to-editor="currentView = 'editor'"
      />
    </div>

    <!-- Processing Modal -->
    <ProcessingModal v-if="isProcessing" :stage="processingStage" />

    <!-- Unified Controls -->
    <div class="controls">
      <button @click="resetGrid">Reset Grid</button>

      <label>Grid Size: {{ gridSize }}x{{ gridSize }}</label>
      <input type="range" min="2" max="20" v-model.number="gridSize" @change="regenerateGrid" />

      <label for="colorPicker">Cell Color:</label>
      <input type="color" id="colorPicker" v-model="cellColor" @change="updateCellColors" />

      <!-- <button @click="createParallelLine">Create Parallel Line</button> -->

      <button @click="toggleArcticMode" :class="{ 'arctic-active': arcticMode }">
        {{ arcticMode ? 'Exit Arctic Mode' : 'Arctic Mode' }}
      </button>

      <input 
        v-model="aiPrompt" 
        type="text" 
        placeholder="Enter architectural style prompt..."
        class="prompt-input"
      />
      <button 
        @click="generateAIBuilding" 
        :disabled="isProcessing || Object.keys(cellsMap).length === 0"
        class="generate-btn"
      >
        {{ isProcessing ? 'Processing...' : 'Generate AI Building' }}
      </button>

      <button @click="downloadSnapshot">Download Image</button>
      <button @click="downloadOBJ" :disabled="Object.keys(cellsMap).length === 0">Download 3D Model</button>
    </div>
  </div>
</template>


<script>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { DragControls } from 'three/examples/jsm/controls/DragControls.js';
import { OBJExporter } from 'three/examples/jsm/exporters/OBJExporter.js';
import ComparisonSlider from './ComparisonSlider.vue';
import ProcessingModal from './ProcessingModal.vue';

export default {
  name: 'DraggableGrid',
  components: {
    ComparisonSlider,
    ProcessingModal
  },
  setup() {
    // Reactive Vue variables
    const canvasContainer = ref(null);
    const gridSize = ref(10);
    const cellColor = ref('#ffffff');
    const arcticMode = ref(false);
    const aiPrompt = ref('prompt . . .');
    const currentView = ref('editor');
    const isProcessing = ref(false);
    const processingStage = ref('');
    const currentSnapshot = ref('');
    const generatedImage = ref('');
    const cellsMap = ref({});
    const selectedPoints = ref([]);
    const parallelLines = ref([]);
    
    // Non-reactive Three.js variables
    let scene, camera, renderer, orbitControls, dragControls, raycaster, mouse;
    let points = [];
    let lines = [];
    let gridObject;
    let isMouseDown = false;
    let mouseDownTime = 0;
    let parallelLineGroup = new THREE.Group();
    let arcticMesh = null;
    let previewCube = null;
    
    const COMFY_API_URL = 'http://localhost:5000';
    
    const initThree = () => {
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);
      
      const aspect = canvasContainer.value.clientWidth / canvasContainer.value.clientHeight;
      const frustumSize = 10;
      
      camera = new THREE.OrthographicCamera(
        (frustumSize * aspect) / -2,
        (frustumSize * aspect) / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.1,
        1000
      );
      
      const distance = 15;
      camera.position.set(
        distance * Math.cos(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2))),
        distance * Math.sin(Math.atan(1/Math.sqrt(2))),
        distance * Math.sin(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2)))
      );
      camera.lookAt(0, 0, 0);
      
      renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
      renderer.setSize(canvasContainer.value.clientWidth, canvasContainer.value.clientHeight);
      canvasContainer.value.appendChild(renderer.domElement);
      
      const loader = new THREE.CubeTextureLoader();
      const envMap = loader.load([
        'px.jpg', 'nx.jpg',
        'py.jpg', 'ny.jpg',
        'pz.jpg', 'nz.jpg'
      ]);
      scene.environment = envMap;
      //scene.background = envMap; // optional


      const ambientLight = new THREE.AmbientLight(0x404040);
      ambientLight.name = 'ambientLight';
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
      directionalLight.position.set(1, 1, 1);
      scene.add(directionalLight);
      
      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2();
      
      orbitControls = new OrbitControls(camera, renderer.domElement);
      orbitControls.enableDamping = true;
      orbitControls.dampingFactor = 0.05;
      orbitControls.enabled = false;
      orbitControls.enableZoom = true;
      orbitControls.enablePan = true;
      
      scene.add(parallelLineGroup);
      createPreviewCube();
      createGrid();
      setupDragControls();
      
      renderer.domElement.addEventListener('mousedown', onMouseDown);
      renderer.domElement.addEventListener('mouseup', onMouseUp);
      renderer.domElement.addEventListener('click', onMouseClick);
      renderer.domElement.addEventListener('contextmenu', onContextMenu);
      renderer.domElement.addEventListener('mousemove', onMouseMove);
      
      animate();
    };
    
    const createPreviewCube = () => {
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
    };
    
    const onMouseMove = (event) => {
      if (!isMouseDown && !arcticMode.value) {
        updatePreview(event.clientX, event.clientY);
      }
    };
    
    const updatePreview = (clientX, clientY) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, camera);
      
      const cellMeshes = Object.values(cellsMap.value).map(cell => cell.mesh);
      let intersects = raycaster.intersectObjects(cellMeshes);
      
      if (intersects.length > 0) {
        const hitObject = intersects[0].object;
        for (const cell of Object.values(cellsMap.value)) {
          if (cell.mesh === hitObject) {
            const previewY = cell.worldPosition.y + 0.5 + 0.25;
            const newVoxelBaseY = cell.worldPosition.y + 0.5;
            const checkPos = new THREE.Vector3(cell.worldPosition.x, newVoxelBaseY, cell.worldPosition.z);
            
            if (!findCellAtPosition(checkPos)) {
              previewCube.position.set(cell.worldPosition.x, previewY, cell.worldPosition.z);
              previewCube.visible = true;
              return;
            }
            break;
          }
        }
      }
      
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
      const intersection = new THREE.Vector3();
      
      if (raycaster.ray.intersectPlane(groundPlane, intersection)) {
        const gridSpacing = 1;
        const halfSize = (gridSize.value - 1) * gridSpacing / 2;
        
        const cellI = Math.floor((intersection.x + halfSize + gridSpacing/2) / gridSpacing);
        const cellJ = Math.floor((intersection.z + halfSize + gridSpacing/2) / gridSpacing);
        
        if (cellI >= 0 && cellI < gridSize.value - 1 && cellJ >= 0 && cellJ < gridSize.value - 1) {
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
    };

    const findCellAtPosition = (position) => {
      const tolerance = 0.1;
      for (const cell of Object.values(cellsMap.value)) {
        if (cell.worldPosition.distanceTo(position) < tolerance) {
          return cell;
        }
      }
      return null;
    };
    
    const setupDragControls = () => {
      if (dragControls) {
        dragControls.deactivate();
        dragControls.dispose();
      }
      
      const draggableObjects = [...points];
      parallelLines.value.forEach(plObj => {
        if (plObj.handle) {
          draggableObjects.push(plObj.handle);
        }
      });
      
      dragControls = new DragControls(draggableObjects, camera, renderer.domElement);
      
      dragControls.addEventListener('dragstart', (event) => {
        orbitControls.enabled = false;
        const parallelLine = parallelLines.value.find(pl => pl.handle === event.object);
        if (parallelLine) {
          parallelLine.isDragging = true;
        }
      });
      
      dragControls.addEventListener('drag', (event) => {
        event.object.position.y = 0;
        
        const isGridPoint = points.includes(event.object);
        if (isGridPoint) {
          updateLines();
          updateCells();
          updateParallelLinesFromPoints();
        } else {
          const parallelLine = parallelLines.value.find(pl => pl.handle === event.object);
          if (parallelLine && parallelLine.isDragging) {
            const offset = event.object.position.clone().sub(parallelLine.lastPosition);
            offset.y = 0;
            parallelLine.lastPosition.copy(event.object.position);
            
            for (let i = 0; i < parallelLine.points.length; i++) {
              const newPos = parallelLine.points[i].position.clone().add(offset);
              newPos.y = 0;
              parallelLine.points[i].position.copy(newPos);
            }
            
            updateParallelLine(parallelLine);
            updateLines();
            updateCells();
          }
        }
      });
      
      dragControls.addEventListener('dragend', (event) => {
        orbitControls.enabled = false;
        const parallelLine = parallelLines.value.find(pl => pl.handle === event.object);
        if (parallelLine) {
          parallelLine.isDragging = false;
        }
      });
    };
    
    const createGrid = () => {
      if (gridObject) {
        scene.remove(gridObject);
        points = [];
        lines = [];
        Object.values(cellsMap.value).forEach(cell => {
          if (cell.mesh && cell.mesh.parent) {
            cell.mesh.parent.remove(cell.mesh);
          }
        });
        cellsMap.value = {};
      }
      
      gridObject = new THREE.Group();
      scene.add(gridObject);
      
      const size = gridSize.value;
      const spacing = 1;
      const halfSize = (size - 1) * spacing / 2;
      
      for (let i = 0; i < size; i++) {
        for (let j = 0; j < size; j++) {
          const geometry = new THREE.SphereGeometry(0.08, 16, 16);
          const material = new THREE.MeshPhongMaterial({ 
             color: 0xbbbbbb,           // Light gray
             emissive: 0x444444,        // Subtle glow
             shininess: 60              // Slight gloss to catch light


          });
          const sphere = new THREE.Mesh(geometry, material);
          
          sphere.position.set(i * spacing - halfSize, 0, j * spacing - halfSize);
          sphere.userData = { gridX: i, gridZ: j };
          
          gridObject.add(sphere);
          points.push(sphere);
        }
      }
      
      for (let i = 0; i < size; i++) {
        for (let j = 0; j < size - 1; j++) {
          const pointA = points[i * size + j];
          const pointB = points[i * size + j + 1];
          
          const geometry = new THREE.BufferGeometry();
          const positions = new Float32Array([
            pointA.position.x, pointA.position.y, pointA.position.z,
            pointB.position.x, pointB.position.y, pointB.position.z
          ]);
          
          geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const material = new THREE.LineBasicMaterial({ color: 0xcccccc });
          const line = new THREE.Line(geometry, material);
          
          gridObject.add(line);
          lines.push({ line, pointA, pointB });
        }
      }
      
      for (let i = 0; i < size - 1; i++) {
        for (let j = 0; j < size; j++) {
          const pointA = points[i * size + j];
          const pointB = points[(i + 1) * size + j];
          
          const geometry = new THREE.BufferGeometry();
          const positions = new Float32Array([
            pointA.position.x, pointA.position.y, pointA.position.z,
            pointB.position.x, pointB.position.y, pointB.position.z
          ]);
          
          geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const material = new THREE.LineBasicMaterial({ color: 0xcccccc });
          const line = new THREE.Line(geometry, material);
          
          gridObject.add(line);
          lines.push({ line, pointA, pointB });
        }
      }
      
      selectedPoints.value = [];
      parallelLines.value.forEach(pl => {
        if (pl.line && pl.line.parent) {
          pl.line.parent.remove(pl.line);
        }
        if (pl.handle && pl.handle.parent) {
          pl.handle.parent.remove(pl.handle);
        }
      });
      parallelLines.value = [];
      
      setupDragControls();
    };
    
    const onMouseClick = (event) => {
      if (event.button !== 0) return;
      
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(points);
      
      if (intersects.length > 0) {
        const clickedPoint = intersects[0].object;
        const index = selectedPoints.value.indexOf(clickedPoint);
        if (index === -1) {
          selectedPoints.value.push(clickedPoint);
          clickedPoint.material.color.set('#ff830f');
        } else {
          selectedPoints.value.splice(index, 1);
          clickedPoint.material.color.set(0xe0e0e0);
        }
      }
    };
    
    const createParallelLine = () => {
      if (selectedPoints.value.length < 3) {
        alert("Need at least 3 points to create a parallel line");
        return;
      }
      
      const positions = [];
      selectedPoints.value.forEach(point => {
        positions.push(point.position.x, point.position.y, point.position.z);
      });
      
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      const material = new THREE.LineBasicMaterial({ color: '#ff830f', linewidth: 2 });
      const lineMesh = new THREE.Line(geometry, material);
      parallelLineGroup.add(lineMesh);
      
      const handleGeom = new THREE.SphereGeometry(0.1, 16, 16);
      const handleMat = new THREE.MeshPhongMaterial({ color: '#ff830f' });
      const handle = new THREE.Mesh(handleGeom, handleMat);
      
      const center = new THREE.Vector3();
      selectedPoints.value.forEach(point => {
        center.add(point.position);
      });
      center.divideScalar(selectedPoints.value.length);
      handle.position.copy(center);
      
      parallelLineGroup.add(handle);
      
      const parallelLine = {
        line: lineMesh,
        handle: handle,
        points: [...selectedPoints.value],
        lastPosition: handle.position.clone(),
        isDragging: false
      };
      
      parallelLines.value.push(parallelLine);
      
      selectedPoints.value.forEach(point => {
        point.material.color.set('#ff830f');
      });
      selectedPoints.value = [];
      
      setupDragControls();
    };
    
    const updateParallelLine = (parallelLine) => {
      const positions = [];
      parallelLine.points.forEach(point => {
        point.position.y = 0;
        positions.push(point.position.x, 0, point.position.z);
      });
      
      parallelLine.line.geometry.setAttribute(
        'position', 
        new THREE.Float32BufferAttribute(positions, 3)
      );
      parallelLine.line.geometry.attributes.position.needsUpdate = true;
      
      const center = new THREE.Vector3();
      parallelLine.points.forEach(point => {
        center.add(point.position);
      });
      center.divideScalar(parallelLine.points.length);
      center.y = 0;
      
      if (!parallelLine.isDragging) {
        parallelLine.handle.position.copy(center);
        parallelLine.lastPosition.copy(center);
      } else {
        parallelLine.handle.position.y = 0;
        parallelLine.lastPosition.y = 0;
      }
    };
    
    const updateParallelLinesFromPoints = () => {
      parallelLines.value.forEach(parallelLine => {
        updateParallelLine(parallelLine);
      });
    };
    
    const findGridCell = (worldX, worldZ) => {
      const size = gridSize.value;
      
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
    };
    
    const worldToGridPosition = (worldPosition) => {
      const cellInfo = findGridCell(worldPosition.x, worldPosition.z);
      
      if (!cellInfo) return null;
      
      const { i, j, p1, p2, p3, p4 } = cellInfo;
      
      return {
        gridX: i,
        gridZ: j,
        localX: worldPosition.x,
        localY: worldPosition.y,
        localZ: worldPosition.z,
        corners: [p1, p2, p3, p4]
      };
    };
    
    const getCellKey = (gridX, gridZ, height) => `${gridX},${gridZ},${height}`;
    
    const createCellGeometry = (corners, height) => {
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
    };
     
    const fillCell = (position) => {
      const gridPos = worldToGridPosition(position);
      if (!gridPos) return;
      
      const height = Math.round(position.y * 2) / 2;
      const key = getCellKey(gridPos.gridX, gridPos.gridZ, height);
      
      if (cellsMap.value[key]) return;
      
      const geometry = createCellGeometry(gridPos.corners, height);
      const color = new THREE.Color(cellColor.value);
      const material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(cellColor.value).clone().lerp(new THREE.Color('#ffffff'), 0.5), // softer tint
        metalness: 0,
        roughness: 2,            // more frosted surface
        transmission: 0.75,        // high light passing through
        thickness: 4,            // higher to simulate depth blur
        ior: 1.3,                  // lower than perfect glass
        transparent: true,
        opacity: 1.0,              // full opacity, controlled by transmission
        reflectivity: 0.15,
        clearcoat: 0.1,
        clearcoatRoughness: 0.5,
        envMapIntensity: 1.0
      });


      
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      if (arcticMode.value) {
        mesh.visible = false;
      }
      
      cellsMap.value[key] = {
        gridPosition: gridPos,
        worldPosition: new THREE.Vector3(position.x, height, position.z),
        mesh,
        height
      };
      
      if (arcticMode.value) {
        updateArcticMesh();
      }
    };
    
    const onMouseDown = (event) => {
      isMouseDown = true;
      mouseDownTime = Date.now();
    };
    
    const onMouseUp = (event) => {
      const clickDuration = Date.now() - mouseDownTime;

      if (clickDuration < 200) {
        if (event.button === 0) {
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(mouse, camera);

          const pointIntersects = raycaster.intersectObjects(points);
          if (pointIntersects.length > 0) {
            return;
          }

          if (previewCube.visible) {
            const targetPos = new THREE.Vector3(
              previewCube.position.x,
              previewCube.position.y - 0.25,
              previewCube.position.z
            );
            fillCell(targetPos);
          }

        } else if (event.button === 2) {
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(mouse, camera);

          const cellMeshes = Object.values(cellsMap.value).map(cell => cell.mesh);
          const intersects = raycaster.intersectObjects(cellMeshes);

          if (intersects.length > 0) {
            const hitObject = intersects[0].object;
            for (const [key, cell] of Object.entries(cellsMap.value)) {
              if (cell.mesh === hitObject) {
                cell.mesh.visible = false; // <- ensures immediate hide even before render
                scene.remove(cell.mesh);
                scene.remove(cell.mesh);
                delete cellsMap.value[key];
                if (arcticMode.value) updateArcticMesh();
                break;
              }
            }
          }
        }
      } else {
        orbitControls.enabled = true;
      }

      isMouseDown = false;
    };



    // ✅ MOVE THIS OUTSIDE `onMouseUp`
    const eraseVoxelAtMouse = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);

      const cellMeshes = Object.values(cellsMap.value).map(cell => cell.mesh);
      const intersects = raycaster.intersectObjects(cellMeshes);

      if (intersects.length > 0) {
        const hitObject = intersects[0].object;
        for (const [key, cell] of Object.entries(cellsMap.value)) {
          if (cell.mesh === hitObject) {
            scene.remove(cell.mesh);
            delete cellsMap.value[key];
            if (arcticMode.value) updateArcticMesh();
            break;
          }
        }
      }
    };
   

    
    const onContextMenu = (event) => {
      event.preventDefault();
    };
    
    const updateLines = () => {
      lines.forEach(({ line, pointA, pointB }) => {
        const positions = line.geometry.attributes.position.array;
        
        positions[0] = pointA.position.x;
        positions[1] = pointA.position.y;
        positions[2] = pointA.position.z;
        
        positions[3] = pointB.position.x;
        positions[4] = pointB.position.y;
        positions[5] = pointB.position.z;
        
        line.geometry.attributes.position.needsUpdate = true;
      });
    };
    
    const updateCells = () => {
      Object.values(cellsMap.value).forEach(cell => {
        if (!cell.gridPosition || !cell.gridPosition.corners) return;
        
        const height = cell.height;
        const corners = cell.gridPosition.corners;
        const newGeometry = createCellGeometry(corners, height);
        
        cell.mesh.geometry.dispose();
        cell.mesh.geometry = newGeometry;
      });
    };
    
    const updateCellColors = () => {
      const color = new THREE.Color(cellColor.value);
      Object.values(cellsMap.value).forEach(cell => {
        if (cell.mesh && cell.mesh.material) {
          cell.mesh.material.color = color;
        }
      });
    };
    
    const createUnifiedGeometry = () => {
      if (Object.keys(cellsMap.value).length === 0) return null;
      
      const vertices = [];
      const indices = [];
      let vertexIndex = 0;
      
      Object.values(cellsMap.value).forEach(cell => {
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
    };
    
    const updateArcticMesh = () => {
      if (!arcticMode.value) return;

      if (arcticMesh) {
        scene.remove(arcticMesh);
        arcticMesh.geometry.dispose();
        arcticMesh.material.dispose();
        arcticMesh = null;
      }

      const arcticEdges = scene.getObjectByName('arcticEdges');
      if (arcticEdges) {
        scene.remove(arcticEdges);
        arcticEdges.geometry.dispose();
        arcticEdges.material.dispose();
      }

      const unifiedGeometry = createUnifiedGeometry();
      if (unifiedGeometry) {
        const arcticMaterial = new THREE.MeshBasicMaterial({
          color: 0xffffff,
          side: THREE.DoubleSide
        });

        arcticMesh = new THREE.Mesh(unifiedGeometry, arcticMaterial);
        scene.add(arcticMesh);

        const edgesGeometry = new THREE.EdgesGeometry(unifiedGeometry, 45);
        const edgesMaterial = new THREE.LineBasicMaterial({ color: 0x000000, linewidth: 1 });
        const edgesLines = new THREE.LineSegments(edgesGeometry, edgesMaterial);
        edgesLines.name = 'arcticEdges';
        scene.add(edgesLines);
      }
    };
    
    const toggleArcticMode = () => {
      arcticMode.value = !arcticMode.value;
      
      if (arcticMode.value) {
        updateArcticMesh();
        
        if (gridObject) gridObject.visible = false;
        if (parallelLineGroup) parallelLineGroup.visible = false;
        if (previewCube) previewCube.visible = false;
        if (dragControls) dragControls.enabled = false;
        
        Object.values(cellsMap.value).forEach(cell => {
          if (cell.mesh && scene.children.includes(cell.mesh)) {
            cell.mesh.visible = true;
          }
        });

        
        scene.background = new THREE.Color(0xffffff);
        
        const arcticLight = new THREE.DirectionalLight(0xffffff, 0.8);
        arcticLight.position.set(0, 10, 5);
        arcticLight.name = 'arcticLight';
        scene.add(arcticLight);
        
        const originalAmbient = scene.getObjectByName('ambientLight');
        if (originalAmbient) originalAmbient.intensity = 0.9;
        
      } else {
        if (arcticMesh) {
          scene.remove(arcticMesh);
          arcticMesh.geometry.dispose();
          arcticMesh.material.dispose();
          arcticMesh = null;
        }
        const arcticEdges = scene.getObjectByName('arcticEdges');
        if (arcticEdges) {
          scene.remove(arcticEdges);
          arcticEdges.geometry.dispose();
          arcticEdges.material.dispose();
        }
        
        if (gridObject) gridObject.visible = true;
        if (parallelLineGroup) parallelLineGroup.visible = true;
        if (dragControls) dragControls.enabled = true;
        
        Object.values(cellsMap.value).forEach(cell => {
          if (cell.mesh) cell.mesh.visible = true;
        });
        
        scene.background = new THREE.Color(0xffffff);
        
        const arcticLight = scene.getObjectByName('arcticLight');
        if (arcticLight) scene.remove(arcticLight);
        
        const originalAmbient = scene.getObjectByName('ambientLight');
        if (originalAmbient) originalAmbient.intensity = 1.0;
      }
    };
    
    const animate = () => {
      requestAnimationFrame(animate);
      orbitControls.update();
      renderer.render(scene, camera);
    };
    
    const handleResize = () => {
      if (!canvasContainer.value) return;
      
      const width = canvasContainer.value.clientWidth;
      const height = canvasContainer.value.clientHeight;
      const aspect = width / height;
      const frustumSize = 10;
      
      camera.left = (frustumSize * aspect) / -2;
      camera.right = (frustumSize * aspect) / 2;
      camera.top = frustumSize / 2;
      camera.bottom = frustumSize / -2;
      
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    
    const resetGrid = () => {
      if (arcticMode.value) {
        toggleArcticMode();
      }
      
      Object.values(cellsMap.value).forEach(cell => {
        if (cell.mesh) {
          scene.remove(cell.mesh);
        }
      });
      cellsMap.value = {};
      
      selectedPoints.value.forEach(point => {
        point.material.color.set(0xe0e0e0);
      });
      selectedPoints.value = [];
      
      parallelLines.value.forEach(pl => {
        if (pl.line && pl.line.parent) {
          pl.line.parent.remove(pl.line);
        }
        if (pl.handle && pl.handle.parent) {
          pl.handle.parent.remove(pl.handle);
        }
      });
      parallelLines.value = [];
      
      createGrid();
    };
    
    const regenerateGrid = () => {
      resetGrid();
    };

    const captureArcticSnapshot = async () => {
      const wasInArcticMode = arcticMode.value;
      
      if (!wasInArcticMode) {
        toggleArcticMode();
        await nextTick();
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      const previewWasVisible = previewCube.visible;
      previewCube.visible = false;
      
      renderer.render(scene, camera);
      const dataURL = renderer.domElement.toDataURL('image/png', 1.0);
      
      previewCube.visible = previewWasVisible;
      
      if (!wasInArcticMode) {
        toggleArcticMode();
      }
      
      return dataURL;
    };
    
    const processWithComfyUI = async (imageDataURL) => {
      try {
        const response = await fetch(`${COMFY_API_URL}/api/process-base64`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            image: imageDataURL,
            prompt: aiPrompt.value
          })
        });
        
        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
          throw new Error(result.error || 'Processing failed');
        }
        
        return result.output_image;
        
      } catch (error) {
        console.error('ComfyUI processing error:', error);
        throw error;
      }
    };
    
    const generateAIBuilding = async () => {
      if (Object.keys(cellsMap.value).length === 0) {
        alert('Please create some voxels first!');
        return;
      }
      
      try {
        isProcessing.value = true;
        
        processingStage.value = 'Capturing snapshot...';
        const snapshot = await captureArcticSnapshot();
        currentSnapshot.value = snapshot;
        
        processingStage.value = 'Processing with AI...';
        const result = await processWithComfyUI(snapshot);
        generatedImage.value = result;
        
        processingStage.value = 'Complete!';
        
        setTimeout(() => {
          isProcessing.value = false;
          currentView.value = 'comparison';
        }, 500);
        
      } catch (error) {
        console.error('AI generation failed:', error);
        alert(`AI generation failed: ${error.message}`);
        isProcessing.value = false;
      }
    };
    
    const downloadSnapshot = async () => {
      try {
        const snapshot = await captureArcticSnapshot();
        downloadDataURL(snapshot, `isogen_snapshot_${Date.now()}.png`);
      } catch (error) {
        console.error('Snapshot download failed:', error);
      }
    };
    
    const downloadOBJ = () => {
      if (Object.keys(cellsMap.value).length === 0) {
        alert('No voxels to export!');
        return;
      }
      
      try {
        const exportGroup = new THREE.Group();
        Object.values(cellsMap.value).forEach(cell => {
          if (cell.mesh) {
            const meshClone = cell.mesh.clone();
            exportGroup.add(meshClone);
          }
        });
        
        const exporter = new OBJExporter();
        const objData = exporter.parse(exportGroup);
        
        const blob = new Blob([objData], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        downloadURL(url, `isogen_model_${Date.now()}.obj`);
        
        URL.revokeObjectURL(url);
        
      } catch (error) {
        console.error('OBJ export failed:', error);
        alert('3D model export failed.');
      }
    };
    
    const downloadDataURL = (dataURL, filename) => {
      const link = document.createElement('a');
      link.download = filename;
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
    
    const downloadURL = (url, filename) => {
      const link = document.createElement('a');
      link.download = filename;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
    
    onMounted(() => {
      initThree();
      window.addEventListener('resize', handleResize);
      // ✅ Ensure right-click erase works by preventing context menu
      renderer.domElement.addEventListener('contextmenu', onContextMenu);
      renderer.domElement.addEventListener('mousedown', onMouseDown);
      renderer.domElement.addEventListener('mouseup', onMouseUp);
      renderer.domElement.addEventListener('click', onMouseClick);
      renderer.domElement.addEventListener('mousemove', onMouseMove);
    });

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize);
      if (renderer) {
        renderer.domElement.removeEventListener('mousedown', onMouseDown);
        renderer.domElement.removeEventListener('mouseup', onMouseUp);
        renderer.domElement.removeEventListener('click', onMouseClick);
        renderer.domElement.removeEventListener('contextmenu', onContextMenu);
        renderer.domElement.removeEventListener('mousemove', onMouseMove);
        renderer.dispose();
      }
    });

    return {
      canvasContainer,
      gridSize,
      cellColor,
      arcticMode,
      aiPrompt,
      currentView,
      isProcessing,
      processingStage,
      currentSnapshot,
      generatedImage,
      cellsMap,
      selectedPoints,
      parallelLines,
      resetGrid,
      regenerateGrid,
      updateCellColors,
      createParallelLine,
      toggleArcticMode,
      generateAIBuilding,
      downloadSnapshot,
      downloadOBJ
    };
  }
};

</script>

<style scoped>
label {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.grid-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

#canvas-container,
.comparison-container {
  flex-grow: 1;
  min-height: 500px;
  position: relative;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 24px;
  padding-bottom: 40px;
  background: linear-gradient(
  to top,
  rgba(255, 255, 255, 0.15) 0%,
  rgba(255, 255, 255, 0.05) 40%,
  rgba(255, 255, 255, 0) 100%
  
);

  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-top: none;
  box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

button,
.generate-btn {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  color: white;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

button:hover:not(:disabled),
.generate-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
}

button:disabled,
.generate-btn:disabled {
  background: rgba(200, 200, 200, 0.2);
  cursor: not-allowed;
  opacity: 0.6;
}

.prompt-input {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  min-width: 240px;
  font-size: 14px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

input[type="color"] {
  width: 40px;
  height: 30px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  padding: 0;
  background-color: rgba(138, 138, 138, 0.05);
  cursor: pointer;
}

input[type="range"] {
  -webkit-appearance: none;
  background: transparent;
  height: 20px;
  cursor: pointer;
}

input[type="range"]::-webkit-slider-runnable-track {
  background: rgba(255, 255, 255, 0.3);
  height: 6px;
  border-radius: 3px;
}

input[type="range"]::-moz-range-track {
  background: rgba(255, 255, 255, 0.3);
  height: 6px;
  border-radius: 3px;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  background: white;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.1);
  margin-top: -5px;
}

input[type="range"]::-moz-range-thumb {
  background: white;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.1);
}

.arctic-active {
  background-color: rgba(255, 255, 255, 0.3) !important;
  box-shadow: 0 0 10px #727272;
  color: white;
}

.arctic-active:hover {
  background-color: rgba(255, 255, 255, 0.3)!important;
}

.ai-controls,
.export-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .ai-controls,
  .export-controls {
    flex-direction: column;
    width: 100%;
  }

  .prompt-input {
    min-width: 100%;
  }
}
</style>

