<template>
  <div class="comparison-slider">
    <!-- Header -->
    <div class="comparison-header">
      <h2></h2>
      <button @click="$emit('back-to-editor')" class="back-btn">
        ← Back to Editor
      </button>
    </div>
    
    <!-- Image Comparison Container -->
    <div class="image-comparison" ref="comparisonContainer">
      <div class="image-container">
        <!-- Before Image (Base Layer) - Now shows AI Generated on left -->
        <div class="image-layer before-layer">
          <img :src="afterImage" alt="AI Generated" @load="onImageLoad" />
        </div>
        
        <!-- After Image (Clipped Layer) - Now shows Original on right -->
        <div 
          class="image-layer after-layer" 
          :style="{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }"
        >
          <img :src="beforeImage" alt="Original" @load="onImageLoad" />
        </div>
        
        <!-- Divider Line -->
        <div 
          class="divider-line" 
          :style="{ left: `${sliderValue}%` }"
        >
          <div class="divider-handle">
            <div class="handle-icon">⟷</div>
          </div>
        </div>
      </div>
      
      <!-- Slider Control -->
      <div class="slider-container">
        <input 
          type="range" 
          min="0" 
          max="100" 
          v-model.number="sliderValue"
          class="comparison-slider-input"
          @input="onSliderChange"
        />
        <div class="slider-labels">
          <span>AI Generated</span>
          <span>Original</span>
        </div>
      </div>
    </div>
    
    <!-- Download Controls -->
    <div class="download-controls">
      <button @click="downloadImage(beforeImage, 'original')" class="download-btn">
        Download Original
      </button>
      <button @click="downloadImage(afterImage, 'ai-generated')" class="download-btn">
        Download AI gen
      </button>
      <button @click="downloadComparison" class="download-btn">
        Download Comparison
      </button>
    </div>
    
    <!-- Image Info -->
    <div class="image-info" v-if="imageLoaded">
      <div class="info-item">
        <strong>Dimensions:</strong> {{ imageWidth }} × {{ imageHeight }}px
      </div>
      <div class="info-item">
        <strong>Generated:</strong> {{ new Date().toLocaleString() }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'ComparisonSlider',
  props: {
    beforeImage: {
      type: String,
      required: true
    },
    afterImage: {
      type: String,
      required: true
    }
  },
  emits: ['back-to-editor'],
  setup(props) {
    const sliderValue = ref(50);
    const imageLoaded = ref(false);
    const imageWidth = ref(0);
    const imageHeight = ref(0);
    const comparisonContainer = ref(null);
    
    const onSliderChange = () => {
      if (navigator.vibrate) {
        navigator.vibrate(1);
      }
    };
    
    const onImageLoad = (event) => {
      if (!imageLoaded.value) {
        imageWidth.value = event.target.naturalWidth;
        imageHeight.value = event.target.naturalHeight;
        imageLoaded.value = true;
      }
    };
    
    const downloadImage = (dataURL, prefix) => {
      const link = document.createElement('a');
      link.download = `isogen_${prefix}_${Date.now()}.png`;
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
    
    const downloadComparison = async () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const beforeImg = new Image();
        const afterImg = new Image();
        
        await Promise.all([
          new Promise(resolve => {
            beforeImg.onload = resolve;
            beforeImg.src = props.beforeImage;
          }),
          new Promise(resolve => {
            afterImg.onload = resolve;
            afterImg.src = props.afterImage;
          })
        ]);
        
        canvas.width = beforeImg.width * 2;
        canvas.height = beforeImg.height;
        
        // Now AI Generated is on left, Original on right to match the flipped display
        ctx.drawImage(afterImg, 0, 0);
        ctx.drawImage(beforeImg, beforeImg.width, 0);
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(10, 10, 120, 30);
        ctx.fillRect(beforeImg.width + 10, 10, 120, 30);
        
        ctx.fillStyle = 'white';
        ctx.font = '16px Arial';
        ctx.fillText('AI Generated', 20, 30);
        ctx.fillText('Original', beforeImg.width + 20, 30);
        
        const dataURL = canvas.toDataURL('image/png');
        downloadImage(dataURL, 'comparison');
        
      } catch (error) {
        console.error('Comparison download failed:', error);
        alert('Failed to create comparison image');
      }
    };
    
    let isDragging = false;
    
    const handleMouseDown = (event) => {
      event.preventDefault(); // Prevent text selection
      isDragging = true;
      updateSliderFromPosition(event);
    };
    
    const handleMouseMove = (event) => {
      if (isDragging) {
        event.preventDefault(); // Prevent text selection during drag
        updateSliderFromPosition(event);
      }
    };
    
    const handleMouseUp = () => {
      isDragging = false;
    };
    
    const updateSliderFromPosition = (event) => {
      if (!comparisonContainer.value) return;
      
      const rect = comparisonContainer.value.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
      sliderValue.value = Math.round(percentage);
    };
    
    onMounted(() => {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      if (comparisonContainer.value) {
        comparisonContainer.value.addEventListener('mousedown', handleMouseDown);
      }
    });
    
    return {
      sliderValue,
      imageLoaded,
      imageWidth,
      imageHeight,
      comparisonContainer,
      onSliderChange,
      onImageLoad,
      downloadImage,
      downloadComparison
    };
  }
};
</script>

