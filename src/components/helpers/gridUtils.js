import * as THREE from 'three';

export function createGrid(scene, gridSize) {
  const gridObject = new THREE.Group();
  scene.add(gridObject);
  
  const points = [];
  const lines = [];
  
  // Create points
  const size = gridSize;
  const spacing = 1;
  const halfSize = (size - 1) * spacing / 2;
  
  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      const geometry = new THREE.SphereGeometry(0.05, 16, 16);
      const material = new THREE.MeshPhongMaterial({ color: 0x156289 });
      const sphere = new THREE.Mesh(geometry, material);
      
      sphere.position.set(
        i * spacing - halfSize,
        0, // Always at y=0 to stay in grid plane
        j * spacing - halfSize
      );
      
      sphere.userData = { gridX: i, gridZ: j };
      
      gridObject.add(sphere);
      points.push(sphere);
    }
  }
  
  // Create horizontal lines
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
      lines.push({
        line,
        pointA,
        pointB
      });
    }
  }
  
  // Create vertical lines
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
      lines.push({
        line,
        pointA,
        pointB
      });
    }
  }
  
  return { gridObject, points, lines };
}

export function updateLines(lines) {
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
}

export function findGridCell(points, gridSize, worldX, worldZ) {
  const size = gridSize;
  
  // Find the four grid points that form a cell containing the worldX, worldZ
  for (let i = 0; i < size - 1; i++) {
    for (let j = 0; j < size - 1; j++) {
      const p1 = points[i * size + j];
      const p2 = points[i * size + (j + 1)];
      const p3 = points[(i + 1) * size + j];
      const p4 = points[(i + 1) * size + (j + 1)];
      
      // Check if the point is inside this grid cell
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

export function worldToGridPosition(points, gridSize, worldPosition) {
  // Find the grid cell containing this position
  const cellInfo = findGridCell(points, gridSize, worldPosition.x, worldPosition.z);
  
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
}