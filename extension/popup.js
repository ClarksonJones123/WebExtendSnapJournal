// Popup functionality for Screenshot Annotator Extension
class ScreenshotAnnotator {
  constructor() {
    this.screenshots = [];
    this.selectedScreenshot = null;
    this.memoryUsage = 0;
    
    this.init();
  }
  
  async init() {
    await this.loadScreenshots();
    this.setupEventListeners();
    this.updateUI();
  }
  
  setupEventListeners() {
    // Capture screenshot
    document.getElementById('captureBtn').addEventListener('click', () => {
      this.captureScreenshot();
    });
    
    // Start annotation mode
    document.getElementById('annotateBtn').addEventListener('click', () => {
      this.startAnnotation();
    });
    
    // Export to PDF
    document.getElementById('exportPdfBtn').addEventListener('click', () => {
      this.exportToPDF();
    });
    
    // Clear all screenshots
    document.getElementById('clearMemoryBtn').addEventListener('click', () => {
      this.clearAllScreenshots();
    });
  }
  
  async loadScreenshots() {
    try {
      const result = await chrome.storage.local.get('screenshots');
      this.screenshots = result.screenshots || [];
      this.calculateMemoryUsage();
    } catch (error) {
      console.error('Error loading screenshots:', error);
      this.showStatus('Error loading screenshots', 'error');
    }
  }
  
  async saveScreenshots() {
    try {
      await chrome.storage.local.set({ screenshots: this.screenshots });
      this.calculateMemoryUsage();
      this.updateUI();
    } catch (error) {
      console.error('Error saving screenshots:', error);
      this.showStatus('Error saving screenshots', 'error');
    }
  }
  
  calculateMemoryUsage() {
    this.memoryUsage = 0;
    this.screenshots.forEach(screenshot => {
      // Estimate memory usage based on image data length
      if (screenshot.imageData) {
        this.memoryUsage += screenshot.imageData.length * 0.75; // Base64 overhead
      }
      // Add annotation data
      screenshot.annotations.forEach(annotation => {
        this.memoryUsage += JSON.stringify(annotation).length;
      });
    });
  }
  