<style scoped>
/* Updated button styles with glass morphism effect */
button,
.back-btn,
.download-btn {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.557);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(50%);
  border: none;
  border-radius: 30px / 30px;
  color: #676767;
  font-weight: 400;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 
    0px 0px 2px rgba(0, 0, 0, 0.2),
    inset 4px -4px 4px rgba(255, 255, 255, 0.4),
    inset -4px 4px 4px rgba(255, 255, 255, 0.4),
    inset 4px -4px 4px rgba(255, 255, 255, 0.4),
    inset -4px 4px 4px rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
  position: relative;
}

button:hover:not(:disabled),
.back-btn:hover:not(:disabled),
.download-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  border-radius: 38px 32px 35px 40px / 42px 28px 39px 34px;
  box-shadow: 
    0 0px 4px rgba(0, 0, 0, 0.25),
    inset 7px -7px 7px rgba(255, 255, 255, 0.5),
    inset -7px 7px 7px rgba(255, 255, 255, 0.5),
    inset 7px -7px 7px rgba(255, 255, 255, 0.5),
    inset -7px 7px 7px rgba(255, 255, 255, 0.5);
}

button:disabled,
.back-btn:disabled,
.download-btn:disabled {
  background: rgba(200, 200, 200, 0.2);
  cursor: not-allowed;
  opacity: 0.6;
}

.comparison-slider {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
  user-select: none; /* Prevent text selection on the entire component */
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.comparison-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
  font-weight: 600;
}

.image-comparison {
  flex-grow: 0;
  flex-shrink: 0;
  height: auto;
}

.image-container {
  position: relative;
  height: 600px; 
  background: white;
  border-radius: 12px;
  overflow: hidden;
  outline: none;
  box-shadow: 0 0px 0px rgba(0, 0, 0, 0.1);
  cursor: grab;
  user-select: none; /* Prevent text selection */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.image-container:active {
  cursor: grabbing;
}

.image-layer {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none; /* Prevent text selection */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.image-layer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  margin: 0 auto;
  background-color: white;
  user-select: none; /* Prevent image selection */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -webkit-user-drag: none; /* Prevent image dragging */
  pointer-events: none; /* Make images non-interactive */
}

.before-layer {
  z-index: 1;
}

.after-layer {
  z-index: 2;
}

.image-label {
  position: absolute;
  top: 15px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  font-size: 14px;
  font-weight: 600;
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.before-label {
  left: 15px;
  background: rgba(108, 117, 125, 0.9);
}

.after-label {
  right: 15px;
  background: rgba(76, 175, 80, 0.9);
}

.divider-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: white;
  z-index: 3;
  transform: translateX(-1px);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
}

.divider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  cursor: grab;
}

.divider-handle:active {
  cursor: grabbing;
}

.handle-icon {
  font-size: 18px;
  color: #666;
  font-weight: bold;
}

.slider-container {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.comparison-slider-input {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e9ecef;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.comparison-slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #5c5c5c;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
}

.comparison-slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.comparison-slider-input::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #5c5c5c;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.download-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding: 20px;
  background: rgb(158, 158, 158);
  border-radius: 0px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.image-info {
  display: flex;
  gap: 30px;
  justify-content: center;
  padding: 15px;
  background: rgb(158, 158, 158);
  border-radius: 0px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  font-size: 14px;
}

.info-item {
  color: #ffffff;
}

.info-item strong {
  color: #ffffff;
}

@media (max-width: 768px) {
  .comparison-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .download-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .image-info {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .image-label {
    font-size: 12px;
    padding: 6px 12px;
  }
}

.image-layer img {
  transition: opacity 0.3s ease;
}

.image-layer img:not([src]) {
  opacity: 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.comparison-slider > * {
  animation: fadeIn 0.6s ease forwards;
}

.comparison-slider > *:nth-child(2) {
  animation-delay: 0.1s;
}

.comparison-slider > *:nth-child(3) {
  animation-delay: 0.2s;
}

.comparison-slider > *:nth-child(4) {
  animation-delay: 0.3s;
}
</style>