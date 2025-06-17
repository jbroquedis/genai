<template>
  <div class="processing-modal-overlay">
    <div class="processing-modal">
      <!-- Header -->
      <div class="modal-header">
        <h3>Thinking...</h3>
      </div>
      
      <!-- Progress Content -->
      <div class="modal-content">
        <!-- Animated Icon -->
        <div class="processing-icon">
          <div class="spinner">
            <div class="cube">
              <div class="face front"></div>
              <div class="face back"></div>
              <div class="face right"></div>
              <div class="face left"></div>
              <div class="face top"></div>
              <div class="face bottom"></div>
            </div>
          </div>
        </div>
        
        <!-- Progress Steps -->
        <div class="progress-steps">
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 0, 
              'completed': currentStepIndex > 0 
            }"
          >
            <div class="step-icon">🕛</div>
            <span>Capturing snapshot</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 1, 
              'completed': currentStepIndex > 1 
            }"
          >
            <div class="step-icon">🕒</div>
            <span>Processing with AI</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 2, 
              'completed': currentStepIndex > 2 
            }"
          >
            <div class="step-icon">🕧</div>
            <span>Generating result</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 3, 
              'completed': currentStepIndex > 3 
            }"
          >
            <div class="step-icon">🕘</div>
            <span>Complete!</span>
          </div>
        </div>
        
        <!-- Current Stage Display -->
        <div class="current-stage">
          <p>{{ stage }}</p>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${progressPercentage}%` }"
            />
          </div>
        </div>
        
        <!-- Tips -->
        <div class="processing-tips">
          <div class="tip" v-show="currentStepIndex === 0">
             <strong>Tip:</strong> Arctic mode provides the cleanest input for AI processing
          </div>
          <div class="tip" v-show="currentStepIndex === 1">
             <strong>Tip:</strong> Complex designs may take longer to process
          </div>
          <div class="tip" v-show="currentStepIndex === 2">
             <strong>Tip:</strong> The AI is creating realistic architectural details
          </div>
          <div class="tip" v-show="currentStepIndex === 3">
             <strong>Success:</strong> Your AI building is ready!
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="modal-footer">
        <small>This may take 30-60 seconds depending on complexity</small>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ProcessingModal',
  props: {
    stage: {
      type: String,
      default: 'Processing...'
    }
  },
  setup(props) {
    const steps = [
      'Capturing snapshot',
      'Processing with AI',
      'Generating result',
      'Complete'
    ];
    
    const currentStepIndex = computed(() => {
      const stage = props.stage.toLowerCase();
      if (stage.includes('capturing') || stage.includes('snapshot')) return 0;
      if (stage.includes('processing') || stage.includes('ai')) return 1;
      if (stage.includes('generating') || stage.includes('result')) return 2;
      if (stage.includes('complete')) return 3;
      return 0;
    });
    
    const progressPercentage = computed(() => {
      return ((currentStepIndex.value + 1) / steps.length) * 100;
    });
    
    return {
      currentStepIndex,
      progressPercentage
    };
  }
};
</script>

<style scoped>
.processing-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.processing-modal {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border-radius: 20px;
  padding: 24px 32px;
  max-width: 480px;
  width: 90%;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  color: white;
  font-family: 'Inter', sans-serif;
  text-align: center;
  animation: modalAppear 0.3s ease-out;
}

.modal-header h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: rgba(51, 51, 51, 0.08);
}

.modal-content {
  padding: 24px 0;
  color: rgba(36, 36, 36, 0.08);
}

.processing-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
  color: rgb(59, 59, 59);
}

.spinner {
  perspective: 200px;
}

.cube {
  position: relative;
  width: 60px;
  height: 60px;
  transform-style: preserve-3d;
  animation: rotateCube 2s infinite linear;
  color: rgb(100, 100, 100);
}

@keyframes rotateCube {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}

.face {
  position: absolute;
  width: 60px;
  height: 60px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  opacity: 0.6;
}

.front  { background: rgba(61, 61, 61, 0.08); transform: rotateY(0deg) translateZ(30px); }
.back   { background: rgba(61, 61, 61, 0.08); transform: rotateY(180deg) translateZ(30px); }
.right  { background: rgba(61, 61, 61, 0.08);  transform: rotateY(90deg) translateZ(30px); }
.left   { background: rgba(61, 61, 61, 0.08);  transform: rotateY(-90deg) translateZ(30px); }
.top    { background: rgba(61, 61, 61, 0.08); transform: rotateX(90deg) translateZ(30px); }
.bottom { background: rgba(61, 61, 61, 0.08); transform: rotateX(-90deg) translateZ(30px); }

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(51, 51, 51, 0.08);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffffff88, #ffffffcc);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.modal-footer {
  margin-top: 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}
</style>
