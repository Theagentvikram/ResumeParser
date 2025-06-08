import os
import shutil
from pathlib import Path
import uuid
from typing import Optional
import json

# For Supabase integration (if enabled)
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_ENABLED = SUPABASE_URL and SUPABASE_KEY
except ImportError:
    SUPABASE_ENABLED = False

# Create local storage directory
LOCAL_STORAGE_DIR = Path("./storage")
LOCAL_STORAGE_DIR.mkdir(exist_ok=True)

def upload_to_storage(source_path: str, destination_path: str) -> str:
    """
    Upload a file to storage (local or Supabase)
    
    Args:
        source_path: Path to the source file
        destination_path: Path where the file should be stored
        
    Returns:
        Path to the stored file
    """
    try:
        if SUPABASE_ENABLED:
            return upload_to_supabase(source_path, destination_path)
        else:
            return upload_to_local_storage(source_path, destination_path)
    except Exception as e:
        print(f"Error uploading to storage: {str(e)}")
        # Fall back to local storage
        return upload_to_local_storage(source_path, destination_path)

def upload_to_local_storage(source_path: str, destination_path: str) -> str:
    """
    Upload a file to local storage
    
    Args:
        source_path: Path to the source file
        destination_path: Path where the file should be stored
        
    Returns:
        Path to the stored file
    """
    # Create directory if not exists
    dest_dir = LOCAL_STORAGE_DIR / Path(destination_path).parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    dest_file = LOCAL_STORAGE_DIR / destination_path
    shutil.copy2(source_path, dest_file)
    
    return str(destination_path)

def upload_to_supabase(source_path: str, destination_path: str) -> str:
    """
    Upload a file to Supabase Storage
    
    Args:
        source_path: Path to the source file
        destination_path: Path where the file should be stored
        
    Returns:
        Path to the stored file
    """
    if not SUPABASE_ENABLED:
        raise ValueError("Supabase is not configured")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Read file content
    with open(source_path, "rb") as f:
        file_content = f.read()
    
    # Extract bucket and path
    parts = destination_path.split("/", 1)
    bucket = parts[0]
    file_path = parts[1] if len(parts) > 1 else f"{uuid.uuid4()}.pdf"
    
    # Upload to Supabase
    response = supabase.storage.from_(bucket).upload(file_path, file_content)
    
    return f"{bucket}/{file_path}"

def get_download_url(file_path: str) -> str:
    """
    Get download URL for a file
    
    Args:
        file_path: Path to the file in storage
        
    Returns:
        Download URL
    """
    try:
        if SUPABASE_ENABLED:
            return get_supabase_download_url(file_path)
        else:
            return get_local_download_url(file_path)
    except Exception as e:
        print(f"Error getting download URL: {str(e)}")
        # Fall back to local URL
        return get_local_download_url(file_path)

def get_local_download_url(file_path: str) -> str:
    """
    Get download URL for a file in local storage
    
    Args:
        file_path: Path to the file in storage
        
    Returns:
        Download URL
    """
    # In a real deployment, this would be a proper URL
    # For local development, we just return a relative path
    return f"/download/{file_path}"

def get_supabase_download_url(file_path: str) -> str:
    """
    Get download URL for a file in Supabase Storage
    
    Args:
        file_path: Path to the file in storage
        
    Returns:
        Download URL
    """
    if not SUPABASE_ENABLED:
        raise ValueError("Supabase is not configured")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Extract bucket and path
    parts = file_path.split("/", 1)
    bucket = parts[0]
    file_path = parts[1] if len(parts) > 1 else file_path
    
    # Get public URL
    public_url = supabase.storage.from_(bucket).get_public_url(file_path)
    
    return public_url 