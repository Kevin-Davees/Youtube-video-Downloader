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
    """Main download function with playlist support"""
    if not setup():
        return
    
    import yt_dlp
    
    print("YouTube Downloader (Single Videos & Playlists)")
    print("-" * 40)
    
    # Get URL
    url = input("\n📺 Enter YouTube URL (video or playlist): ").strip()
    if not url:
        print("❌ No URL provided!")
        return
    
    # Check if it's a playlist
    is_playlist = "playlist" in url.lower() or "list=" in url.lower()
    
    if is_playlist:
        print("🔗 Playlist detected!")
        
        # Ask how many videos to download
        print("\nPlaylist options:")
        print("1. Download entire playlist")
        print("2. Download first N videos")
        print("3. Download specific range")
        
        choice = input("\nChoose option (1-3) [1]: ").strip() or "1"
        
        if choice == "2":
            max_videos = input("How many videos to download?: ").strip()
            if max_videos.isdigit():
                playlist_items = f"1-{max_videos}"
            else:
                playlist_items = None
        elif choice == "3":
            playlist_items = input("Enter range (e.g., 1-10, 2,5,8): ").strip()
        else:
            playlist_items = None
    
    # Get resolution choice
    print("\n📊 Available resolutions:")
    print("1. 480p (SD)")
    print("2. 720p (HD)")
    print("3. 1080p (Full HD) ← DEFAULT")
    print("4. 1440p (2K)")
    print("5. 2160p (4K)")
    print("6. Best available")
    
    choice = input("\n🎯 Choose resolution (1-6, default 3): ").strip()
    
    # Map choice to resolution
    resolutions = {
        '1': '480',
        '2': '720', 
        '3': '1080',
        '4': '1440',
        '5': '2160',
        '6': 'best'
    }
    
    selected = resolutions.get(choice, '1080')  # Default to 1080p
    
    if selected == 'best':
        format_str = 'bestvideo+bestaudio/best'
    else:
        format_str = f'bestvideo[height<={selected}]+bestaudio/best'
    
    # Set download path
    save_path = r"C:\Users\peter\Downloads"
    
    if is_playlist:
        playlist_name = input(f"\n📁 Playlist folder name (optional): ").strip()
        if playlist_name:
            save_path = os.path.join(save_path, playlist_name)
    
    custom_path = input(f"\n💾 Save to [{save_path}]: ").strip()
    if custom_path:
        save_path = custom_path
    
    # Create folder if needed
    os.makedirs(save_path, exist_ok=True)
    
    # Download options
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(playlist_title)s' if is_playlist else '', 
                               '%(playlist_index)s - ' if is_playlist else '', 
                               '%(title)s.%(ext)s'),
        'format': format_str,
        'quiet': False,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
    }
    
    # Add playlist options if it's a playlist
    if is_playlist:
        ydl_opts.update({
            'yes_playlist': True,  # Always treat as playlist
            'extract_flat': False,  # Download all videos
            'playlistreverse': False,  # Don't reverse order
            'playlistrandom': False,  # Don't randomize
            'lazy_playlist': False,  # Process entire playlist
        })
        
        if 'playlist_items' in locals() and playlist_items:
            ydl_opts['playlist_items'] = playlist_items
    
    # Show what will be downloaded
    resolution_names = {
        '480': '480p (SD)',
        '720': '720p (HD)',
        '1080': '1080p (Full HD)',
        '1440': '1440p (2K)',
        '2160': '2160p (4K)',
        'best': 'Best available quality'
    }
    
    print(f"\n📥 Download settings:")
    print(f"   Type: {'🎵 PLAYLIST' if is_playlist else '🎬 SINGLE VIDEO'}")
    print(f"   Quality: {resolution_names.get(selected, selected)}")
    print(f"   Location: {save_path}")
    
    if is_playlist and 'playlist_items' in locals() and playlist_items:
        print(f"   Items: {playlist_items}")
    
    # Download
    try:
        print(f"\n{'='*50}")
        print(f"⬇️  Downloading {'playlist' if is_playlist else 'video'}...")
        print(f"{'='*50}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        print(f"\n✅ {'Playlist' if is_playlist else 'Video'} download complete!")
        print(f"📁 Saved to: {save_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def progress_hook(d):
    """Show download progress"""
    if d['status'] == 'downloading':
        filename = os.path.basename(d['filename']) if 'filename' in d else 'Unknown'
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        
        # Truncate long filenames
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        print(f"\r📥 {filename} | {percent} | {speed} | ETA: {eta}", end='', flush=True)
    
    elif d['status'] == 'finished':
        print(f"\r✅ Download finished! Processing...")

if __name__ == "__main__":
    main()