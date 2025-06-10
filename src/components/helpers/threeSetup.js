import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export function initThree(container) {
  // Create scene
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf0f0f0);
  
  // Create orthographic camera for isometric view
  const aspect = container.clientWidth / container.clientHeight;
  const frustumSize = 10; // Adjust this to control zoom level
  
  const camera = new THREE.OrthographicCamera(
    (frustumSize * aspect) / -2,  // left
    (frustumSize * aspect) / 2,   // right
    frustumSize / 2,              // top
    frustumSize / -2,             // bottom
    0.1,                          // near
    1000                          // far
  );
  
  // Position camera for isometric view
  // Standard isometric angles: 35.264° elevation, 45° azimuth
  const distance = 15;
  camera.position.set(
    distance * Math.cos(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2))),
    distance * Math.sin(Math.atan(1/Math.sqrt(2))),
    distance * Math.sin(Math.PI / 4) * Math.cos(Math.atan(1/Math.sqrt(2)))
  );
  
  // Look at the center of the scene
  camera.lookAt(0, 0, 0);
  
  // Create renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);
  
  // Add lights for soft, friendly appearance
  const ambientLight = new THREE.AmbientLight(0x606060, 0.8);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(1, 1, 1);
  scene.add(directionalLight);
  
  // Add softer point lights for more dimension
  const pointLight1 = new THREE.PointLight(0xffffff, 0.4);
  pointLight1.position.set(5, 5, 5);
  scene.add(pointLight1);
  
  const pointLight2 = new THREE.PointLight(0xffffff, 0.3);
  pointLight2.position.set(-5, 3, -5);
  scene.add(pointLight2);
  
  // Initialize raycaster and mouse
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  
  // Add orbit controls with constraints for isometric view
  const orbitControls = new OrbitControls(camera, renderer.domElement);
  orbitControls.enableDamping = true;
  orbitControls.dampingFactor = 0.05;
  orbitControls.enabled = false; // Start with orbit controls disabled
  
  // Optional: Constrain orbit controls to maintain isometric feel
  // orbitControls.enableRotate = false; // Disable rotation to keep pure isometric
  // orbitControls.minPolarAngle = Math.PI / 4; // Minimum elevation
  // orbitControls.maxPolarAngle = Math.PI / 3; // Maximum elevation
  
  // Create group for parallel lines
  const parallelLineGroup = new THREE.Group();
  scene.add(parallelLineGroup);
  
  // Setup animation loop
  const animate = () => {
    requestAnimationFrame(animate);
    orbitControls.update();
    renderer.render(scene, camera);
  };
  
  // Start animation
  animate();
  
  // Handle window resizing for orthographic camera
  const handleResize = () => {
    if (!container) return;
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    const aspect = width / height;
    
    // Update orthographic camera frustum
    camera.left = (frustumSize * aspect) / -2;
    camera.right = (frustumSize * aspect) / 2;
    camera.top = frustumSize / 2;
    camera.bottom = frustumSize / -2;
    
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  };
  
  window.addEventListener('resize', handleResize);
  
  // Return all objects needed for the scene
  return {
    scene,
    camera,
    renderer,
    orbitControls,
    raycaster,
    mouse,
    parallelLineGroup,
    handleResize,
    dispose: () => {
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      renderer.domElement.remove();
    }
  };
}