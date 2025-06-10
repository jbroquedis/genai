import * as THREE from 'three';
import { worldToGridPosition } from './gridUtils';

export function getCellKey(gridX, gridZ, height, color) {
  return `${gridX},${gridZ},${height},${color}`;
}

export function createCellGeometry(corners, height) {
  // Create a custom geometry for the cell that matches the grid's shape
  const cellHeight = 0.5; // Height of each cell
  const p1 = corners[0].position;
  const p2 = corners[1].position;
  const p3 = corners[2].position;
  const p4 = corners[3].position;
  
  // Create vertices for the cell (top and bottom faces)
  const vertices = [
    // Bottom face (at y = height)
    p1.x, height, p1.z,
    p2.x, height, p2.z,
    p4.x, height, p4.z,
    p3.x, height, p3.z,
    
    // Top face (at y = height + cellHeight)
    p1.x, height + cellHeight, p1.z,
    p2.x, height + cellHeight, p2.z,
    p4.x, height + cellHeight, p4.z,
    p3.x, height + cellHeight, p3.z
  ];
  
  // Define faces using vertex indices
  const indices = [
    // Bottom face
    0, 1, 2,
    0, 2, 3,
    
    // Top face
    4, 6, 5,
    4, 7, 6,
    
    // Side faces
    0, 4, 1,
    1, 4, 5,
    
    1, 5, 2,
    2, 5, 6,
    
    2, 6, 3,
    3, 6, 7,
    
    3, 7, 0,
    0, 7, 4
  ];
  
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  
  return geometry;
}

export function createCell(scene, gridPos, position, height, color) {
  // Create a cell geometry that matches the grid's shape
  const geometry = createCellGeometry(gridPos.corners, height);
  
  // Parse the color
  const cellColor = new THREE.Color(color);
  
  // Create materials for the cell with white edges
  const material = new THREE.MeshPhongMaterial({
    color: cellColor,
    transparent: true,
    opacity: 0.75,
    specular: 0x222222,
    shininess: 50
  });
  
  const wireframeMaterial = new THREE.LineBasicMaterial({ 
    color: 0xffffff, 
    linewidth: 2 
  });
  
  // Create the cell mesh
  const cellMesh = new THREE.Mesh(geometry, material);
  
  // Create wireframe for white edges
  const edges = new THREE.EdgesGeometry(geometry);
  const wireframe = new THREE.LineSegments(edges, wireframeMaterial);
  
  // Add both to scene
  scene.add(cellMesh);
  cellMesh.add(wireframe);
  
  return {
    gridPosition: gridPos,
    worldPosition: new THREE.Vector3(position.x, height, position.z),
    mesh: cellMesh,
    wireframe: wireframe,
    height,
    color
  };
}

export function updateCells(cellsMap, createCellGeometry) {
  // Update positions of all cells based on their grid positions
  Object.values(cellsMap).forEach(cell => {
    if (!cell.gridPosition || !cell.gridPosition.corners) return;
    
    const height = cell.height;
    const corners = cell.gridPosition.corners;
    
    // Recreate the cell geometry with updated corner positions
    const newGeometry = createCellGeometry(corners, height);
    
    // Replace the cell's geometry
    cell.mesh.geometry.dispose();
    cell.mesh.geometry = newGeometry;
    
    // Update wireframe
    if (cell.wireframe) {
      const newEdges = new THREE.EdgesGeometry(newGeometry);
      cell.wireframe.geometry.dispose();
      cell.wireframe.geometry = newEdges;
    }
  });
}

export function getRaycastPoint(raycaster, camera, points, cellMeshes) {
  // Check for intersections with existing cells
  let intersects = raycaster.intersectObjects(cellMeshes, false);
  
  if (intersects.length > 0) {
    // Get the intersection point and face normal
    const point = intersects[0].point.clone();
    const faceNormal = intersects[0].face.normal.clone();
    
    // Transform the normal from local object space to world space
    const worldNormal = faceNormal.clone().transformDirection(intersects[0].object.matrixWorld);
    
    // Determine which face was clicked
    if (Math.abs(worldNormal.y) > 0.5) {
      // Top or bottom face - add cell above or below
      if (worldNormal.y > 0) {
        // Create cell above
        point.y += 0.5;
      } else {
        // Create cell below
        point.y -= 0.5;
      }
    } else {
      // Side face - create cell adjacent horizontally
      // Move in the direction of the normal by half a cell width
      point.add(worldNormal.multiplyScalar(0.5));
    }
    
    return point;
  }
  
  // If no cell was hit, check for grid points
  intersects = raycaster.intersectObjects(points);
  if (intersects.length > 0) {
    const point = intersects[0].point.clone();
    // Place at base grid level
    point.y = 0;
    return point;
  }
  
  // If nothing was hit, find intersection with base grid plane
  const planeNormal = new THREE.Vector3(0, 1, 0);
  const plane = new THREE.Plane(planeNormal, 0);
  const intersection = new THREE.Vector3();
  
  if (raycaster.ray.intersectPlane(plane, intersection)) {
    return intersection;
  }
  
  return null;
}

export function removeCell(scene, cellsMap, position, gridPos, height) {
  if (!gridPos) return;
  
  // Check cells at this position with any color
  Object.keys(cellsMap).forEach(key => {
    const cell = cellsMap[key];
    if (cell.gridPosition.gridX === gridPos.gridX && 
        cell.gridPosition.gridZ === gridPos.gridZ && 
        cell.height === height) {
      scene.remove(cell.mesh);
      delete cellsMap[key];
    }
  });
}