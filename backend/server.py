from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse, Response
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

class PDFExportRequest(BaseModel):
    screenshot_ids: List[str]
    title: Optional[str] = None
    cleanup_after_export: bool = False

class MemoryUsageResponse(BaseModel):
    total_size_bytes: int
    total_size_mb: float
    file_count: int
    screenshots: int

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

@api_router.post("/export/pdf")
async def export_screenshots_to_pdf(export_request: PDFExportRequest):
    """Export selected screenshots to PDF with optional cleanup"""
    try:
        # Fetch screenshots
        screenshots_data = []
        for screenshot_id in export_request.screenshot_ids:
            screenshot = await db.screenshots.find_one({"id": screenshot_id})
            if screenshot:
                screenshots_data.append(screenshot)
        
        if not screenshots_data:
            raise HTTPException(status_code=404, detail="No valid screenshots found")
        
        # Calculate memory usage before export
        memory_before = pdf_generator.get_memory_usage(screenshots_data)
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_pdf(
            screenshots_data, 
            title=export_request.title
        )
        
        # Prepare response data
        export_info = {
            "exported_screenshots": len(screenshots_data),
            "total_annotations": sum(len(s.get('annotations', [])) for s in screenshots_data),
            "memory_freed": 0,
            "cleanup_performed": False
        }
        
        # Optional cleanup after export
        if export_request.cleanup_after_export:
            deleted_count = 0
            memory_freed = 0
            
            for screenshot in screenshots_data:
                # Calculate file sizes before deletion
                original_file = SCREENSHOTS_DIR / screenshot["filename"]
                display_file = SCREENSHOTS_DIR / f"{Path(screenshot['filename']).stem}_display.png"
                
                file_size = 0
                if original_file.exists():
                    file_size += original_file.stat().st_size
                    original_file.unlink()
                
                if display_file.exists():
                    file_size += display_file.stat().st_size
                    display_file.unlink()
                
                memory_freed += file_size
                
                # Delete from database
                await db.screenshots.delete_one({"id": screenshot["id"]})
                deleted_count += 1
            
            export_info.update({
                "memory_freed": round(memory_freed / (1024 * 1024), 2),  # MB
                "cleanup_performed": True,
                "deleted_screenshots": deleted_count
            })
        
        # Create filename for download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots_export_{timestamp}.pdf"
        
        # Return PDF as response
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.get("/memory/usage")
async def get_memory_usage():
    """Get current memory usage of all screenshots"""
    try:
        # Get all screenshots
        screenshots = await db.screenshots.find().to_list(1000)
        
        if not screenshots:
            return {
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "file_count": 0,
                "screenshots": 0
            }
        
        # Calculate usage
        usage = pdf_generator.get_memory_usage(screenshots)
        return usage
        
    except Exception as e:
        logging.error(f"Error calculating memory usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/memory/cleanup")
async def cleanup_all_screenshots():
    """Delete all screenshots and free up memory"""
    try:
        # Get all screenshots
        screenshots = await db.screenshots.find().to_list(1000)
        
        if not screenshots:
            return {"message": "No screenshots to delete", "memory_freed": 0}
        
        # Calculate memory before deletion
        memory_usage = pdf_generator.get_memory_usage(screenshots)
        
        deleted_count = 0
        for screenshot in screenshots:
            # Delete files
            original_file = SCREENSHOTS_DIR / screenshot["filename"]
            if original_file.exists():
                original_file.unlink()
            
            display_file = SCREENSHOTS_DIR / f"{Path(screenshot['filename']).stem}_display.png"
            if display_file.exists():
                display_file.unlink()
            
            deleted_count += 1
        
        # Delete all from database
        result = await db.screenshots.delete_many({})
        
        return {
            "message": f"Deleted {deleted_count} screenshots",
            "memory_freed": memory_usage["total_size_mb"],
            "deleted_from_db": result.deleted_count
        }
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/export/preview/{screenshot_id}")
async def preview_screenshot_for_export(screenshot_id: str):
    """Get a preview of how a screenshot will look in PDF export"""
    try:
        screenshot = await db.screenshots.find_one({"id": screenshot_id})
        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")
        
        # Generate annotated image
        annotated_img = pdf_generator.create_annotated_image(screenshot)
        
        return Response(
            content=annotated_img.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=preview_{screenshot_id}.png"}
        )
        
    except Exception as e:
        logging.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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