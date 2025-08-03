from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import red, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage, ImageDraw, ImageFont
import io
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ScreenshotPDFGenerator:
    def __init__(self, screenshots_dir: Path):
        self.screenshots_dir = screenshots_dir
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Screenshot info style
        self.info_style = ParagraphStyle(
            'ScreenshotInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            textColor=black
        )
        
        # Annotation style
        self.annotation_style = ParagraphStyle(
            'AnnotationText',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=20,
            spaceAfter=6,
            textColor=red
        )

    def create_annotated_image(self, screenshot: Dict[str, Any]) -> io.BytesIO:
        """Create an image with annotations rendered directly on it"""
        try:
            # Load the display image
            image_filename = Path(screenshot["filename"]).stem + "_display.png"
            image_path = self.screenshots_dir / image_filename
            
            if not image_path.exists():
                # Fallback to original image
                image_path = self.screenshots_dir / screenshot["filename"]
            
            # Open and copy the image
            with PILImage.open(image_path) as img:
                # Create a copy to draw on
                annotated_img = img.copy()
                draw = ImageDraw.Draw(annotated_img)
                
                # Draw annotations
                for annotation in screenshot.get("annotations", []):
                    x = annotation["x"]
                    y = annotation["y"]
                    pointer_x = annotation["pointer_x"]
                    pointer_y = annotation["pointer_y"]
                    text = annotation["text"]
                    
                    # Draw arrow line
                    draw.line([(x, y), (pointer_x, pointer_y)], fill='red', width=3)
                    
                    # Draw arrowhead
                    import math
                    angle = math.atan2(pointer_y - y, pointer_x - x)
                    arrow_length = 12
                    
                    # Calculate arrowhead points
                    arrow_x1 = pointer_x - arrow_length * math.cos(angle - math.pi / 6)
                    arrow_y1 = pointer_y - arrow_length * math.sin(angle - math.pi / 6)
                    arrow_x2 = pointer_x - arrow_length * math.cos(angle + math.pi / 6)
                    arrow_y2 = pointer_y - arrow_length * math.sin(angle + math.pi / 6)
                    
                    # Draw arrowhead
                    draw.line([(pointer_x, pointer_y), (arrow_x1, arrow_y1)], fill='red', width=3)
                    draw.line([(pointer_x, pointer_y), (arrow_x2, arrow_y2)], fill='red', width=3)
                    
                    # Draw pointer dot
                    draw.ellipse([
                        pointer_x - 4, pointer_y - 4,
                        pointer_x + 4, pointer_y + 4
                    ], fill='red')
                    
                    # Draw text background
                    try:
                        font = ImageFont.truetype("arial.ttf", 14)
                    except:
                        font = ImageFont.load_default()
                    
                    # Get text size
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # Draw text background
                    draw.rectangle([
                        x - 2, y - text_height - 6,
                        x + text_width + 2, y - 2
                    ], fill='white', outline='red', width=1)
                    
                    # Draw text
                    draw.text((x, y - text_height - 4), text, fill='black', font=font)
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                annotated_img.save(img_bytes, format='PNG', optimize=True)
                img_bytes.seek(0)
                
                return img_bytes
                
        except Exception as e:
            logger.error(f"Error creating annotated image: {e}")
            # Return original image if annotation fails
            with open(image_path, 'rb') as f:
                return io.BytesIO(f.read())

    def generate_pdf(self, screenshots: List[Dict[str, Any]], title: str = None) -> io.BytesIO:
        """Generate PDF from screenshots with annotations"""
        try:
            # Create PDF buffer
            pdf_buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )
            
            # Story elements
            story = []
            
            # Title
            if not title:
                title = f"Screenshot Collection - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Add summary
            summary_text = f"""
            <b>Collection Summary:</b><br/>
            Total Screenshots: {len(screenshots)}<br/>
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            Total Annotations: {sum(len(s.get('annotations', [])) for s in screenshots)}
            """
            story.append(Paragraph(summary_text, self.info_style))
            story.append(Spacer(1, 20))
            
            # Add each screenshot
            for i, screenshot in enumerate(screenshots, 1):
                # Screenshot info
                created_at_str = screenshot['created_at']
                # Handle different datetime formats
                if isinstance(created_at_str, str):
                    if created_at_str.endswith('Z'):
                        created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_dt = datetime.fromisoformat(created_at_str)
                else:
                    # If it's already a datetime object
                    created_dt = created_at_str
                
                info_text = f"""
                <b>Screenshot #{i}</b><br/>
                Created: {created_dt.strftime('%Y-%m-%d %H:%M:%S')}<br/>
                Original Size: {screenshot['original_width']} × {screenshot['original_height']} pixels<br/>
                Display Size: {screenshot['display_width']} × {screenshot['display_height']} pixels<br/>
                Annotations: {len(screenshot.get('annotations', []))}
                """
                story.append(Paragraph(info_text, self.info_style))
                
                # Create annotated image
                img_bytes = self.create_annotated_image(screenshot)
                
                # Add image to PDF with size constraints
                img = Image(img_bytes, width=7*inch, height=None)  # Maintain aspect ratio
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 10))
                
                # Add annotation details
                annotations = screenshot.get('annotations', [])
                if annotations:
                    story.append(Paragraph("<b>Annotations:</b>", self.info_style))
                    for j, annotation in enumerate(annotations, 1):
                        annotation_text = f"""
                        {j}. "{annotation['text']}"<br/>
                        &nbsp;&nbsp;&nbsp;&nbsp;Position: ({int(annotation['x'])}, {int(annotation['y'])}) → 
                        ({int(annotation['pointer_x'])}, {int(annotation['pointer_y'])})
                        """
                        story.append(Paragraph(annotation_text, self.annotation_style))
                
                # Add page break except for last screenshot
                if i < len(screenshots):
                    story.append(PageBreak())
            
            # Build PDF
            doc.build(story)
            
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")

    def get_memory_usage(self, screenshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate memory usage of screenshots"""
        total_size = 0
        file_count = 0
        
        for screenshot in screenshots:
            # Original file
            original_path = self.screenshots_dir / screenshot["filename"]
            if original_path.exists():
                total_size += original_path.stat().st_size
                file_count += 1
            
            # Display file
            display_filename = Path(screenshot["filename"]).stem + "_display.png"
            display_path = self.screenshots_dir / display_filename
            if display_path.exists():
                total_size += display_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "screenshots": len(screenshots)
        }