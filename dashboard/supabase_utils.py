"""
Supabase Storage Utilities for ProTrack
Handles file uploads to Supabase Storage buckets: profilepic and Uploadfiles
"""

import os
import requests
from django.conf import settings
from typing import Optional, Tuple
import mimetypes


class SupabaseStorage:
    """Handle file operations with Supabase Storage"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_KEY', '')
        self.storage_url = f"{self.supabase_url}/storage/v1"
        
    def _get_headers(self):
        """Get authorization headers for Supabase API"""
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'apikey': self.supabase_key
        }
    
    def upload_file(self, file, bucket_name: str, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to Supabase Storage
        
        Args:
            file: Django UploadedFile object
            bucket_name: Name of the bucket ('profilepic' or 'Uploadfiles')
            file_path: Path within the bucket (e.g., 'user_123/profile.jpg')
        
        Returns:
            Tuple of (success: bool, url: str, error: Optional[str])
        """
        if not self.supabase_url or not self.supabase_key:
            return False, '', 'Supabase credentials not configured'
        
        try:
            # Get content type
            content_type = file.content_type or mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            
            # Upload URL
            upload_url = f"{self.storage_url}/object/{bucket_name}/{file_path}"
            
            # Prepare headers
            headers = self._get_headers()
            headers['Content-Type'] = content_type
            
            # Upload file
            response = requests.post(
                upload_url,
                headers=headers,
                data=file.read()
            )
            
            if response.status_code in [200, 201]:
                # Get public URL
                public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
                return True, public_url, None
            else:
                error_msg = response.json().get('message', 'Upload failed')
                return False, '', error_msg
                
        except Exception as e:
            return False, '', str(e)
    
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
                headers=self._get_headers()
            )
            
            if response.status_code in [200, 204]:
                return True, None
            else:
                error_msg = response.json().get('message', 'Delete failed')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
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
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                files = response.json()
                return True, files, None
            else:
                error_msg = response.json().get('message', 'List failed')
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
    file_extension = os.path.splitext(file.name)[1]
    file_path = f"user_{user_id}/profile{file_extension}"
    return storage.upload_file(file, 'profilepic', file_path)


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
    safe_filename = file.name.replace(' ', '_')
    file_path = f"course_{course_id}/{safe_filename}"
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
    return storage.upload_file(pdf_file, 'Uploadfiles', file_path)
