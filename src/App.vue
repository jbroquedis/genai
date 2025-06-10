<template>
  <div class="app">
    <DraggableGrid />
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
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}

.app {
  width: 100%;
  height: 100vh;
}
</style>