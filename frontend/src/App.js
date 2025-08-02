import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScreenshotAnnotationApp = () => {
  const [screenshots, setScreenshots] = useState([]);
  const [currentScreenshot, setCurrentScreenshot] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isAnnotating, setIsAnnotating] = useState(false);
  const [annotationText, setAnnotationText] = useState("");
  const [annotations, setAnnotations] = useState([]);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const [pendingAnnotation, setPendingAnnotation] = useState(null);

  // Load screenshots on component mount
  useEffect(() => {
    fetchScreenshots();
  }, []);

  // Load annotations when screenshot changes
  useEffect(() => {
    if (currentScreenshot) {
      fetchAnnotations(currentScreenshot.id);
    }
  }, [currentScreenshot]);

  const fetchScreenshots = async () => {
    try {
      const response = await axios.get(`${API}/screenshots`);
      setScreenshots(response.data);
    } catch (error) {
      console.error("Error fetching screenshots:", error);
    }
  };

  const fetchAnnotations = async (screenshotId) => {
    try {
      const response = await axios.get(`${API}/screenshots/${screenshotId}/annotations`);
      setAnnotations(response.data);
    } catch (error) {
      console.error("Error fetching annotations:", error);
    }
  };

  const captureCurrentPage = async () => {
    setIsCapturing(true);
    try {
      // Use html2canvas-like approach or browser screenshot API
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // For now, we'll use the Screen Capture API (requires user permission)
      if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: {
            mediaSource: 'screen',
            width: { max: 1920 },
            height: { max: 1080 }
          }
        });
        
        const video = document.createElement('video');
        video.srcObject = stream;
        video.play();
        
        video.addEventListener('loadedmetadata', () => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0);
          
          // Stop the stream
          stream.getTracks().forEach(track => track.stop());
          
          // Convert to base64 and upload
          const imageData = canvas.toDataURL('image/png');
          uploadScreenshot(imageData);
        });
      } else {
        alert('Screen capture not supported in this browser');
      }
    } catch (error) {
      console.error("Error capturing screenshot:", error);
      alert('Error capturing screenshot. Please try again.');
    } finally {
      setIsCapturing(false);
    }
  };

  const uploadScreenshot = async (imageData) => {
    try {
      const response = await axios.post(`${API}/screenshots/base64`, {
        image: imageData
      });
      
      // Refresh screenshots list
      await fetchScreenshots();
      
      // Select the newly uploaded screenshot
      setCurrentScreenshot(response.data);
      
      console.log("Screenshot uploaded successfully:", response.data);
    } catch (error) {
      console.error("Error uploading screenshot:", error);
      alert('Error uploading screenshot');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/screenshots/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      await fetchScreenshots();
      setCurrentScreenshot(response.data);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert('Error uploading file');
    }
  };

  const handleImageClick = (event) => {
    if (!isAnnotating || !currentScreenshot) return;

    const rect = imageRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (pendingAnnotation) {
      // This is the second click - set the pointer location
      const newAnnotation = {
        ...pendingAnnotation,
        pointer_x: x,
        pointer_y: y
      };
      
      addAnnotation(newAnnotation);
      setPendingAnnotation(null);
      setIsAnnotating(false);
      setAnnotationText("");
    } else {
      // This is the first click - set the text location
      setPendingAnnotation({
        text: annotationText,
        x: x,
        y: y,
        pointer_x: x, // Default to same position, user will click again
        pointer_y: y
      });
    }
  };

  const addAnnotation = async (annotationData) => {
    try {
      await axios.post(`${API}/screenshots/${currentScreenshot.id}/annotations`, annotationData);
      await fetchAnnotations(currentScreenshot.id);
    } catch (error) {
      console.error("Error adding annotation:", error);
      alert('Error adding annotation');
    }
  };

  const deleteAnnotation = async (annotationId) => {
    try {
      await axios.delete(`${API}/screenshots/${currentScreenshot.id}/annotations/${annotationId}`);
      await fetchAnnotations(currentScreenshot.id);
    } catch (error) {
      console.error("Error deleting annotation:", error);
    }
  };

  const startAnnotation = () => {
    if (!annotationText.trim()) {
      alert('Please enter annotation text first');
      return;
    }
    setIsAnnotating(true);
    setPendingAnnotation(null);
  };

  const cancelAnnotation = () => {
    setIsAnnotating(false);
    setPendingAnnotation(null);
  };

  const drawAnnotations = () => {
    if (!canvasRef.current || !imageRef.current || !currentScreenshot) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = imageRef.current;

    // Set canvas size to match the displayed image
    canvas.width = img.width;
    canvas.height = img.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw all annotations
    annotations.forEach(annotation => {
      // Draw arrow/pointer line
      ctx.beginPath();
      ctx.moveTo(annotation.x, annotation.y);
      ctx.lineTo(annotation.pointer_x, annotation.pointer_y);
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw arrowhead
      const angle = Math.atan2(annotation.pointer_y - annotation.y, annotation.pointer_x - annotation.x);
      const arrowLength = 10;
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

      // Draw text background
      ctx.font = '14px Arial';
      const textMetrics = ctx.measureText(annotation.text);
      const padding = 4;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(
        annotation.x - padding,
        annotation.y - 20 - padding,
        textMetrics.width + padding * 2,
        20 + padding * 2
      );

      // Draw text
      ctx.fillStyle = '#000000';
      ctx.fillText(annotation.text, annotation.x, annotation.y - 4);

      // Draw point indicator
      ctx.beginPath();
      ctx.arc(annotation.pointer_x, annotation.pointer_y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#ff0000';
      ctx.fill();
    });

    // Draw pending annotation if exists
    if (pendingAnnotation) {
      ctx.fillStyle = 'rgba(255, 255, 0, 0.7)';
      ctx.fillRect(
        pendingAnnotation.x - 2,
        pendingAnnotation.y - 18,
        ctx.measureText(pendingAnnotation.text).width + 4,
        20
      );
      ctx.fillStyle = '#000000';
      ctx.fillText(pendingAnnotation.text, pendingAnnotation.x, pendingAnnotation.y - 2);
    }
  };

  // Redraw annotations when they change
  useEffect(() => {
    drawAnnotations();
  }, [annotations, pendingAnnotation, currentScreenshot]);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          Screenshot Annotation Tool
        </h1>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-4">
              <button
                onClick={captureCurrentPage}
                disabled={isCapturing}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {isCapturing ? "Capturing..." : "Capture Screen"}
              </button>

              <label className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg cursor-pointer">
                Upload Screenshot
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            <div className="text-sm text-gray-600">
              Screenshots: {screenshots.length}
            </div>
          </div>

          {/* Annotation Controls */}
          {currentScreenshot && (
            <div className="mt-4 border-t pt-4">
              <div className="flex flex-wrap gap-4 items-center">
                <input
                  type="text"
                  value={annotationText}
                  onChange={(e) => setAnnotationText(e.target.value)}
                  placeholder="Enter annotation text..."
                  className="flex-1 min-w-64 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                {!isAnnotating ? (
                  <button
                    onClick={startAnnotation}
                    className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
                  >
                    Add Annotation
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <span className="text-sm text-gray-600 py-2">
                      {pendingAnnotation ? "Click where to point" : "Click where to place text"}
                    </span>
                    <button
                      onClick={cancelAnnotation}
                      className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-6">
          {/* Screenshots List */}
          <div className="w-64 bg-white rounded-lg shadow-md p-4">
            <h2 className="text-lg font-semibold mb-4">Screenshots</h2>
            <div className="space-y-2">
              {screenshots.map((screenshot) => (
                <div
                  key={screenshot.id}
                  onClick={() => setCurrentScreenshot(screenshot)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentScreenshot?.id === screenshot.id
                      ? "bg-blue-100 border-2 border-blue-500"
                      : "bg-gray-50 hover:bg-gray-100"
                  }`}
                >
                  <div className="text-sm font-medium">
                    {new Date(screenshot.created_at).toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-600">
                    {screenshot.display_width} x {screenshot.display_height}
                  </div>
                  <div className="text-xs text-gray-500">
                    {screenshot.annotations.length} annotations
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 bg-white rounded-lg shadow-md p-4">
            {currentScreenshot ? (
              <div>
                <div className="mb-4 flex justify-between items-center">
                  <h2 className="text-lg font-semibold">
                    Screenshot ({currentScreenshot.display_width} x {currentScreenshot.display_height})
                  </h2>
                  <div className="text-sm text-gray-600">
                    Annotations: {annotations.length}
                  </div>
                </div>

                <div className="relative inline-block">
                  <img
                    ref={imageRef}
                    src={`${API}/screenshots/${currentScreenshot.id}/file/display`}
                    alt="Screenshot"
                    onClick={handleImageClick}
                    className={`max-w-full h-auto border-2 border-gray-300 ${
                      isAnnotating ? "cursor-crosshair" : "cursor-default"
                    }`}
                    onLoad={drawAnnotations}
                  />
                  <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 pointer-events-none"
                  />
                </div>

                {/* Annotations List */}
                {annotations.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">Annotations</h3>
                    <div className="space-y-2">
                      {annotations.map((annotation) => (
                        <div
                          key={annotation.id}
                          className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <div className="font-medium">{annotation.text}</div>
                            <div className="text-sm text-gray-600">
                              Position: ({Math.round(annotation.x)}, {Math.round(annotation.y)}) →
                              ({Math.round(annotation.pointer_x)}, {Math.round(annotation.pointer_y)})
                            </div>
                          </div>
                          <button
                            onClick={() => deleteAnnotation(annotation.id)}
                            className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-20 text-gray-500">
                <p className="text-xl mb-4">No screenshot selected</p>
                <p>Capture a screenshot or upload an image to get started</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <ScreenshotAnnotationApp />
    </div>
  );
}

export default App;