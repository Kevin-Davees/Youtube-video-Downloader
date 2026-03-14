import os
import sys
import time

# Function to check and install yt-dlp
def setup():
    """Check if yt-dlp is installed, install if not"""
    try:
        import yt_dlp
        return True
    except ImportError:
        print("Installing yt-dlp...")
        os.system(f"{sys.executable} -m pip install yt_dlp")
        return True

def download_video(url, save_path, download_count, total_count):
    """Download a single video"""
    import yt_dlp
    
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'quiet': False,
        'no_warnings': True,
        'progress_hooks': [lambda d: print_progress(d, download_count, total_count)],
    }
    
    try:
        print(f"\n⬇️ Downloading video {download_count}/{total_count}")
        print(f"   URL: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        print(f"✅ Download {download_count}/{total_count} complete!")
        return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

def print_progress(d, download_count, total_count):
    """Print download progress"""
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        percent = d.get('_percent_str', '?')
        speed = d.get('_speed_str', '?')
        
        if total > 0:
            print(f"   [{download_count}/{total_count}] {percent} - {speed}", end='\r')
    elif d['status'] == 'finished':
        print(f"   [{download_count}/{total_count}] Processing...")

def main():
    """Main download function"""
    if not setup():
        return
    
    print("Simple YouTube Downloader - Multiple URLs")
    print("-" * 40)
    print("Paste multiple URLs (one per line)")
    print("Press Enter twice when done, or Ctrl+Z (Windows) / Ctrl+D (Unix) to finish")
    print("-" * 40)
    
    # Get multiple URLs
    urls = []
    print("\nEnter URLs (one per line):")
    
    try:
        while True:
            line = input()
            if line == "":
                # Check if two consecutive empty lines
                if len(urls) > 0 and urls[-1] == "":
                    urls.pop()
                    break
            urls.append(line)
    except EOFError:
        pass
    
    # Filter out empty strings and strip whitespace
    urls = [url.strip() for url in urls if url.strip()]
    
    if not urls:
        print("❌ No URLs provided!")
        return
    
    print(f"\n📋 Found {len(urls)} URL(s):")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    # Set download path
    save_path = r"C:\Users\peter\Downloads"
    print(f"\n💾 Save location: {save_path}")
    custom_path = input(f"Press Enter to use above, or type new path: ").strip()
    if custom_path:
        save_path = custom_path
    
    # Create folder if needed
    os.makedirs(save_path, exist_ok=True)
    
    # Ask for format preference
    print("\n📹 Choose format:")
    print("  1. Best quality (up to 1080p) [Default]")
    print("  2. Audio only (MP3)")
    print("  3. Video only (no audio)")
    print("  4. Specific resolution (e.g., 720p)")
    
    format_choice = input("Choice [1]: ").strip()
    
    # Format options based on choice
    format_options = {
        '1': 'bestvideo[height<=1080]+bestaudio/best',
        '2': 'bestaudio/best',
        '3': 'bestvideo[height<=1080]/best',
        '4': 'bestvideo[height<=720]+bestaudio/best'
    }
    
    if format_choice == '4':
        resolution = input("Enter max resolution (e.g., 720, 480, 360): ").strip()
        if resolution.isdigit():
            format_options['4'] = f'bestvideo[height<={resolution}]+bestaudio/best'
    
    selected_format = format_options.get(format_choice, format_options['1'])
    
    # Confirm download
    print(f"\n⚠️  Starting download of {len(urls)} video(s)...")
    print(f"   Save to: {save_path}")
    print(f"   Format: {selected_format}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Download cancelled.")
        return
    
    # Download each video
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, url in enumerate(urls, 1):
        result = download_video(url, save_path, i, len(urls))
        if result:
            successful += 1
        else:
            failed += 1
        
        # Small delay between downloads
        if i < len(urls):
            time.sleep(1)
    
    # Summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*40}")
    print("📊 Download Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"   💾 Saved to: {save_path}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()