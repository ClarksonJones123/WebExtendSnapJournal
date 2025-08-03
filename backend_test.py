import requests
import sys
import os
import base64
import io
from PIL import Image
from datetime import datetime
import json

class ScreenshotAPITester:
    def __init__(self, base_url="https://a94e0096-2120-40ab-94be-a87e0b28a87f.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.screenshot_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_test_image(self, width=1000, height=800):
        """Create a test image for upload testing"""
        # Create a test image with specific dimensions
        img = Image.new('RGB', (width, height), color='lightblue')
        
        # Add some content to make it realistic
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Draw some test content
        draw.rectangle([50, 50, width-50, height-50], outline='red', width=3)
        draw.text((100, 100), f"Test Image {width}x{height}", fill='black')
        draw.text((100, 150), f"Created: {datetime.now()}", fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        return img_bytes, width, height

    def test_root_endpoint(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_file_upload(self):
        """Test file upload with memory and sizing verification"""
        print("\n📁 Testing File Upload with Memory & Sizing...")
        
        # Create test image
        img_bytes, original_width, original_height = self.create_test_image(1200, 900)
        
        success, response = self.run_test(
            "File Upload",
            "POST",
            "screenshots/upload",
            200,
            files={'file': ('test_screenshot.png', img_bytes, 'image/png')}
        )
        
        if success:
            self.screenshot_id = response['id']
            
            # Verify sizing calculations
            expected_display_width = int(original_width * 0.9)
            expected_display_height = int(original_height * 0.9)
            
            print(f"   Original size: {original_width}x{original_height}")
            print(f"   Expected display size: {expected_display_width}x{expected_display_height}")
            print(f"   Actual display size: {response['display_size']['width']}x{response['display_size']['height']}")
            
            if (response['display_size']['width'] == expected_display_width and 
                response['display_size']['height'] == expected_display_height):
                print("✅ 90% resizing calculation correct")
            else:
                print("❌ 90% resizing calculation incorrect")
                
        return success

    def test_base64_upload(self):
        """Test base64 upload with memory efficiency"""
        print("\n📷 Testing Base64 Upload...")
        
        # Create test image
        img_bytes, original_width, original_height = self.create_test_image(800, 600)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        image_data = f"data:image/png;base64,{img_base64}"
        
        success, response = self.run_test(
            "Base64 Upload",
            "POST",
            "screenshots/base64",
            200,
            data={"image": image_data}
        )
        
        if success:
            # Verify sizing
            expected_display_width = int(original_width * 0.9)
            expected_display_height = int(original_height * 0.9)
            
            print(f"   Base64 size: {len(img_base64)} characters")
            print(f"   Display size verification: {response['display_size']['width']}x{response['display_size']['height']}")
            
            if (response['display_size']['width'] == expected_display_width and 
                response['display_size']['height'] == expected_display_height):
                print("✅ Base64 upload sizing correct")
            else:
                print("❌ Base64 upload sizing incorrect")
                
        return success

    def test_get_screenshots(self):
        """Test getting all screenshots"""
        success, response = self.run_test(
            "Get All Screenshots",
            "GET",
            "screenshots",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} screenshots")
            
        return success

    def test_get_screenshot_by_id(self):
        """Test getting specific screenshot"""
        if not self.screenshot_id:
            print("⚠️  Skipping - No screenshot ID available")
            return True
            
        success, response = self.run_test(
            "Get Screenshot by ID",
            "GET",
            f"screenshots/{self.screenshot_id}",
            200
        )
        
        if success:
            print(f"   Screenshot ID: {response.get('id')}")
            print(f"   Display size: {response.get('display_width')}x{response.get('display_height')}")
            
        return success

    def test_get_screenshot_files(self):
        """Test getting screenshot files (original and display)"""
        if not self.screenshot_id:
            print("⚠️  Skipping - No screenshot ID available")
            return True
            
        # Test original file
        success1, _ = self.run_test(
            "Get Original File",
            "GET",
            f"screenshots/{self.screenshot_id}/file/original",
            200
        )
        
        # Test display file
        success2, _ = self.run_test(
            "Get Display File",
            "GET",
            f"screenshots/{self.screenshot_id}/file/display",
            200
        )
        
        return success1 and success2

    def test_annotation_crud(self):
        """Test annotation CRUD operations"""
        if not self.screenshot_id:
            print("⚠️  Skipping - No screenshot ID available")
            return True
            
        print("\n📝 Testing Annotation CRUD...")
        
        # Create annotation
        annotation_data = {
            "text": "Test Annotation",
            "x": 100.5,
            "y": 150.5,
            "pointer_x": 200.5,
            "pointer_y": 250.5
        }
        
        success1, response = self.run_test(
            "Create Annotation",
            "POST",
            f"screenshots/{self.screenshot_id}/annotations",
            200,
            data=annotation_data
        )
        
        annotation_id = None
        if success1:
            annotation_id = response.get('id')
            print(f"   Created annotation ID: {annotation_id}")
        
        # Get annotations
        success2, annotations = self.run_test(
            "Get Annotations",
            "GET",
            f"screenshots/{self.screenshot_id}/annotations",
            200
        )
        
        if success2:
            print(f"   Found {len(annotations)} annotations")
        
        # Update annotation
        success3 = True
        if annotation_id:
            updated_data = {
                "text": "Updated Test Annotation",
                "x": 110.5,
                "y": 160.5,
                "pointer_x": 210.5,
                "pointer_y": 260.5
            }
            
            success3, _ = self.run_test(
                "Update Annotation",
                "PUT",
                f"screenshots/{self.screenshot_id}/annotations/{annotation_id}",
                200,
                data=updated_data
            )
        
        # Delete annotation
        success4 = True
        if annotation_id:
            success4, _ = self.run_test(
                "Delete Annotation",
                "DELETE",
                f"screenshots/{self.screenshot_id}/annotations/{annotation_id}",
                200
            )
        
        return success1 and success2 and success3 and success4

    def test_memory_usage_tracking(self):
        """Test memory usage tracking endpoint"""
        print("\n📊 Testing Memory Usage Tracking...")
        
        success, response = self.run_test(
            "Get Memory Usage",
            "GET",
            "memory/usage",
            200
        )
        
        if success:
            print(f"   Total memory usage: {response.get('total_size_mb', 0)} MB")
            print(f"   Total files: {response.get('file_count', 0)}")
            print(f"   Screenshots: {response.get('screenshots', 0)}")
            
            # Verify response structure
            required_fields = ['total_size_bytes', 'total_size_mb', 'file_count', 'screenshots']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in memory usage response: {field}")
                    return False
            
            print("✅ Memory usage tracking working correctly")
        
        return success

    def test_pdf_export_without_cleanup(self):
        """Test PDF export without cleanup"""
        if not self.screenshot_id:
            print("⚠️  Skipping - No screenshot ID available")
            return True
            
        print("\n📄 Testing PDF Export (without cleanup)...")
        
        # First, add an annotation to make the export more meaningful
        annotation_data = {
            "text": "PDF Export Test Annotation",
            "x": 150.0,
            "y": 200.0,
            "pointer_x": 300.0,
            "pointer_y": 350.0
        }
        
        # Add annotation
        self.run_test(
            "Add Annotation for PDF",
            "POST",
            f"screenshots/{self.screenshot_id}/annotations",
            200,
            data=annotation_data
        )
        
        # Test PDF export
        export_data = {
            "screenshot_ids": [self.screenshot_id],
            "title": "Test PDF Export",
            "cleanup_after_export": False
        }
        
        success, response = self.run_test(
            "PDF Export (no cleanup)",
            "POST",
            "export/pdf",
            200,
            data=export_data
        )
        
        if success:
            # Check if we got PDF content (response should be binary)
            if isinstance(response, str) and len(response) > 1000:
                print("✅ PDF export generated successfully")
                print(f"   PDF size: {len(response)} bytes")
            else:
                print("❌ PDF export may have failed - unexpected response size")
                return False
        
        return success

    def test_pdf_export_with_cleanup(self):
        """Test PDF export with cleanup enabled"""
        print("\n📄 Testing PDF Export (with cleanup)...")
        
        # Create a new screenshot specifically for cleanup testing
        img_bytes, _, _ = self.create_test_image(800, 600)
        
        success1, response = self.run_test(
            "Upload Screenshot for Cleanup Test",
            "POST",
            "screenshots/upload",
            200,
            files={'file': ('cleanup_test.png', img_bytes, 'image/png')}
        )
        
        if not success1:
            return False
            
        cleanup_screenshot_id = response['id']
        
        # Add annotation
        annotation_data = {
            "text": "Cleanup Test Annotation",
            "x": 100.0,
            "y": 150.0,
            "pointer_x": 250.0,
            "pointer_y": 300.0
        }
        
        self.run_test(
            "Add Annotation for Cleanup Test",
            "POST",
            f"screenshots/{cleanup_screenshot_id}/annotations",
            200,
            data=annotation_data
        )
        
        # Get memory usage before export
        success2, memory_before = self.run_test(
            "Memory Usage Before Export",
            "GET",
            "memory/usage",
            200
        )
        
        if success2:
            print(f"   Memory before export: {memory_before.get('total_size_mb', 0)} MB")
        
        # Test PDF export with cleanup
        export_data = {
            "screenshot_ids": [cleanup_screenshot_id],
            "title": "Cleanup Test PDF",
            "cleanup_after_export": True
        }
        
        success3, response = self.run_test(
            "PDF Export (with cleanup)",
            "POST",
            "export/pdf",
            200,
            data=export_data
        )
        
        if success3:
            print("✅ PDF export with cleanup completed")
            print(f"   PDF size: {len(response) if isinstance(response, str) else 'Unknown'} bytes")
            
            # Verify screenshot was deleted
            success4, _ = self.run_test(
                "Verify Screenshot Deleted",
                "GET",
                f"screenshots/{cleanup_screenshot_id}",
                404  # Should be 404 since it was deleted
            )
            
            if success4:
                print("✅ Screenshot successfully deleted after export")
            else:
                print("❌ Screenshot was not deleted after export")
                return False
                
            # Check memory usage after cleanup
            success5, memory_after = self.run_test(
                "Memory Usage After Cleanup",
                "GET",
                "memory/usage",
                200
            )
            
            if success5:
                print(f"   Memory after cleanup: {memory_after.get('total_size_mb', 0)} MB")
                if memory_before and memory_after:
                    memory_freed = memory_before.get('total_size_mb', 0) - memory_after.get('total_size_mb', 0)
                    print(f"   Memory freed: {memory_freed} MB")
        
        return success1 and success3

    def test_export_preview(self):
        """Test export preview functionality"""
        if not self.screenshot_id:
            print("⚠️  Skipping - No screenshot ID available")
            return True
            
        print("\n🔍 Testing Export Preview...")
        
        success, response = self.run_test(
            "Export Preview",
            "GET",
            f"export/preview/{self.screenshot_id}",
            200
        )
        
        if success:
            # Response should be image data
            if isinstance(response, str) and len(response) > 1000:
                print("✅ Export preview generated successfully")
                print(f"   Preview size: {len(response)} bytes")
            else:
                print("❌ Export preview may have failed - unexpected response size")
                return False
        
        return success

    def test_bulk_memory_cleanup(self):
        """Test bulk memory cleanup functionality"""
        print("\n🧹 Testing Bulk Memory Cleanup...")
        
        # Create multiple screenshots for cleanup testing
        screenshot_ids = []
        for i in range(3):
            img_bytes, _, _ = self.create_test_image(600, 400)
            success, response = self.run_test(
                f"Upload Screenshot {i+1} for Bulk Cleanup",
                "POST",
                "screenshots/upload",
                200,
                files={'file': (f'bulk_cleanup_{i}.png', img_bytes, 'image/png')}
            )
            
            if success:
                screenshot_ids.append(response['id'])
        
        if len(screenshot_ids) < 3:
            print("❌ Failed to create test screenshots for bulk cleanup")
            return False
        
        # Get memory usage before cleanup
        success1, memory_before = self.run_test(
            "Memory Usage Before Bulk Cleanup",
            "GET",
            "memory/usage",
            200
        )
        
        if success1:
            print(f"   Memory before bulk cleanup: {memory_before.get('total_size_mb', 0)} MB")
            print(f"   Screenshots before cleanup: {memory_before.get('screenshots', 0)}")
        
        # Perform bulk cleanup
        success2, cleanup_response = self.run_test(
            "Bulk Memory Cleanup",
            "POST",
            "memory/cleanup",
            200
        )
        
        if success2:
            print(f"✅ Bulk cleanup completed")
            print(f"   Memory freed: {cleanup_response.get('memory_freed', 0)} MB")
            print(f"   Screenshots deleted: {cleanup_response.get('deleted_from_db', 0)}")
            
            # Verify all screenshots were deleted
            success3, memory_after = self.run_test(
                "Memory Usage After Bulk Cleanup",
                "GET",
                "memory/usage",
                200
            )
            
            if success3:
                print(f"   Memory after bulk cleanup: {memory_after.get('total_size_mb', 0)} MB")
                print(f"   Screenshots after cleanup: {memory_after.get('screenshots', 0)}")
                
                if memory_after.get('screenshots', 0) == 0:
                    print("✅ All screenshots successfully deleted")
                else:
                    print("❌ Some screenshots may not have been deleted")
                    return False
        
        return success1 and success2

    def test_memory_stress(self):
        """Test memory handling with larger images"""
        print("\n🧠 Testing Memory Efficiency with Large Images...")
        
        # Test with a larger image
        img_bytes, original_width, original_height = self.create_test_image(2000, 1500)
        
        success, response = self.run_test(
            "Large Image Upload",
            "POST",
            "screenshots/upload",
            200,
            files={'file': ('large_test.png', img_bytes, 'image/png')}
        )
        
        if success:
            print(f"   Large image processed successfully")
            print(f"   Original: {original_width}x{original_height}")
            print(f"   Display: {response['display_size']['width']}x{response['display_size']['height']}")
            
            # Verify 90% calculation for large image
            expected_width = int(original_width * 0.9)
            expected_height = int(original_height * 0.9)
            
            if (response['display_size']['width'] == expected_width and 
                response['display_size']['height'] == expected_height):
                print("✅ Large image 90% resizing correct")
            else:
                print("❌ Large image 90% resizing incorrect")
        
        return success

    def cleanup_test_data(self):
        """Clean up test screenshots"""
        if self.screenshot_id:
            print(f"\n🧹 Cleaning up test screenshot: {self.screenshot_id}")
            success, _ = self.run_test(
                "Delete Screenshot",
                "DELETE",
                f"screenshots/{self.screenshot_id}",
                200
            )
            return success
        return True

def main():
    print("🚀 Starting Screenshot Annotation API Tests")
    print("=" * 60)
    
    tester = ScreenshotAPITester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_file_upload,
        tester.test_base64_upload,
        tester.test_get_screenshots,
        tester.test_get_screenshot_by_id,
        tester.test_get_screenshot_files,
        tester.test_annotation_crud,
        tester.test_memory_stress,
        tester.cleanup_test_data
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check backend implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())