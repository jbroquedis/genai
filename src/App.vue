<template>
  <div id="app">
    <div class="app-container">
      <!-- Header -->
      <header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <span class="gradient-text">isOGen</span>
          </h1>
          <p class="app-subtitle">AI-Powered 3D Architectural Design Tool</p>
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

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px 0;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
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
  margin-bottom: 8px;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: none;
}

.app-subtitle {
  font-size: 1.1rem;
  color: #666;
  font-weight: 400;
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
  transition: all 0.3s ease;
}

button:focus {
  outline: 2px solid #667eea;
  outline-offset: 2px;
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