from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import json
from pdf_generator import ScreenshotPDFGenerator

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Ensure screenshots directory exists
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Initialize PDF generator
pdf_generator = ScreenshotPDFGenerator(SCREENSHOTS_DIR)

# Define Models
class Screenshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_width: int
    original_height: int
    display_width: int  # 90% of original
    display_height: int  # 90% of original
    created_at: datetime = Field(default_factory=datetime.utcnow)
    annotations: List[Dict[str, Any]] = []

class ScreenshotCreate(BaseModel):
    filename: str
    original_width: int
    original_height: int

class Annotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    screenshot_id: str
    text: str
    x: float  # X coordinate on display image (90% scale)
    y: float  # Y coordinate on display image (90% scale)
    pointer_x: float  # Where the pointer points to on display image
    pointer_y: float  # Where the pointer points to on display image
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnnotationCreate(BaseModel):
    text: str
    x: float
    y: float
    pointer_x: float
    pointer_y: float

# Helper functions
def calculate_display_size(original_width: int, original_height: int) -> tuple:
    """Calculate 90% display size"""
    return int(original_width * 0.9), int(original_height * 0.9)

def resize_image_for_display(image_path: str, display_width: int, display_height: int) -> str:
    """Resize image to 90% for display, return new filename"""
    with Image.open(image_path) as img:
        # Resize to 90% size for display
        resized_img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        # Save resized version
        base_name = Path(image_path).stem
        display_filename = f"{base_name}_display.png"
        display_path = SCREENSHOTS_DIR / display_filename
        
        # Optimize for memory and quality
        resized_img.save(display_path, "PNG", optimize=True, quality=85)
        
        return display_filename

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Screenshot Annotation API"}

@api_router.post("/screenshots/upload")
async def upload_screenshot(file: UploadFile = File(...)):
    """Upload a screenshot file"""
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = SCREENSHOTS_DIR / unique_filename
        
        # Save original file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Get image dimensions
        with Image.open(file_path) as img:
            original_width, original_height = img.size
        
        # Calculate display size (90%)
        display_width, display_height = calculate_display_size(original_width, original_height)
        
        # Create resized version for display
        display_filename = resize_image_for_display(str(file_path), display_width, display_height)
        
        # Create screenshot record
        screenshot = Screenshot(
            filename=unique_filename,
            original_width=original_width,
            original_height=original_height,
            display_width=display_width,
            display_height=display_height
        )
        
        # Save to database
        await db.screenshots.insert_one(screenshot.dict())
        
        return {
            "id": screenshot.id,
            "filename": unique_filename,
            "display_filename": display_filename,
            "original_size": {"width": original_width, "height": original_height},
            "display_size": {"width": display_width, "height": display_height}
        }
        
    except Exception as e:
        logging.error(f"Error uploading screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/screenshots/base64")
async def upload_screenshot_base64(data: dict):
    """Upload screenshot from base64 data"""
    try:
        # Extract base64 data
        image_data = data.get("image")
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Remove data:image/png;base64, prefix if present
        if image_data.startswith("data:"):
            image_data = image_data.split(",")[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Create image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        original_width, original_height = img.size
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        file_path = SCREENSHOTS_DIR / unique_filename
        
        # Save original file with memory optimization
        img.save(file_path, "PNG", optimize=True, quality=85)
        
        # Calculate display size (90%)
        display_width, display_height = calculate_display_size(original_width, original_height)
        
        # Create resized version for display
        display_filename = resize_image_for_display(str(file_path), display_width, display_height)
        
        # Create screenshot record
        screenshot = Screenshot(
            filename=unique_filename,
            original_width=original_width,
            original_height=original_height,
            display_width=display_width,
            display_height=display_height
        )
        
        # Save to database
        await db.screenshots.insert_one(screenshot.dict())
        
        return {
            "id": screenshot.id,
            "filename": unique_filename,
            "display_filename": display_filename,
            "original_size": {"width": original_width, "height": original_height},
            "display_size": {"width": display_width, "height": display_height}
        }
        
    except Exception as e:
        logging.error(f"Error processing base64 screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/screenshots", response_model=List[Screenshot])
async def get_screenshots():
    """Get all screenshots"""
    screenshots = await db.screenshots.find().to_list(1000)
    return [Screenshot(**screenshot) for screenshot in screenshots]

@api_router.get("/screenshots/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    """Get specific screenshot by ID"""
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return Screenshot(**screenshot)

@api_router.get("/screenshots/{screenshot_id}/file/{file_type}")
async def get_screenshot_file(screenshot_id: str, file_type: str):
    """Get screenshot file (original or display)"""
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    if file_type == "original":
        filename = screenshot["filename"]
    elif file_type == "display":
        # Generate display filename
        base_name = Path(screenshot["filename"]).stem
        filename = f"{base_name}_display.png"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Use 'original' or 'display'")
    
    file_path = SCREENSHOTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="image/png")

@api_router.post("/screenshots/{screenshot_id}/annotations")
async def add_annotation(screenshot_id: str, annotation_data: AnnotationCreate):
    """Add annotation to screenshot"""
    # Check if screenshot exists
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Create annotation
    annotation = Annotation(
        screenshot_id=screenshot_id,
        **annotation_data.dict()
    )
    
    # Add annotation to screenshot
    await db.screenshots.update_one(
        {"id": screenshot_id},
        {"$push": {"annotations": annotation.dict()}}
    )
    
    return annotation

@api_router.get("/screenshots/{screenshot_id}/annotations")
async def get_annotations(screenshot_id: str):
    """Get all annotations for a screenshot"""
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return screenshot.get("annotations", [])

@api_router.put("/screenshots/{screenshot_id}/annotations/{annotation_id}")
async def update_annotation(screenshot_id: str, annotation_id: str, annotation_data: AnnotationCreate):
    """Update an annotation"""
    # Update the annotation in the array
    result = await db.screenshots.update_one(
        {"id": screenshot_id, "annotations.id": annotation_id},
        {"$set": {
            "annotations.$.text": annotation_data.text,
            "annotations.$.x": annotation_data.x,
            "annotations.$.y": annotation_data.y,
            "annotations.$.pointer_x": annotation_data.pointer_x,
            "annotations.$.pointer_y": annotation_data.pointer_y
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"message": "Annotation updated"}

@api_router.delete("/screenshots/{screenshot_id}/annotations/{annotation_id}")
async def delete_annotation(screenshot_id: str, annotation_id: str):
    """Delete an annotation"""
    result = await db.screenshots.update_one(
        {"id": screenshot_id},
        {"$pull": {"annotations": {"id": annotation_id}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"message": "Annotation deleted"}

@api_router.delete("/screenshots/{screenshot_id}")
async def delete_screenshot(screenshot_id: str):
    """Delete screenshot and its files"""
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Delete files
    original_file = SCREENSHOTS_DIR / screenshot["filename"]
    if original_file.exists():
        original_file.unlink()
    
    # Delete display file
    base_name = Path(screenshot["filename"]).stem
    display_file = SCREENSHOTS_DIR / f"{base_name}_display.png"
    if display_file.exists():
        display_file.unlink()
    
    # Delete from database
    await db.screenshots.delete_one({"id": screenshot_id})
    
    return {"message": "Screenshot deleted"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()