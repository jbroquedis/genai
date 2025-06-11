<template>
  <div id="gradio-embed-container">
    <DraggableGrid />
  </div>
</template>

<script setup>
import DraggableGrid from '../components/DraggableGrid.vue'
</script>

<style>
body {
  margin: 0;
  background: transparent;
}
#gradio-embed-container {
  width: 100%;
  height: 600px;
  overflow: hidden;
}
</style>
