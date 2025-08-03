# 🚨 CRITICAL DEVELOPMENT NOTES 🚨

## PROJECT TYPE: BROWSER EXTENSION ONLY

### ⚠️ THIS IS NOT A FULL-STACK APPLICATION ⚠️

**REMEMBER:** This project is a **simple browser extension** and should NEVER be treated as a full-stack application.

---

## What This Project IS:
- ✅ **Browser Extension** - Manifest V3 Chrome/Edge extension
- ✅ **Client-Side Only** - Runs entirely in the browser
- ✅ **Local Storage** - Uses browser's local storage API
- ✅ **No Servers** - Zero backend infrastructure
- ✅ **Simple Installation** - Load unpacked extension in browser

## What This Project IS NOT:
- ❌ **Full-Stack App** - No server-client architecture
- ❌ **Web Application** - Not hosted on any domain
- ❌ **Backend API** - No FastAPI, Express, or any server
- ❌ **Database Application** - No MongoDB, SQL, or any database
- ❌ **Complex Build** - No webpack, Docker, or build processes

---

## Architecture Overview:

```
Browser Extension Architecture:
┌─────────────────────┐
│   Browser Only      │
├─────────────────────┤
│ popup.html/js       │ ← Extension popup interface
│ content.js          │ ← Injected into webpages  
│ background.js       │ ← Service worker
│ manifest.json       │ ← Extension configuration
└─────────────────────┘
         ↓
┌─────────────────────┐
│ Browser Local       │
│ Storage API         │ ← All data stored here
└─────────────────────┘
```

**NO EXTERNAL COMPONENTS** - Everything runs inside the browser.

---

## Installation Method:
1. Copy extension files to local folder
2. Open `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the extension folder

**NO** `npm install`, **NO** server setup, **NO** database configuration.

---

## File Structure:
```
/app/extension/           ← ONLY these files matter
├── manifest.json         ← Extension config
├── popup.html           ← UI interface
├── popup.js             ← Main logic
├── background.js        ← Service worker
├── content.js           ← Page injection script
├── styles.css           ← Styling
└── icons/              ← Extension icons
```

**IGNORE** any other folders like `/app/backend/` or `/app/frontend/` - they are NOT part of this project.

---

## Key Reminders for Developers:

### ✅ DO:
- Treat this as a browser extension project
- Use Chrome extension APIs
- Store data in browser local storage
- Focus on client-side JavaScript
- Test by loading in Chrome/Edge
- Use manifest.json for configuration

### ❌ DON'T:
- Create backend servers or APIs
- Set up databases or data persistence layers
- Use npm/yarn for dependency management
- Create complex build processes
- Try to deploy to web servers
- Use server-side languages (Python, Node.js server)

---

## Memory Optimization Context:
The "memory optimization" refers to:
- **Browser Storage Management** - Not server memory
- **Local Data Cleanup** - Clearing browser storage
- **Image Size Reduction** - 90% display sizing
- **Storage Quota Management** - Browser storage limits

**NOT server memory, RAM usage, or database optimization.**

---

## 🎯 Project Goal:
Create a **simple, lightweight browser extension** that:
1. Captures webpage screenshots
2. Adds text annotations with arrows
3. Manages local storage efficiently  
4. Exports annotated screenshots
5. Works entirely offline in browser

**Period. Nothing more, nothing less.**

---

## If Someone Suggests Full-Stack Features:
**STOP THEM IMMEDIATELY** and remind them:
- This is a browser extension
- No servers allowed
- No databases allowed  
- No complex architectures
- Keep it simple and local

---

**REMEMBER: Simple browser extension = Happy users + Easy maintenance**