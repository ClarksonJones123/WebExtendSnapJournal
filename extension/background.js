// Background script for Screenshot Annotator Extension

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureVisibleTab') {
    // Capture the visible tab
    chrome.tabs.captureVisibleTab(
      null,
      { format: 'png', quality: 90 },
      (dataUrl) => {
        if (chrome.runtime.lastError) {
          console.error('Capture error:', chrome.runtime.lastError);
          sendResponse({ error: chrome.runtime.lastError.message });
        } else {
          console.log('Screenshot captured successfully');
          sendResponse({ imageData: dataUrl });
        }
      }
    );
    return true; // Keep message channel open for async response
  }
});

// Handle installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Screenshot Annotator Extension installed');
});

// Monitor memory usage
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && changes.screenshots) {
    const newScreenshots = changes.screenshots.newValue || [];
    console.log(`Screenshots updated: ${newScreenshots.length} total`);
    
    // Calculate approximate memory usage
    let totalSize = 0;
    newScreenshots.forEach(screenshot => {
      if (screenshot.imageData) {
        totalSize += screenshot.imageData.length;
      }
    });
    
    console.log(`Approximate memory usage: ${Math.round(totalSize / 1024)} KB`);
    
    // Warn if memory usage is high (50MB limit)
    if (totalSize > 50 * 1024 * 1024) {
      try {
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icons/icon48.png',
          title: 'Screenshot Annotator',
          message: 'Memory usage is high. Consider exporting and clearing screenshots.'
        });
      } catch (error) {
        console.log('Notification not available:', error);
      }
    }
  }
});