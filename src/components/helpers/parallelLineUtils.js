import * as THREE from 'three';

export function createParallelLine(scene, parallelLineGroup, selectedPoints) {
  if (selectedPoints.length < 2) {
    console.log("Need at least 2 points to create a parallel line");
    return null;
  }
  
  // Create a new parallel line
  const positions = [];
  
  // Collect positions of selected points
  selectedPoints.forEach(point => {
    positions.push(
      point.position.x,
      point.position.y,
      point.position.z
    );
  });
  
  // Create geometry for the line
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  
  // Create material with a distinct color
  const material = new THREE.LineBasicMaterial({ color: 0xff6600, linewidth: 2 });
  
  // Create the line mesh
  const lineMesh = new THREE.Line(geometry, material);
  parallelLineGroup.add(lineMesh);
  
  // Create endpoints for dragging the parallel line
  const endpoints = [];
  
  // Create draggable endpoints at both ends of the line
  const endpointGeom = new THREE.SphereGeometry(0.1, 16, 16);
  const endpointMat = new THREE.MeshPhongMaterial({ color: 0xff6600 });
  
  // Create two endpoints - one at each end of the line
  const startPoint = new THREE.Mesh(endpointGeom, endpointMat);
  startPoint.position.copy(selectedPoints[0].position);
  
  const endPoint = new THREE.Mesh(endpointGeom, endpointMat);
  endPoint.position.copy(selectedPoints[selectedPoints.length - 1].position);
  
  // Add the endpoints to the scene
  parallelLineGroup.add(startPoint);
  parallelLineGroup.add(endPoint);
  
  endpoints.push(startPoint);
  endpoints.push(endPoint);
  
  // Create a handle for dragging the entire line
  const handleGeom = new THREE.SphereGeometry(0.15, 16, 16);
  const handleMat = new THREE.MeshPhongMaterial({ color: 0xff9900 });
  const handle = new THREE.Mesh(handleGeom, handleMat);
  
  // Position the handle at the center of the endpoints
  const center = new THREE.Vector3();
  endpoints.forEach(point => {
    center.add(point.position);
  });
  center.divideScalar(endpoints.length);
  handle.position.copy(center);
  
  parallelLineGroup.add(handle);
  
  // Create and return the parallel line data
  return {
    line: lineMesh,
    points: [...selectedPoints],
    endpoints: endpoints,
    handle: handle,
    lastPosition: handle.position.clone(),
    isDragging: false,
    draggedObject: null
  };
}

export function updateParallelLine(parallelLine) {
  // Get positions of all points in the line
  const positions = [];
  
  // Update positions from endpoints
  if (parallelLine.endpoints) {
    parallelLine.endpoints.forEach(point => {
      positions.push(
        point.position.x,
        point.position.y,
        point.position.z
      );
    });
  }
  
  // Update the line geometry
  parallelLine.line.geometry.setAttribute(
    'position', 
    new THREE.Float32BufferAttribute(positions, 3)
  );
  parallelLine.line.geometry.attributes.position.needsUpdate = true;
  
  // Update handle position if not being dragged
  if (!parallelLine.isDragging || parallelLine.draggedObject !== parallelLine.handle) {
    // Update handle position to center of endpoints
    const center = new THREE.Vector3();
    parallelLine.endpoints.forEach(point => {
      center.add(point.position);
    });
    center.divideScalar(parallelLine.endpoints.length);
    
    parallelLine.handle.position.copy(center);
    parallelLine.lastPosition.copy(center);
  }
}

export function updateParallelLines(parallelLines) {
  parallelLines.forEach(parallelLine => {
    updateParallelLine(parallelLine);
  });
}

export function cleanupParallelLines(scene, parallelLines) {
  parallelLines.forEach(pl => {
    if (pl.line && pl.line.parent) {
      pl.line.parent.remove(pl.line);
    }
    if (pl.endpoints) {
      pl.endpoints.forEach(endpoint => {
        if (endpoint && endpoint.parent) {
          endpoint.parent.remove(endpoint);
        }
      });
    }
    if (pl.handle && pl.handle.parent) {
      pl.handle.parent.remove(pl.handle);
    }
  });
  
  return [];
}