  formatMemorySize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB';
    return Math.round(bytes / (1024 * 1024)) + ' MB';
  }
  
  async captureScreenshot() {
    try {
      this.showStatus('Capturing screenshot...', 'info');
      
      // Get current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Directly capture visible tab using background script
      const response = await chrome.runtime.sendMessage({ 
        action: 'captureVisibleTab' 
      });
      
      if (response && response.imageData) {
        // Create screenshot object
        const screenshot = {
          id: Date.now().toString(),
          imageData: response.imageData,
          originalWidth: 1920, // Default width
          originalHeight: 1080, // Default height  
          displayWidth: Math.round(1920 * 0.9), // 90% sizing
          displayHeight: Math.round(1080 * 0.9),
          url: tab.url,
          title: tab.title,
          timestamp: new Date().toISOString(),
          annotations: []
        };
        
        this.screenshots.push(screenshot);
        await this.saveScreenshots();
        
        this.showStatus('Screenshot captured successfully!', 'success');
        this.selectedScreenshot = screenshot;
        
        // Enable annotation button
        document.getElementById('annotateBtn').disabled = false;
        document.getElementById('annotateBtn').classList.remove('disabled');
        
      } else {
        throw new Error(response?.error || 'Failed to capture screenshot');
      }
    } catch (error) {
      console.error('Capture error:', error);
      this.showStatus(`Failed to capture screenshot: ${error.message}`, 'error');
    }
  }
  
  // Function to be injected into the page for screenshot capture
  capturePageScreenshot() {
    return new Promise((resolve) => {
      // Create a canvas to capture the visible page
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Get page dimensions
      const width = Math.max(
        document.documentElement.scrollWidth,
        document.documentElement.clientWidth,
        window.innerWidth
      );
      const height = Math.max(
        document.documentElement.scrollHeight,
        document.documentElement.clientHeight,
        window.innerHeight
      );
      
      // Set canvas size
      canvas.width = width;
      canvas.height = height;
      
      // Use html2canvas-like approach or fallback to chrome.tabs.captureVisibleTab
      // For now, we'll use a simple approach with chrome.tabs.captureVisibleTab
      // This will be handled by the background script
      
      chrome.runtime.sendMessage({ 
        action: 'captureVisibleTab' 
      }, (response) => {
        if (response && response.imageData) {
          resolve({
            imageData: response.imageData,
            dimensions: { width: window.innerWidth, height: window.innerHeight }
          });
        } else {
          resolve(null);
        }
      });
    });
  }
  
  async startAnnotation() {
    if (!this.selectedScreenshot) {
      this.showStatus('Please select a screenshot first', 'error');
      return;
    }
    
    try {
      // Get current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Send message to content script to start annotation mode
      await chrome.tabs.sendMessage(tab.id, {
        action: 'startAnnotation',
        screenshot: this.selectedScreenshot
      });
      
      this.showStatus('Annotation mode activated! Click on the page to add annotations.', 'success');
      
      // Close popup to allow interaction with page
      window.close();
      
    } catch (error) {
      console.error('Annotation error:', error);
      this.showStatus('Failed to start annotation mode', 'error');
    }
  }
  
  async exportToPDF() {
    if (this.screenshots.length === 0) {
      this.showStatus('No screenshots to export', 'error');
      return;
    }
    
    try {
      this.showStatus('Generating PDF...', 'info');
      
      // Simple PDF export using jsPDF (would need to include library)
      // For now, we'll create a simple HTML export
      const htmlContent = this.generateHTMLExport();
      
      // Create blob and download
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      
      // Use Chrome downloads API
      await chrome.downloads.download({
        url: url,
        filename: `screenshots-${new Date().toISOString().slice(0, 10)}.html`,
        saveAs: true
      });
      
      this.showStatus('Export completed!', 'success');
      
      // Ask if user wants to clear memory
      if (confirm('Export completed! Do you want to clear screenshots to free memory?')) {
        this.clearAllScreenshots();
      }
      
    } catch (error) {
      console.error('Export error:', error);
      this.showStatus('Failed to export', 'error');
    }
  }
  
  generateHTMLExport() {
    let html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Screenshot Annotations Export</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .screenshot { margin-bottom: 40px; page-break-after: always; }
        .screenshot img { max-width: 90%; border: 1px solid #ccc; }
        .annotations { margin-top: 20px; }
        .annotation { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 3px solid #007cba; }
        .timestamp { color: #666; font-size: 12px; }
        .url { color: #007cba; font-size: 14px; margin-bottom: 10px; }
      </style>
    </head>
    <body>
      <h1>Screenshot Annotations Export</h1>
      <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>
      <p>Total Screenshots: ${this.screenshots.length}</p>
      <hr>
    `;
    
    this.screenshots.forEach((screenshot, index) => {
      html += `
      <div class="screenshot">
        <h2>Screenshot ${index + 1}</h2>
        <div class="url">${screenshot.url}</div>
        <div class="timestamp">${new Date(screenshot.timestamp).toLocaleString()}</div>
        <img src="${screenshot.imageData}" alt="Screenshot ${index + 1}">
        
        <div class="annotations">
          <h3>Annotations (${screenshot.annotations.length})</h3>
      `;
      
      screenshot.annotations.forEach((annotation, i) => {
        html += `
        <div class="annotation">
          <strong>${i + 1}.</strong> ${annotation.text}
          <br><small>Position: (${Math.round(annotation.x)}, ${Math.round(annotation.y)}) → (${Math.round(annotation.pointer_x)}, ${Math.round(annotation.pointer_y)})</small>
        </div>
        `;
      });
      
      html += `
        </div>
      </div>
      `;
    });
    
    html += `
    </body>
    </html>
    `;
    
    return html;
  }
  
  async clearAllScreenshots() {
    if (this.screenshots.length === 0) {
      this.showStatus('No screenshots to clear', 'info');
      return;
    }
    
    if (confirm(`Are you sure you want to delete all ${this.screenshots.length} screenshots? This will free ${this.formatMemorySize(this.memoryUsage)} of memory.`)) {
      try {
        this.screenshots = [];
        await this.saveScreenshots();
        this.selectedScreenshot = null;
        
        this.showStatus(`Memory cleared! Freed ${this.formatMemorySize(this.memoryUsage)}`, 'success');
        
        // Disable buttons
        document.getElementById('annotateBtn').disabled = true;
        document.getElementById('annotateBtn').classList.add('disabled');
        
      } catch (error) {
        console.error('Clear error:', error);
        this.showStatus('Failed to clear screenshots', 'error');
      }
    }
  }
  
  updateUI() {
    // Update memory info
    document.getElementById('memoryUsage').textContent = this.formatMemorySize(this.memoryUsage);
    document.getElementById('screenshotCount').textContent = this.screenshots.length;
    
    // Update screenshots list
    const listElement = document.getElementById('screenshotsList');
    listElement.innerHTML = '';
    
    if (this.screenshots.length === 0) {
      listElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">No screenshots yet. Click "Capture Current Page" to get started.</div>';
    } else {
      this.screenshots.forEach(screenshot => {
        const item = document.createElement('div');
        item.className = 'screenshot-item';
        if (this.selectedScreenshot && this.selectedScreenshot.id === screenshot.id) {
          item.classList.add('selected');
        }
        
        item.innerHTML = `
          <div>
            <div class="screenshot-info">${screenshot.title}</div>
            <div class="screenshot-time">${new Date(screenshot.timestamp).toLocaleString()}</div>
            <div class="screenshot-info">${screenshot.displayWidth}×${screenshot.displayHeight} | ${screenshot.annotations.length} annotations</div>
          </div>
        `;
        
        item.addEventListener('click', () => {
          this.selectedScreenshot = screenshot;
          this.updateUI();
          
          // Enable annotation button
          document.getElementById('annotateBtn').disabled = false;
          document.getElementById('annotateBtn').classList.remove('disabled');
        });
        
        listElement.appendChild(item);
      });
    }
    
    // Update export button
    const exportBtn = document.getElementById('exportPdfBtn');
    if (this.screenshots.length > 0) {
      exportBtn.disabled = false;
      exportBtn.classList.remove('disabled');
    } else {
      exportBtn.disabled = true;
      exportBtn.classList.add('disabled');
    }
  }
  
  showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove('hidden');
    
    // Auto hide after 3 seconds
    setTimeout(() => {
      statusEl.classList.add('hidden');
    }, 3000);
  }
}

// Initialize when popup loads
document.addEventListener('DOMContentLoaded', () => {
  new ScreenshotAnnotator();
});