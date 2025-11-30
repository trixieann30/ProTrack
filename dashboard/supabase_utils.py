"""Supabase Storage Utilities for ProTrack

Handles file uploads to Supabase Storage buckets: profilepic and Uploadfiles
"""

import os
import requests
from typing import Optional, Tuple
import mimetypes
from decouple import config
import time


class SupabaseStorage:
    """Handle file operations with Supabase Storage"""
    
    def __init__(self):
        # Load from environment variables using decouple
        self.supabase_url = config('SUPABASE_URL', default='').strip().rstrip('/')
        self.supabase_key = config('SUPABASE_KEY', default='').strip()
        
        if self.supabase_url and self.supabase_key:
            print(f"✓ Supabase configured: {self.supabase_url[:30]}...")
        else:
            print("✗ Supabase credentials missing!")
            
        self.storage_url = f"{self.supabase_url}/storage/v1"
    
    def _get_headers(self):
        """Get authorization headers for Supabase API"""
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'apikey': self.supabase_key
        }
    
    def delete_file(self, bucket_name: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from Supabase Storage
        
        Args:
            bucket_name: Name of the bucket
            file_path: Path within the bucket
            
        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        if not self.supabase_url or not self.supabase_key:
            return False, 'Supabase credentials not configured'
        
        try:
            delete_url = f"{self.storage_url}/object/{bucket_name}/{file_path}"
            
            response = requests.delete(
                delete_url,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                print(f"✓ File deleted: {file_path}")
                return True, None
            else:
                try:
                    error_msg = response.json().get('message', 'Delete failed')
                except:
                    error_msg = f'Delete failed with status {response.status_code}'
                
                print(f"✗ Delete failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Exception during delete: {error_msg}")
            return False, error_msg
    
    def upload_file(self, file, bucket_name: str, file_path: str, upsert: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to Supabase Storage
        
        Args:
            file: Django UploadedFile object
            bucket_name: Name of the bucket ('profilepic' or 'Uploadfiles')
            file_path: Path within the bucket (e.g., 'user_123/profile.jpg')
            upsert: If True, will overwrite existing file
            
        Returns:
            Tuple of (success: bool, url: str, error: Optional[str])
        """
        if not self.supabase_url or not self.supabase_key:
            return False, '', 'Supabase credentials not configured'
        
        try:
            # Get content type
            content_type = file.content_type or mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            
            # Upload URL with upsert parameter if needed
            upload_url = f"{self.storage_url}/object/{bucket_name}/{file_path}"
            if upsert:
                upload_url += "?upsert=true"
            
            # Prepare headers
            headers = self._get_headers()
            headers['Content-Type'] = content_type
            
            # Read file data
            file.seek(0)  # Reset file pointer to start
            file_data = file.read()
            
            print(f"📤 Uploading to: {upload_url}")
            print(f"📦 File size: {len(file_data)} bytes")
            print(f"📦 Content-Type: {content_type}")
            print(f"🔄 Upsert mode: {upsert}")
            
            # Upload file
            response = requests.post(
                upload_url,
                headers=headers,
                data=file_data,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                # Get public URL
                public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
                print(f"✓ Upload successful: {public_url}")
                return True, public_url, None
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('error', 'Upload failed'))
                except:
                    error_msg = f'Upload failed with status {response.status_code}: {response.text[:200]}'
                
                print(f"✗ Upload failed: {error_msg}")
                return False, '', error_msg
                
        except requests.exceptions.Timeout:
            error_msg = 'Upload timeout - please try again'
            print(f"✗ {error_msg}")
            return False, '', error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Exception during upload: {error_msg}")
            return False, '', error_msg
    
    def get_public_url(self, bucket_name: str, file_path: str) -> str:
        """
        Get public URL for a file
        
        Args:
            bucket_name: Name of the bucket
            file_path: Path within the bucket
            
        Returns:
            Public URL string
        """
        return f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
    
    def list_files(self, bucket_name: str, folder_path: str = '') -> Tuple[bool, list, Optional[str]]:
        """
        List files in a bucket folder
        
        Args:
            bucket_name: Name of the bucket
            folder_path: Optional folder path within bucket
            
        Returns:
            Tuple of (success: bool, files: list, error: Optional[str])
        """
        if not self.supabase_url or not self.supabase_key:
            return False, [], 'Supabase credentials not configured'
        
        try:
            list_url = f"{self.storage_url}/object/list/{bucket_name}"
            if folder_path:
                list_url += f"?prefix={folder_path}"
            
            response = requests.get(
                list_url,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                files = response.json()
                return True, files, None
            else:
                try:
                    error_msg = response.json().get('message', 'List failed')
                except:
                    error_msg = f'List failed with status {response.status_code}'
                
                return False, [], error_msg
                
        except Exception as e:
            return False, [], str(e)


# Helper functions for specific use cases

def upload_profile_picture(user_id: int, file) -> Tuple[bool, str, Optional[str]]:
    """
    Upload a profile picture to the profilepic bucket
    
    Args:
        user_id: User ID
        file: Django UploadedFile object
        
    Returns:
        Tuple of (success: bool, url: str, error: Optional[str])
    """
    storage = SupabaseStorage()
    
    # Get file extension
    file_extension = os.path.splitext(file.name)[1].lower()
    
    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if file_extension not in allowed_extensions:
        return False, '', f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
    
    # Create file path with timestamp to make it unique
    timestamp = int(time.time())
    file_path = f"user_{user_id}/profile_{timestamp}{file_extension}"
    
    print(f"🚀 Uploading profile picture for user {user_id}")
    
    # Try to delete old profile pictures for this user (cleanup)
    # This is optional but helps manage storage
    try:
        old_files_success, old_files, _ = storage.list_files('profilepic', f'user_{user_id}/')
        if old_files_success and old_files:
            for old_file in old_files:
                old_path = old_file.get('name')
                if old_path and old_path != file_path:
                    storage.delete_file('profilepic', old_path)
                    print(f"🗑️ Deleted old profile picture: {old_path}")
    except Exception as e:
        print(f"⚠️ Could not cleanup old files: {e}")
    
    # Upload with upsert=True to overwrite if needed
    return storage.upload_file(file, 'profilepic', file_path, upsert=True)


def upload_training_material(course_id: int, file) -> Tuple[bool, str, Optional[str]]:
    """
    Upload a training material to the Uploadfiles bucket
    
    Args:
        course_id: Course ID
        file: Django UploadedFile object
        
    Returns:
        Tuple of (success: bool, url: str, error: Optional[str])
    """
    storage = SupabaseStorage()
    
    # Keep original filename but make it safe
    safe_filename = file.name.replace(' ', '_').replace('(', '').replace(')', '')
    
    file_path = f"course_{course_id}/{safe_filename}"
    
    print(f"🚀 Uploading training material for course {course_id}")
    
    return storage.upload_file(file, 'Uploadfiles', file_path)


def delete_training_material(file_url: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a training material from Supabase
    
    Args:
        file_url: Full URL of the file
        
    Returns:
        Tuple of (success: bool, error: Optional[str])
    """
    storage = SupabaseStorage()
    
    # Extract bucket and path from URL
    # URL format: https://xxx.supabase.co/storage/v1/object/public/Uploadfiles/course_1/file.pdf
    try:
        parts = file_url.split('/storage/v1/object/public/')
        if len(parts) == 2:
            bucket_and_path = parts[1].split('/', 1)
            if len(bucket_and_path) == 2:
                bucket_name, file_path = bucket_and_path
                return storage.delete_file(bucket_name, file_path)
    except Exception as e:
        return False, str(e)
    
    return False, 'Invalid file URL format'


def upload_certificate(enrollment_id: int, pdf_file) -> Tuple[bool, str, Optional[str]]:
    """
    Upload a certificate PDF to the Uploadfiles bucket
    
    Args:
        enrollment_id: Enrollment ID
        pdf_file: Django UploadedFile object or file-like object
        
    Returns:
        Tuple of (success: bool, url: str, error: Optional[str])
    """
    storage = SupabaseStorage()
    
    file_path = f"certificates/enrollment_{enrollment_id}.pdf"
    
    print(f"🚀 Uploading certificate for enrollment {enrollment_id}")
    
    return storage.upload_file(pdf_file, 'Uploadfiles', file_path)