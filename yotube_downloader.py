import os
import sys

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

def main():
    """Main download function"""
    if not setup():
        return
    
    import yt_dlp
    
    print("Simple YouTube Downloader")
    print("-" * 30)
    
    # Get URL
    url = input("\nVideo URL: ").strip()
    if not url:
        print("❌ No URL provided!")
        return
    
    # Set download path
    save_path = r"C:\Users\peter\Downloads"
    custom_path = input(f"\nSave to [{save_path}]: ").strip()
    if custom_path:
        save_path = custom_path
    
    # Create folder if needed
    os.makedirs(save_path, exist_ok=True)
    
    # Download options
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'quiet': False,
        'no_warnings': True,
    }
    
    # Download
    try:
        print("\n⬇️ Downloading...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()