# Screenshot Annotator Browser Extension

## ⚠️ IMPORTANT: THIS IS NOT A FULL-STACK APPLICATION

**This is a SIMPLE BROWSER EXTENSION ONLY.**

- ❌ **NO BACKEND SERVERS** (No FastAPI, Node.js, or any server)
- ❌ **NO DATABASES** (No MongoDB, PostgreSQL, or any database)  
- ❌ **NO COMPLEX BUILD PROCESS** (No webpack, npm build, or compilation)
- ❌ **NO EXTERNAL DEPENDENCIES** (No API calls or external services)
- ❌ **NO INSTALLATION COMMANDS** (No `npm install`, `pip install`, etc.)

**What this IS:**
- ✅ **Simple Browser Extension** - Just load into Chrome/Edge
- ✅ **Local Storage Only** - Everything stored in browser
- ✅ **Drag & Drop Installation** - No setup required
- ✅ **Works Offline** - No internet connection needed after installation

---

A lightweight browser extension for capturing webpage screenshots and adding precise text annotations with memory optimization.

## Features

✅ **Simple Screenshot Capture** - One-click webpage screenshot capture  
✅ **Precise Annotations** - Add text with arrow pointers to specific locations  
✅ **90% Display Sizing** - Automatic resize for accurate annotation placement  
✅ **Memory Management** - Real-time usage tracking with cleanup options  
✅ **Local Storage** - All data stored locally in browser (no external servers)  
✅ **Export Options** - Export annotated screenshots as HTML  
✅ **Easy Installation** - No complex setup required  

## Installation Instructions

### Method 1: Load as Unpacked Extension (Development)

1. **Download Extension Files**
   - Download all files in the `/extension/` folder to your computer
   - Keep the folder structure intact

2. **Open Chrome/Edge Extensions Page**
   - Chrome: Go to `chrome://extensions/`
   - Edge: Go to `edge://extensions/`

3. **Enable Developer Mode**
   - Toggle "Developer mode" ON (top-right corner)

4. **Load Extension**
   - Click "Load unpacked"
   - Select the `/extension/` folder containing the files
   - The extension should now appear in your extensions list

5. **Pin Extension (Recommended)**
   - Click the extensions icon (puzzle piece) in the toolbar
   - Find "Screenshot Annotator" and click the pin icon
   - The extension icon will now appear in your toolbar

### Method 2: Icon Creation (Optional)

If icons don't display properly, you can create simple icon files:

```bash
# Create basic icon files (you can replace with actual icons)
echo "📷" > /app/extension/icons/icon16.png
echo "📷" > /app/extension/icons/icon48.png  
echo "📷" > /app/extension/icons/icon128.png
```

## How to Use

### 1. Capture Screenshot
- Click the extension icon in your toolbar
- Click "📷 Capture Current Page"
- The current webpage will be captured and stored locally

### 2. Add Annotations
- Select a screenshot from the list
- Click "✏️ Start Annotating" 
- Enter your annotation text
- Click "Add Annotation"
- Click where you want the text to appear
- Click where you want the arrow to point
- Click "Save & Exit"

### 3. Memory Management
- View current memory usage in the popup
- Use "📄 Export PDF" to save your annotated screenshots
- Use "🗑️ Clear All" to free memory when needed

### 4. Export Your Work
- Select screenshots you want to export
- Click "📄 Export PDF" 
- Choose to export as HTML file
- Optionally clear screenshots after export to free memory

## Key Features Explained

### 90% Display Sizing
- Screenshots are automatically resized to 90% of original size
- This ensures accurate annotation placement and positioning
- Reduces memory usage while maintaining visual quality

### Memory Optimization
- Real-time memory usage tracking
- Smart storage management with local browser storage
- Export and cleanup options to prevent memory buildup
- Automatic warnings when storage usage gets high

### Precise Annotations
- Two-click annotation system for accuracy
- Visual arrow pointers connecting text to specific locations
- Sub-pixel positioning for detailed annotations
- Professional rendering with clear text backgrounds

## Troubleshooting

### Common Issues:

1. **Extension won't load**
   - Make sure all files are in the `/extension/` folder
   - Ensure Developer mode is enabled
   - Check browser console for error messages

2. **Screenshot capture fails**
   - Make sure you're on a valid webpage (not chrome:// or extension pages)
   - Grant screen capture permissions when prompted
   - Try refreshing the page and capturing again

3. **Annotations don't save**
   - Check if browser storage quota is exceeded
   - Clear some screenshots to free space
   - Ensure the page isn't blocking the content script

4. **Memory usage high**
   - Export screenshots as HTML to preserve annotations
   - Use "Clear All" to free browser storage
   - Consider capturing smaller screenshots

### Browser Permissions

The extension requires these permissions:
- **activeTab**: To capture the current webpage
- **storage**: To save screenshots and annotations locally  
- **desktopCapture**: For screenshot functionality

All data is stored locally in your browser - no external servers are used.

## Technical Details

### Architecture
- **Manifest V3**: Modern extension format
- **Local Storage**: All data stored in browser
- **Content Scripts**: Handle annotation overlay
- **Background Script**: Manages screenshot capture
- **No External Dependencies**: Works completely offline

### File Structure
```
extension/
├── manifest.json      # Extension configuration
├── popup.html         # Extension popup interface  
├── popup.js          # Popup functionality
├── background.js     # Background tasks
├── content.js        # Page annotation overlay
├── styles.css        # Extension styling
└── icons/           # Extension icons
```

### Storage Format
Screenshots are stored as base64 data URLs with metadata:
- Original dimensions and 90% display size
- Annotation coordinates and text
- Timestamp and URL information
- Memory usage tracking

## Privacy & Security

- **No Data Collection**: All data stays on your device
- **No External Servers**: Extension works completely offline
- **Local Storage Only**: Uses browser's local storage
- **No Network Requests**: No data sent anywhere
- **Source Code Available**: All code is visible and auditable

## Browser Compatibility

- ✅ Chrome 88+
- ✅ Microsoft Edge 88+  
- ✅ Chromium-based browsers
- ❌ Firefox (uses different extension format)
- ❌ Safari (uses different extension format)

## Version History

**v1.0** - Initial release
- Screenshot capture functionality
- Text annotations with arrow pointers
- 90% display sizing for accuracy
- Memory management and optimization
- HTML export functionality
- Local storage management

---

**No complex setup, no servers, no accounts needed - just install and start annotating!**