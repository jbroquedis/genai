<template>
  <div id="app">
    <div class="app-container">
      <!-- Header -->
      <header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <span class="gradient-text">isOGen</span>
          </h1>
          <p class="app-subtitle">the OG of isometric generation</p>
        </div>
      </header>

      <!-- Main Content -->
      <main class="main-content">
        <DraggableGrid />
      </main>
    </div>
  </div>
</template>

<script>
import DraggableGrid from './components/DraggableGrid.vue';

export default {
  name: 'App',
  components: {
    DraggableGrid
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.glass-panel {
  background: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.1);
  padding: 24px;
}



#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;

  /* Smooth gradient that transitions within the topbar area (0-20%) */
  background: linear-gradient(to bottom, #9f9f9f 0%, #ffffff 9%, #ffffff 95%, #9f9f9f 100%);
  backdrop-filter: blur(60px);
  -webkit-backdrop-filter: blur(60px);
}


.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}



.app-header {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(50%);
  border: none;
  border-radius: 25px / 30px;
  margin: 20px auto;
  max-width: 90%;
  padding: 20px 40px;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 6px -6px 6px rgba(255, 255, 255, 0.4),
    inset -6px 6px 6px rgba(255, 255, 255, 0.4),
    inset 6px -6px 6px rgba(255, 255, 255, 0.4),
    inset -6px 6px 6px rgba(255, 255, 255, 0.4);
  position: relative;
}



.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  text-align: center;
}

.app-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}
.gradient-text {
  background: linear-gradient(135deg,#000000 0%, #cacaca 70%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: none;
}

.app-subtitle {
  color: rgba(172, 172, 172, 0.7);
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.45);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Global Styles */
button {
  font-family: inherit;
  cursor: pointer;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px) saturate(160%);
  -webkit-backdrop-filter: blur(12px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  color: white;
  transition: all 0.3s ease;
}

button:hover {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

button:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.4);
}




input {
  font-family: inherit;
}

/* Responsive Design */
@media (max-width: 768px) {
  .app-title {
    font-size: 2rem;
  }
  
  .app-subtitle {
    font-size: 1rem;
  }
  
  .header-content {
    padding: 0 15px;
  }
}

/* Loading Animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.main-content {
  animation: fadeIn 0.6s ease-out;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #667eea;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #5a67d8;
}
</style>