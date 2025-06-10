<template>
  <div class="controls">
    <button @click="$emit('resetGrid')">Reset Grid</button>
    <div>
      <label>Grid Size: {{ gridSize }}x{{ gridSize }}</label>
      <input 
        type="range" 
        min="2" 
        max="20" 
        :value="gridSize"
        @input="$emit('update:gridSize', parseInt($event.target.value))" 
      />
    </div>
    <div>
      <label for="colorPicker">Cell Color:</label>
      <input 
        type="color" 
        id="colorPicker" 
        :value="cellColor"
        @input="$emit('update:cellColor', $event.target.value)" 
      />
    </div>
    <div>
      <button @click="$emit('createParallelLine')">Create Parallel Line</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GridControls',
  props: {
    gridSize: {
      type: Number,
      required: true
    },
    cellColor: {
      type: String,
      required: true
    }
  },
  emits: ['update:gridSize', 'update:cellColor', 'resetGrid', 'createParallelLine']
}
</script>

<style scoped>
.controls {
  padding: 15px;
  background-color: #f5f5f5;
  display: flex;
  gap: 20px;
  align-items: center;
  border-top: 1px solid #e0e0e0;
}

button {
  padding: 8px 16px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

button:hover {
  background-color: #3367d6;
}

button:active {
  transform: translateY(1px);
}

input[type="color"] {
  width: 40px;
  height: 30px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

input[type="range"] {
  cursor: pointer;
  width: 150px;
}

label {
  font-weight: 500;
  color: #444;
}
</style>