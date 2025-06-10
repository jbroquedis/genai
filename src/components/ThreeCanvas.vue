<template>
  <div id="canvas-container" ref="canvasContainer"></div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as THREE from 'three';
import { DragControls } from 'three/examples/jsm/controls/DragControls.js';

import { initThree } from './helpers/threeSetup';
import { createGrid, updateLines, worldToGridPosition } from './helpers/gridUtils';
import { getCellKey, createCellGeometry, createCell, updateCells, getRaycastPoint, removeCell } from './helpers/cellUtils';
import { createParallelLine as createParallelLineHelper, updateParallelLine, updateParallelLines, cleanupParallelLines } from './helpers/parallelLineUtils';

export default {
  name: 'ThreeCanvas',
  props: {
    gridSize: {
      type: Number,
      default: 10
    },
    cellColor: {
      type: String,
      default: '#4285f4'
    }
  },
  emits: ['pointsSelected'],
  setup(props, { emit }) {
    const canvasContainer = ref(null);
    
    let threeInstance = null;
    let points = [];
    let lines = [];
    let parallelLines = [];
    let gridObject;
    let cellsMap = {};
    let isMouseDown = false;
    let mouseDownTime = 0;
    let selectedPoints = [];
    let dragControls = null;
    
    // Initialize Three.js scene
    onMounted(() => {
      if (canvasContainer.value) {
        threeInstance = initThree(canvasContainer.value);
        createInitialGrid();
        setupEvents();
      }
    });
    
    // Clean up resources when component is unmounted
    onBeforeUnmount(() => {
      cleanupEvents();
      if (threeInstance) {
        threeInstance.dispose();
      }
    });
    
    // Watch for grid size changes
    watch(() => props.gridSize, (newSize) => {
      resetGrid();
    });
    
    // Create the initial grid
    const createInitialGrid = () => {
      const { scene } = threeInstance;
      const { gridObject: newGridObject, points: newPoints, lines: newLines } = createGrid(scene, props.gridSize);
      
      gridObject = newGridObject;
      points = newPoints;
      lines = newLines;
      
      setupDragControls();
    };
    
    // Set up drag controls for points and parallel line elements
    const setupDragControls = () => {
      const { camera, renderer } = threeInstance;
      
      // Dispose previous controls if any
      if (dragControls) {
        dragControls.dispose();
      }
      
      // Create a list of all draggable objects
      const draggableObjects = [...points];
      
      // Add parallel line endpoints and handles to draggable objects
      parallelLines.forEach(plObj => {
        if (plObj.endpoints) {
          draggableObjects.push(...plObj.endpoints);
        }
        if (plObj.handle) {
          draggableObjects.push(plObj.handle);
        }
      });
      
      dragControls = new DragControls(draggableObjects, camera, renderer.domElement);
      
      dragControls.addEventListener('dragstart', (event) => {
        threeInstance.orbitControls.enabled = false;
        
        // Check if dragged object is a parallel line element
        const parallelLine = parallelLines.find(pl => 
          (pl.endpoints && pl.endpoints.includes(event.object)) || pl.handle === event.object
        );
        
        if (parallelLine) {
          parallelLine.isDragging = true;
          parallelLine.draggedObject = event.object;
          
          // If it's the handle, store the initial position
          if (parallelLine.handle === event.object) {
            parallelLine.lastPosition = event.object.position.clone();
          }
        }
      });
      
      dragControls.addEventListener('drag', (event) => {
        // ALWAYS constrain movement to XZ plane (y=0)
        event.object.position.y = 0;
        
        // Check if dragged object is a grid point
        const isGridPoint = points.includes(event.object);
        
        if (isGridPoint) {
          updateLines(lines);
          updateCells(cellsMap, createCellGeometry);
          
          // Update any parallel lines connected to this point
          updateParallelLines(parallelLines);
        } else {
          // Check if it's a parallel line element
          const parallelLine = parallelLines.find(pl => 
            (pl.endpoints && pl.endpoints.includes(event.object)) || pl.handle === event.object
          );
          
          if (parallelLine && parallelLine.isDragging) {
            if (parallelLine.handle === event.object) {
              // Handle is being dragged - move all endpoints
              const offset = event.object.position.clone().sub(parallelLine.lastPosition);
              parallelLine.lastPosition.copy(event.object.position);
              
              // Move all endpoints
              if (parallelLine.endpoints) {
                parallelLine.endpoints.forEach(endpoint => {
                  endpoint.position.add(offset);
                });
              }
            }
            
            // Update the visual line
            updateParallelLine(parallelLine);
          }
        }
      });
      
      dragControls.addEventListener('dragend', (event) => {
        threeInstance.orbitControls.enabled = false;
        
        // Reset dragging flag on parallel line
        const parallelLine = parallelLines.find(pl => 
          (pl.endpoints && pl.endpoints.includes(event.object)) || pl.handle === event.object
        );
        
        if (parallelLine) {
          parallelLine.isDragging = false;
          parallelLine.draggedObject = null;
        }
      });
      
      return dragControls;
    };
    
    // Setup event listeners
    const setupEvents = () => {
      const { renderer } = threeInstance;
      
      renderer.domElement.addEventListener('mousedown', onMouseDown);
      renderer.domElement.addEventListener('mouseup', onMouseUp);
      renderer.domElement.addEventListener('click', onMouseClick);
      renderer.domElement.addEventListener('contextmenu', onContextMenu);
    };
    
    // Clean up event listeners
    const cleanupEvents = () => {
      const { renderer } = threeInstance;
      
      if (renderer && renderer.domElement) {
        renderer.domElement.removeEventListener('mousedown', onMouseDown);
        renderer.domElement.removeEventListener('mouseup', onMouseUp);
        renderer.domElement.removeEventListener('click', onMouseClick);
        renderer.domElement.removeEventListener('contextmenu', onContextMenu);
      }
    };
    
    // Update mouse and raycaster from event
    const updateMouseAndRaycaster = (event) => {
      const { raycaster, mouse, camera } = threeInstance;
      const rect = event.target.getBoundingClientRect();
      
      // Calculate normalized mouse coordinates (-1 to +1)
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      // Update raycaster with mouse position
      raycaster.setFromCamera(mouse, camera);
      
      return { raycaster, mouse };
    };
    
    // Handle mouse down event
    const onMouseDown = (event) => {
      isMouseDown = true;
      mouseDownTime = Date.now();
    };
    
    // Handle mouse up event
    const onMouseUp = (event) => {
      const clickDuration = Date.now() - mouseDownTime;
      
      // If it's a short click (less than 200ms), create/remove cell
      if (clickDuration < 200) {
        // Update raycaster
        updateMouseAndRaycaster(event);
        
        // Get cell meshes array
        const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
        
        // Get the point under cursor
        const { raycaster, camera } = threeInstance;
        const point = getRaycastPoint(raycaster, camera, points, cellMeshes);
        
        if (event.button === 0) { // Left click
          // Point selection is handled by onMouseClick
        } else if (event.button === 2) { // Right click
          if (point) {
            const gridPos = worldToGridPosition(points, props.gridSize, point);
            const height = Math.round(point.y * 2) / 2;
            removeCell(threeInstance.scene, cellsMap, point, gridPos, height);
          }
        }
      } else {
        // Long click/drag enables orbit controls
        threeInstance.orbitControls.enabled = true;
      }
      
      isMouseDown = false;
    };
    
    // Handle mouse click event
    const onMouseClick = (event) => {
      if (event.button !== 0) return; // Only process left clicks
      
      // Update raycaster
      updateMouseAndRaycaster(event);
      const { raycaster } = threeInstance;
      
      // Check for intersections with grid points
      const pointIntersects = raycaster.intersectObjects(points);
      
      if (pointIntersects.length > 0) {
        const clickedPoint = pointIntersects[0].object;
        
        // Toggle point selection
        const index = selectedPoints.indexOf(clickedPoint);
        if (index === -1) {
          // Add point to selection
          selectedPoints.push(clickedPoint);
          clickedPoint.material.color.set(0xff0000); // Red for selected
        } else {
          // Remove point from selection
          selectedPoints.splice(index, 1);
          clickedPoint.material.color.set(0x156289); // Back to original color
        }
        
        emit('pointsSelected', selectedPoints);
      } else {
        // Get cell meshes array
        const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
        
        // Get the point under cursor
        const { camera } = threeInstance;
        const point = getRaycastPoint(raycaster, camera, points, cellMeshes);
        
        if (point) {
          createCellAtPoint(point);
        }
      }
    };
    
    // Handle right-click context menu
    const onContextMenu = (event) => {
      event.preventDefault();
      
      // Update raycaster
      updateMouseAndRaycaster(event);
      
      // Get cell meshes array
      const cellMeshes = Object.values(cellsMap).map(cell => cell.mesh);
      
      // Get the point under cursor
      const { raycaster, camera } = threeInstance;
      const point = getRaycastPoint(raycaster, camera, points, cellMeshes);
      
      if (point) {
        const gridPos = worldToGridPosition(points, props.gridSize, point);
        const height = Math.round(point.y * 2) / 2;
        removeCell(threeInstance.scene, cellsMap, point, gridPos, height);
      }
    };
    
    // Create cell at specified point
    const createCellAtPoint = (position) => {
      const gridPos = worldToGridPosition(points, props.gridSize, position);
      
      if (!gridPos) return;
      
      // Round height to nearest 0.5 to create vertical grid
      const height = Math.round(position.y * 2) / 2;
      const currentColor = props.cellColor;
      const key = getCellKey(gridPos.gridX, gridPos.gridZ, height, currentColor);
      
      // If cell already exists, do nothing
      if (cellsMap[key]) return;
      
      // Create new cell
      const cell = createCell(threeInstance.scene, gridPos, position, height, currentColor);
      
      // Add to cells map
      cellsMap[key] = cell;
    };
    
    // Reset grid
    const resetGrid = () => {
      // Remove all filled cells
      Object.values(cellsMap).forEach(cell => {
        if (cell.mesh) {
          threeInstance.scene.remove(cell.mesh);
        }
      });
      cellsMap = {};
      
      // Clear selected points
      selectedPoints.forEach(point => {
        point.material.color.set(0x156289); // Reset to original color
      });
      selectedPoints = [];
      
      // Remove parallel lines
      parallelLines = cleanupParallelLines(threeInstance.scene, parallelLines);
      
      // Remove existing grid
      if (gridObject) {
        threeInstance.scene.remove(gridObject);
      }
      
      // Create new grid
      createInitialGrid();
    };
    
    // Create parallel line from selected points
    const createParallelLine = () => {
      if (selectedPoints.length < 2) {
        console.log("Need at least 2 points to create a parallel line");
        return;
      }
      
      const newLine = createParallelLineHelper(threeInstance.scene, threeInstance.parallelLineGroup, selectedPoints);
      
      if (newLine) {
        parallelLines.push(newLine);
        
        // Reset selected points
        selectedPoints.forEach(point => {
          point.material.color.set(0x156289); // Reset to original color
        });
        selectedPoints = [];
        
        // Update drag controls to include the new endpoints and handle
        setupDragControls();
      }
    };
    
    // Expose functions for parent component
    return {
      canvasContainer,
      resetGrid,
      createParallelLine
    };
  }
}
</script>

<style scoped>
#canvas-container {
  flex-grow: 1;
  min-height: 500px;
  position: relative;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}
</style>