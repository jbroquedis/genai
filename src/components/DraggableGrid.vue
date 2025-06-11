<template>
  <div class="grid-container">
    <div id="canvas-container" ref="canvasContainer"></div>
    <div class="controls">
      <button @click="resetGrid">Reset Grid</button>

      <div style="display: flex; align-items: center; gap: 8px;">
        <label>Grid Size: {{ gridSize }}x{{ gridSize }}</label>
        <input type="range" min="2" max="20" v-model.number="gridSize" @change="regenerateGrid" />
      </div>

      <div style="display: flex; align-items: center; gap: 8px;">
        <label for="colorPicker">Cell Color:</label>
        <input type="color" id="colorPicker" v-model="cellColor" @change="updateCellColors" />
      </div>

      <div>
        <button @click="createParallelLine">Create Parallel Line</button>
      </div>

      <div>
        <button @click="toggleArcticMode" :class="{ 'arctic-active': arcticMode }">
          {{ arcticMode ? 'Exit Arctic Mode' : 'Arctic Mode' }}
        </button>
      </div>
    </div>
  </div>
</template>


<script>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { DragControls } from 'three/examples/jsm/controls/DragControls.js';

export default {
  name: 'DraggableGrid',
  setup() {
    const canvasContainer = ref(null);
    const gridSize = ref(10);
    const cellColor = ref('#ffffff');
    const arcticMode = ref(false);
    
    let scene, camera, renderer, orbitControls, dragControls, raycaster, mouse;
    let points = [];
    let lines = [];
    let parallelLines = [];
    let gridObject;
    let cellsMap = {};
    let isMouseDown = false;
    let mouseDownTime = 0;
    let selectedPoints = [];
    let parallelLineGroup = new THREE.Group();
    let arcticMesh = null;
    let previewCube = null;
    
    const initThree = () => {
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xf0f0f0);
      
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
      
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(canvasContainer.value.clientWidth, canvasContainer.value.clientHeight);
      canvasContainer.value.appendChild(renderer.domElement);
      
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
      
      scene.add(parallelLineGroup);
      
      // Create preview cube with corner points only
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
    
    // Create preview cube with edge lines only (no diagonals)
    const createPreviewCube = () => {
      previewCube = new THREE.Group();
      
      // Create a wireframe box with only the 12 edges (no diagonals)
      // Make it slightly larger to ensure it's visible above voxels
      const geometry = new THREE.BoxGeometry(0.85, 0.55, 0.85);
      const edges = new THREE.EdgesGeometry(geometry);
      const material = new THREE.LineBasicMaterial({
        color: 0xcccccc, // Light grey
        transparent: true,
        opacity: 0.9,
        linewidth: 2,
        depthTest: false // This ensures it renders on top
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
      
      // Check for voxel stacking
      const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
      let intersects = raycaster.intersectObjects(cellMeshes);
      
      if (intersects.length > 0) {
        const hitObject = intersects[0].object;
        for (const cell of Object.values(cellsMap)) {
          if (cell.mesh === hitObject) {
            // Position preview ABOVE the hit voxel
            const previewY = cell.worldPosition.y + 0.5 + 0.25; // existing voxel height + half new voxel height
            
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
      
      // Check for ground placement - snap to grid cell centers, not grid points
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
      const intersection = new THREE.Vector3();
      
      if (raycaster.ray.intersectPlane(groundPlane, intersection)) {
        const gridSpacing = 1;
        const halfSize = (gridSize.value - 1) * gridSpacing / 2;
        
        // Find which grid cell the intersection point is in
        const cellI = Math.floor((intersection.x + halfSize + gridSpacing/2) / gridSpacing);
        const cellJ = Math.floor((intersection.z + halfSize + gridSpacing/2) / gridSpacing);
        
        // Check if we're within the valid grid bounds
        if (cellI >= 0 && cellI < gridSize.value - 1 && cellJ >= 0 && cellJ < gridSize.value - 1) {
          // Calculate the center of this grid cell
          const cellCenterX = (cellI * gridSpacing) - halfSize + (gridSpacing / 2);
          const cellCenterZ = (cellJ * gridSpacing) - halfSize + (gridSpacing / 2);
          
          const groundPos = new THREE.Vector3(cellCenterX, 0, cellCenterZ);
          
          if (!findCellAtPosition(groundPos)) {
            // For ground level: voxel base at y=0, center at y=0.25
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
      for (const cell of Object.values(cellsMap)) {
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
      parallelLines.forEach(plObj => {
        if (plObj.handle) {
          draggableObjects.push(plObj.handle);
        }
      });
      
      dragControls = new DragControls(draggableObjects, camera, renderer.domElement);
      
      dragControls.addEventListener('dragstart', (event) => {
        orbitControls.enabled = false;
        const parallelLine = parallelLines.find(pl => pl.handle === event.object);
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
          const parallelLine = parallelLines.find(pl => pl.handle === event.object);
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
        const parallelLine = parallelLines.find(pl => pl.handle === event.object);
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
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh && cell.mesh.parent) {
            cell.mesh.parent.remove(cell.mesh);
          }
        });
        cellsMap = {};
      }
      
      gridObject = new THREE.Group();
      scene.add(gridObject);
      
      const size = gridSize.value;
      const spacing = 1;
      const halfSize = (size - 1) * spacing / 2;
      
      for (let i = 0; i < size; i++) {
        for (let j = 0; j < size; j++) {
          const geometry = new THREE.SphereGeometry(0.08, 16, 16);
          const material = new THREE.MeshPhongMaterial({ color: 0xe0e0e0 });
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
      
      // Create lines (horizontal and vertical)
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
          const material = new THREE.LineBasicMaterial({ color: 0x888888 });
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
          const material = new THREE.LineBasicMaterial({ color: 0x888888 });
          const line = new THREE.Line(geometry, material);
          
          gridObject.add(line);
          lines.push({ line, pointA, pointB });
        }
      }
      
      selectedPoints = [];
      parallelLines.forEach(pl => {
        if (pl.line && pl.line.parent) {
          pl.line.parent.remove(pl.line);
        }
        if (pl.handle && pl.handle.parent) {
          pl.handle.parent.remove(pl.handle);
        }
      });
      parallelLines = [];
      
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
        const index = selectedPoints.indexOf(clickedPoint);
        if (index === -1) {
          selectedPoints.push(clickedPoint);
          clickedPoint.material.color.set('#ff830f');
        } else {
          selectedPoints.splice(index, 1);
          clickedPoint.material.color.set(0xe0e0e0);
        }
      }
    };
    
    const createParallelLine = () => {
      if (selectedPoints.length < 3) {
        console.log("Need at least 3 points to create a parallel line");
        return;
      }
      
      const positions = [];
      selectedPoints.forEach(point => {
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
      selectedPoints.forEach(point => {
        center.add(point.position);
      });
      center.divideScalar(selectedPoints.length);
      handle.position.copy(center);
      
      parallelLineGroup.add(handle);
      
      const parallelLine = {
        line: lineMesh,
        handle: handle,
        points: [...selectedPoints],
        lastPosition: handle.position.clone(),
        isDragging: false
      };
      
      parallelLines.push(parallelLine);
      
      selectedPoints.forEach(point => {
        point.material.color.set('#ff830f');
      });
      selectedPoints = [];
      
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
      parallelLines.forEach(parallelLine => {
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
      
      if (cellsMap[key]) return;
      
      const geometry = createCellGeometry(gridPos.corners, height);
      const color = new THREE.Color(cellColor.value);
      const material = new THREE.MeshPhongMaterial({
        color: color,
        transparent: true,
        opacity: 0.7
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      if (arcticMode.value) {
        mesh.visible = false;
      }
      
      cellsMap[key] = {
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
        if (event.button === 0) { // Left click
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(mouse, camera);
          
          const pointIntersects = raycaster.intersectObjects(points);
          if (pointIntersects.length > 0) {
            return; // Point selection handled by onMouseClick
          }
          
          // Use preview position for placement
          if (previewCube.visible) {
            const targetPos = new THREE.Vector3(
              previewCube.position.x,
              previewCube.position.y - 0.25,
              previewCube.position.z
            );
            fillCell(targetPos);
          }
          
        } else if (event.button === 2) { // Right click
          const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
          const intersects = raycaster.intersectObjects(cellMeshes);
          
          if (intersects.length > 0) {
            const hitObject = intersects[0].object;
            for (const [key, cell] of Object.entries(cellsMap)) {
              if (cell.mesh === hitObject) {
                scene.remove(cell.mesh);
                delete cellsMap[key];
                if (arcticMode.value) {
                  updateArcticMesh();
                }
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
      Object.values(cellsMap).forEach(cell => {
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
      Object.values(cellsMap).forEach(cell => {
        if (cell.mesh && cell.mesh.material) {
          cell.mesh.material.color = color;
        }
      });
    };
    
    // Simple Arctic Mode
    const createUnifiedGeometry = () => {
      if (Object.keys(cellsMap).length === 0) return null;
      
      const vertices = [];
      const indices = [];
      let vertexIndex = 0;
      
      Object.values(cellsMap).forEach(cell => {
        const positions = cell.mesh.geometry.attributes.position.array;
        const cellIndices = cell.mesh.geometry.index.array;
        
        // Add vertices
        for (let i = 0; i < positions.length; i += 3) {
          vertices.push(
            positions[i] + cell.mesh.position.x,
            positions[i + 1] + cell.mesh.position.y,
            positions[i + 2] + cell.mesh.position.z
          );
        }
        
        // Add indices with offset
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
    };
    
    const toggleArcticMode = () => {
      arcticMode.value = !arcticMode.value;
      
      if (arcticMode.value) {
        updateArcticMesh();
        
        if (gridObject) gridObject.visible = false;
        if (parallelLineGroup) parallelLineGroup.visible = false;
        if (previewCube) previewCube.visible = false;
        if (dragControls) dragControls.enabled = false;
        
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh) cell.mesh.visible = false;
        });
        
        scene.background = new THREE.Color(0xf8fbff);
        
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
        
        if (gridObject) gridObject.visible = true;
        if (parallelLineGroup) parallelLineGroup.visible = true;
        if (dragControls) dragControls.enabled = true;
        
        Object.values(cellsMap).forEach(cell => {
          if (cell.mesh) cell.mesh.visible = true;
        });
        
        scene.background = new THREE.Color(0xf0f0f0);
        
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
      
      Object.values(cellsMap).forEach(cell => {
        if (cell.mesh) {
          scene.remove(cell.mesh);
        }
      });
      cellsMap = {};
      
      selectedPoints.forEach(point => {
        point.material.color.set(0x156289);
      });
      selectedPoints = [];
      
      parallelLines.forEach(pl => {
        if (pl.line && pl.line.parent) {
          pl.line.parent.remove(pl.line);
        }
        if (pl.handle && pl.handle.parent) {
          pl.handle.parent.remove(pl.handle);
        }
      });
      parallelLines = [];
      
      createGrid();
    };
    
    const regenerateGrid = () => {
      resetGrid();
    };
    
    onMounted(() => {
      initThree();
      window.addEventListener('resize', handleResize);
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
      resetGrid,
      regenerateGrid,
      updateCellColors,
      createParallelLine,
      toggleArcticMode
    };
  }
}
</script>

<style scoped>

label {
  font-family: 'Inter', sans-serif; /* Change to your preferred font */
  font-size: 14px; /* Optional */
  font-weight: 500; /* Optional */
  color: rgb(167, 167, 167); /* Optional */
}

.grid-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

#canvas-container {
  flex-grow: 1;
  min-height: 500px;
  position: relative;
}

.controls {
  padding: 10px;
  background-color: #f5f5f5;
  display: flex;
  flex-wrap: wrap; /* handles smaller screens */
  gap: 20px;
  align-items: center; /* ← vertically aligns everything */
}

.controls label {
  font-size: 13px;
  color: #888;
  font-weight: 400;
}


button {
  padding: 8px 16px;
  background-color: #ffffff;
  color: rgb(167, 167, 167);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

button:hover {
  background-color: rgb(223, 223, 223);
}

.arctic-active {
  background-color: #ff8819 !important;
  box-shadow: 0 0 10px rgba(0, 188, 212, 0.5);
}

.arctic-active:hover {
  background-color: #0097a7 !important;
}

/* Reset native appearance */
input[type="range"] {
  -webkit-appearance: none;
  background: transparent; /* so only track is visible */
}

/* Track */
input[type="range"]::-webkit-slider-runnable-track {
  background: #ddd; /* your track color */
  height: 6px;
  border-radius: 3px;
}
input[type="range"]::-moz-range-track {
  background: #ddd;
  height: 6px;
  border-radius: 3px;
}

/* Thumb */
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  background: #ddd;   /* match track color */
  width: 16px;
  height: 16px;
  border-radius: 50%;
  cursor: pointer;
  margin-top: -5px; /* vertical center (depends on track height) */
}
input[type="range"]::-moz-range-thumb {
  background: #ddd;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  cursor: pointer;
}


input[type="color"] {
  width: 40px;
  height: 30px;
  border: 2px solid #aaa;
  border-radius: 4px;
  padding: 0;
  background-color: transparent; /* so the actual selected color shows */
  cursor: pointer;
}



</style>

