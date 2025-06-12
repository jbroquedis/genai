<template>
  <div class="processing-modal-overlay">
    <div class="processing-modal">
      <!-- Header -->
      <div class="modal-header">
        <h3>Generating AI Building</h3>
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
            <div class="step-icon">📸</div>
            <span>Capturing snapshot</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 1, 
              'completed': currentStepIndex > 1 
            }"
          >
            <div class="step-icon">🤖</div>
            <span>Processing with AI</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 2, 
              'completed': currentStepIndex > 2 
            }"
          >
            <div class="step-icon">✨</div>
            <span>Generating result</span>
          </div>
          
          <div 
            class="step" 
            :class="{ 
              'active': currentStepIndex >= 3, 
              'completed': currentStepIndex > 3 
            }"
          >
            <div class="step-icon">✅</div>
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
            💡 <strong>Tip:</strong> Arctic mode provides the cleanest input for AI processing
          </div>
          <div class="tip" v-show="currentStepIndex === 1">
            💡 <strong>Tip:</strong> Complex designs may take longer to process
          </div>
          <div class="tip" v-show="currentStepIndex === 2">
            💡 <strong>Tip:</strong> The AI is creating realistic architectural details
          </div>
          <div class="tip" v-show="currentStepIndex === 3">
            💡 <strong>Success:</strong> Your AI building is ready!
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
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.processing-modal {
  background: white;
  border-radius: 16px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: modalAppear 0.3s ease-out;
}

@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  text-align: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.modal-content {
  padding: 32px 24px;
}

.processing-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
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
}

@keyframes rotateCube {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}

.face {
  position: absolute;
  width: 60px;
  height: 60px;
  border: 2px solid #667eea;
  opacity: 0.8;
}

.front { 
  background: rgba(102, 126, 234, 0.3);
  transform: rotateY(0deg) translateZ(30px); 
}
.back { 
  background: rgba(118, 75, 162, 0.3);
  transform: rotateY(180deg) translateZ(30px); 
}
.right { 
  background: rgba(102, 126, 234, 0.4);
  transform: rotateY(90deg) translateZ(30px); 
}
.left { 
  background: rgba(118, 75, 162, 0.4);
  transform: rotateY(-90deg) translateZ(30px); 
}
.top { 
  background: rgba(102, 126, 234, 0.5);
  transform: rotateX(90deg) translateZ(30px); 
}
.bottom { 
  background: rgba(118, 75, 162, 0.5);
  transform: rotateX(-90deg) translateZ(30px); 
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
  position: relative;
}

.progress-steps::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 12.5%;
  right: 12.5%;
  height: 2px;
  background: #e9ecef;
  z-index: 1;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 2;
  transition: all 0.3s ease;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.step span {
  font-size: 12px;
  text-align: center;
  color: #6c757d;
  font-weight: 500;
  max-width: 80px;
  line-height: 1.2;
}

.step.active .step-icon {
  background: #667eea;
  border-color: #667eea;
  color: white;
  animation: pulse 2s infinite;
}

.step.completed .step-icon {
  background: #28a745;
  border-color: #28a745;
  color: white;
}

.step.active span,
.step.completed span {
  color: #495057;
  font-weight: 600;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.current-stage {
  text-align: center;
  margin-bottom: 24px;
}

.current-stage p {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #495057;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.5s ease;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: 200px 0; }
}

.processing-tips {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #667eea;
}

.tip {
  font-size: 14px;
  line-height: 1.5;
  color: #495057;
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-footer {
  background: #f8f9fa;
  padding: 16px 24px;
  text-align: center;
  border-top: 1px solid #e9ecef;
}

.modal-footer small {
  color: #6c757d;
  font-size: 12px;
}

/* Responsive Design */
@media (max-width: 480px) {
  .processing-modal {
    width: 95%;
    margin: 20px;
  }
  
  .progress-steps {
    flex-wrap: wrap;
    gap: 16px;
    justify-content: center;
  }
  
  .progress-steps::before {
    display: none;
  }
  
  .step {
    flex-basis: 45%;
  }
  
  .step span {
    max-width: none;
  }
}
</style>