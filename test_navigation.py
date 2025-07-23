#!/usr/bin/env python3
"""
Test script for the Bunny CDN directory navigation
"""
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.bunny_client import list_files

async def test_navigation():
    print("Testing Bunny CDN navigation...")
    
    try:
        # Test root directory
        print("\n=== Root Directory ===")
        root_files = await list_files("")
        print(f"Current path: '{root_files['current_path']}'")
        print(f"Parent path: '{root_files['parent_path']}'")
        print(f"Directories: {len(root_files['directories'])}")
        print(f"Video files: {len(root_files['files'])}")
        
        # List some directories
        for i, directory in enumerate(root_files['directories'][:3]):  # Show first 3
            print(f"  Dir {i+1}: {directory['name']} -> {directory['path']}")
        
        # List some files
        for i, file in enumerate(root_files['files'][:3]):  # Show first 3
            print(f"  File {i+1}: {file['name']} ({file['size']} bytes)")
        
        # Test navigating into first directory if available
        if root_files['directories']:
            first_dir = root_files['directories'][0]
            print(f"\n=== Navigating to: {first_dir['name']} ===")
            
            sub_files = await list_files(first_dir['path'])
            print(f"Current path: '{sub_files['current_path']}'")
            print(f"Parent path: '{sub_files['parent_path']}'")
            print(f"Directories: {len(sub_files['directories'])}")
            print(f"Video files: {len(sub_files['files'])}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your .env file is configured with valid Bunny CDN credentials.")

if __name__ == "__main__":
    asyncio.run(test_navigation())
