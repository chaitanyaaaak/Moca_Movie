import os
import time
import requests
import socket
import streamlit as st
from tqdm import tqdm
from pathlib import Path

# Function to check Wi-Fi connection
def is_connected():
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        return True
    except (socket.timeout, socket.gaierror, OSError):
        return False

# Function to download with resume and headers
def download_file_with_resume(url, output):
    try:
        # Check if file already partially downloaded
        downloaded_size = os.path.getsize(output) if os.path.exists(output) else 0

        # Add headers to bypass 403 error
        headers = {
            "Range": f"bytes={downloaded_size}-",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://google.com",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }

        # Send GET request with resume headers
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code not in [200, 206]:
            raise Exception(f"Failed to download: HTTP {response.status_code}")

        # Determine total file size
        content_range = response.headers.get('Content-Range')
        if content_range:
            total_size = int(content_range.split('/')[-1])
        else:
            total_size = int(response.headers.get('Content-Length', 0)) + downloaded_size

        st.info(f"Total size: {total_size / (1024 * 1024):.2f} MB")
        st.info(f"Resuming from: {downloaded_size / (1024 * 1024):.2f} MB")

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Write file with progress
        with open(output, "ab") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress = downloaded_size / total_size
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(f"Downloaded: {downloaded_size / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB ({progress * 100:.1f}%)")
        
        progress_bar.empty()
        status_text.empty()
        return True

    except Exception as e:
        st.error(f"❌ Download error: {e}")
        return False

def main():
    st.title("File Downloader")
    st.write("Download files with resume capability and automatic reconnection")
    
    # Input fields
    url = st.text_input("Download URL", placeholder="https://example.com/file.zip")
    filename = st.text_input("Save as filename", placeholder="file.zip")
    
    # Save location
    save_location = st.text_input("Save location", value=str(Path.home() / "Downloads"))
    browse_button = st.button("Browse")
    
    if browse_button:
        # Note: Streamlit doesn't have a native file dialog, so we'll just suggest common locations
        common_locations = [
            str(Path.home() / "Downloads"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Desktop"),
            os.getcwd()
        ]
        selected = st.selectbox("Select save location", common_locations)
        save_location = selected
    
    # Start download button
    if st.button("Start Download"):
        if not url or not filename:
            st.error("Please enter both URL and filename")
            return
        
        full_path = os.path.join(save_location, filename)
        
        # Create directory if it doesn't exist
        os.makedirs(save_location, exist_ok=True)
        
        st.info(f"Downloading to: {full_path}")
        
        with st.spinner("Checking connection..."):
            while True:
                if is_connected():
                    st.success("✅ Wi-Fi connected. Starting/resuming download...")
                    success = download_file_with_resume(url, full_path)
                    if success:
                        st.success("✅ Download completed!")
                        st.balloons()
                    else:
                        st.error("Download failed")
                    break
                else:
                    st.warning("⚠️ No Wi-Fi. Waiting to reconnect...")
                    time.sleep(10)

if __name__ == "__main__":
    main()