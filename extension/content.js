// Content script for Screenshot Annotator Extension
class AnnotationOverlay {
  constructor() {
    this.isActive = false;
    this.screenshot = null;
    this.annotations = [];
    this.currentAnnotation = null;
    this.overlay = null;
    this.canvas = null;
    this.isAddingAnnotation = false;
    this.pendingText = '';
    
    this.setupMessageListener();
  }
  
  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.action === 'startAnnotation') {
        this.startAnnotationMode(message.screenshot);
        sendResponse({ success: true });
      }
      return true;
    });
  }
  
  startAnnotationMode(screenshot) {
    this.screenshot = screenshot;
    this.annotations = screenshot.annotations || [];
    this.isActive = true;
    
    this.createOverlay();
    this.showAnnotationUI();
  }
  
  createOverlay() {
    // Remove existing overlay if any
    if (this.overlay) {
      this.overlay.remove();
    }
    
    // Create overlay container
    this.overlay = document.createElement('div');
    this.overlay.id = 'screenshot-annotation-overlay';
    this.overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.8);
      z-index: 999999;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    `;
    
    // Create screenshot container
    const screenshotContainer = document.createElement('div');
    screenshotContainer.style.cssText = `
      position: relative;
      max-width: 90vw;
      max-height: 70vh;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    `;
    
    // Create screenshot image (90% size)
    const img = document.createElement('img');
    img.src = this.screenshot.imageData;
    img.style.cssText = `
      display: block;
      width: ${this.screenshot.displayWidth}px;
      height: ${this.screenshot.displayHeight}px;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    `;
    
    // Create canvas for annotations
    this.canvas = document.createElement('canvas');
    this.canvas.width = this.screenshot.displayWidth;
    this.canvas.height = this.screenshot.displayHeight;
    this.canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      cursor: crosshair;
      pointer-events: all;
    `;
    
    screenshotContainer.appendChild(img);
    screenshotContainer.appendChild(this.canvas);
    
    // Create controls
    const controls = this.createControls();
    
    this.overlay.appendChild(controls);
    this.overlay.appendChild(screenshotContainer);
    
    document.body.appendChild(this.overlay);
    
    // Setup canvas event listeners
    this.setupCanvasEvents();
    
    // Draw existing annotations
    this.drawAnnotations();
  }
  
  createControls() {
    const controls = document.createElement('div');
    controls.style.cssText = `
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      align-items: center;
      background: white;
      padding: 12px 20px;
      border-radius: 25px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    `;
    
    // Text input for annotations
    const textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.placeholder = 'Enter annotation text...';
    textInput.style.cssText = `
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      min-width: 200px;
    `;
    textInput.id = 'annotation-text-input';
    
    // Add annotation button
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add Annotation';
    addBtn.style.cssText = `
      padding: 8px 16px;
      background: #007cba;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    `;
    addBtn.onclick = () => this.startAddingAnnotation();
    
    // Save button
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save & Exit';
    saveBtn.style.cssText = `
      padding: 8px 16px;
      background: #059669;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    `;
    saveBtn.onclick = () => this.saveAndExit();
    
    // Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
      padding: 8px 16px;
      background: #6b7280;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    `;
    cancelBtn.onclick = () => this.cancel();
    
    // Status text
    const status = document.createElement('span');
    status.id = 'annotation-status';
    status.style.cssText = `
      font-size: 12px;
      color: #666;
      margin-left: 10px;
    `;
    status.textContent = `${this.annotations.length} annotations`;
    
    controls.appendChild(textInput);
    controls.appendChild(addBtn);
    controls.appendChild(saveBtn);
    controls.appendChild(cancelBtn);
    controls.appendChild(status);
    
    return controls;
  }
  
  setupCanvasEvents() {
    this.canvas.addEventListener('click', (e) => {
      if (!this.isAddingAnnotation) return;
      
      const rect = this.canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
      const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
      
      if (!this.currentAnnotation) {
        // First click - set text position
        this.currentAnnotation = {
          id: Date.now().toString(),
          text: this.pendingText,
          x: x,
          y: y,
          pointer_x: x,
          pointer_y: y,
          timestamp: new Date().toISOString()
        };
        
        document.getElementById('annotation-status').textContent = 'Click where to point the arrow';
      } else {
        // Second click - set pointer position
        this.currentAnnotation.pointer_x = x;
        this.currentAnnotation.pointer_y = y;
        
        // Add to annotations array
        this.annotations.push(this.currentAnnotation);
        
        // Reset state
        this.currentAnnotation = null;
        this.isAddingAnnotation = false;
        this.canvas.style.cursor = 'default';
        
        // Update status
        document.getElementById('annotation-status').textContent = `${this.annotations.length} annotations`;
        
        // Clear input
        document.getElementById('annotation-text-input').value = '';
        
        // Redraw
        this.drawAnnotations();
      }
    });
    
    // Show preview on mouse move when adding annotation
    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.isAddingAnnotation || !this.currentAnnotation) return;
      
      const rect = this.canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
      const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
      
      // Draw preview
      this.drawAnnotations();
      const ctx = this.canvas.getContext('2d');
      
      // Draw preview arrow
      ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(this.currentAnnotation.x, this.currentAnnotation.y);
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.setLineDash([]);
    });
  }
  
  startAddingAnnotation() {
    const textInput = document.getElementById('annotation-text-input');
    const text = textInput.value.trim();
    
    if (!text) {
      alert('Please enter annotation text first');
      textInput.focus();
      return;
    }
    
    this.pendingText = text;
    this.isAddingAnnotation = true;
    this.canvas.style.cursor = 'crosshair';
    
    document.getElementById('annotation-status').textContent = 'Click where to place the text';
  }
  
  drawAnnotations() {
    const ctx = this.canvas.getContext('2d');
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Draw all existing annotations
    this.annotations.forEach(annotation => {
      // Draw arrow line
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(annotation.x, annotation.y);
      ctx.lineTo(annotation.pointer_x, annotation.pointer_y);
      ctx.stroke();
      
      // Draw arrowhead
      const angle = Math.atan2(annotation.pointer_y - annotation.y, annotation.pointer_x - annotation.x);
      const arrowLength = 12;
      
      ctx.beginPath();
      ctx.moveTo(annotation.pointer_x, annotation.pointer_y);
      ctx.lineTo(
        annotation.pointer_x - arrowLength * Math.cos(angle - Math.PI / 6),
        annotation.pointer_y - arrowLength * Math.sin(angle - Math.PI / 6)
      );
      ctx.moveTo(annotation.pointer_x, annotation.pointer_y);
      ctx.lineTo(
        annotation.pointer_x - arrowLength * Math.cos(angle + Math.PI / 6),
        annotation.pointer_y - arrowLength * Math.sin(angle + Math.PI / 6)
      );
      ctx.stroke();
      
      // Draw pointer dot
      ctx.beginPath();
      ctx.arc(annotation.pointer_x, annotation.pointer_y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#ff0000';
      ctx.fill();
      
      // Draw text background
      ctx.font = '14px Arial';
      const textWidth = ctx.measureText(annotation.text).width;
      const textHeight = 16;
      const padding = 6;
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.fillRect(
        annotation.x - padding,
        annotation.y - textHeight - padding,
        textWidth + padding * 2,
        textHeight + padding * 2
      );
      
      // Draw text border
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 1;
      ctx.strokeRect(
        annotation.x - padding,
        annotation.y - textHeight - padding,
        textWidth + padding * 2,
        textHeight + padding * 2
      );
      
      // Draw text
      ctx.fillStyle = '#000000';
      ctx.fillText(annotation.text, annotation.x, annotation.y - 4);
    });
    
    // Draw current annotation if exists
    if (this.currentAnnotation) {
      ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
      const textWidth = ctx.measureText(this.currentAnnotation.text).width;
      ctx.fillRect(
        this.currentAnnotation.x - 4,
        this.currentAnnotation.y - 20,
        textWidth + 8,
        20
      );
      ctx.fillStyle = '#000000';
      ctx.fillText(this.currentAnnotation.text, this.currentAnnotation.x, this.currentAnnotation.y - 4);
    }
  }
  
  async saveAndExit() {
    try {
      // Update screenshot with annotations
      this.screenshot.annotations = this.annotations;
      
      // Save to storage
      const result = await chrome.storage.local.get('screenshots');
      const screenshots = result.screenshots || [];
      
      // Find and update the screenshot
      const index = screenshots.findIndex(s => s.id === this.screenshot.id);
      if (index !== -1) {
        screenshots[index] = this.screenshot;
      }
      
      await chrome.storage.local.set({ screenshots: screenshots });
      
      this.showNotification('Annotations saved successfully!', 'success');
      
      setTimeout(() => {
        this.cleanup();
      }, 1500);
      
    } catch (error) {
      console.error('Save error:', error);
      this.showNotification('Failed to save annotations', 'error');
    }
  }
  
  cancel() {
    this.cleanup();
  }
  
  cleanup() {
    if (this.overlay) {
      this.overlay.remove();
    }
    
    this.isActive = false;
    this.screenshot = null;
    this.annotations = [];
    this.currentAnnotation = null;
    this.isAddingAnnotation = false;
    this.pendingText = '';
  }
  
  showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 6px;
      color: white;
      font-size: 14px;
      font-weight: 500;
      z-index: 1000000;
      ${type === 'success' ? 'background: #059669;' : 'background: #dc2626;'}
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  showAnnotationUI() {
    // Show tutorial message
    const tutorial = document.createElement('div');
    tutorial.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 15px 25px;
      border-radius: 8px;
      font-size: 14px;
      z-index: 1000000;
      text-align: center;
      max-width: 600px;
    `;
    tutorial.innerHTML = `
      <div><strong>Screenshot Annotation Mode</strong></div>
      <div style="margin-top: 8px; font-size: 12px; opacity: 0.9;">
        1. Enter text in the input field<br>
        2. Click "Add Annotation"<br>
        3. Click where you want the text to appear<br>
        4. Click where you want the arrow to point<br>
        5. Click "Save & Exit" when done
      </div>
    `;
    
    document.body.appendChild(tutorial);
    
    setTimeout(() => {
      tutorial.remove();
    }, 8000);
  }
}

// Initialize content script
if (!window.screenshotAnnotator) {
  window.screenshotAnnotator = new AnnotationOverlay();
}