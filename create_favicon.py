#!/usr/bin/env python3
"""
Script to create favicon files from the OCS logo
"""

try:
    from PIL import Image, ImageDraw
    import os
    
    def create_favicon_files():
        # Path to the original logo
        logo_path = "ocs-portal-py/static/ocs-logo.png"
        static_dir = "ocs-portal-py/static"
        
        if not os.path.exists(logo_path):
            print(f"Logo file not found: {logo_path}")
            return
        
        # Open the original logo
        try:
            original = Image.open(logo_path)
            print(f"Original image size: {original.size}")
            
            # Convert to RGBA if not already
            if original.mode != 'RGBA':
                original = original.convert('RGBA')
            
            # Create different sizes for favicon
            sizes = [
                (16, 16, "favicon-16x16.png"),
                (32, 32, "favicon-32x32.png"),
                (180, 180, "apple-touch-icon.png"),
            ]
            
            for width, height, filename in sizes:
                # Resize the image
                resized = original.resize((width, height), Image.Resampling.LANCZOS)
                output_path = os.path.join(static_dir, filename)
                resized.save(output_path, "PNG")
                print(f"Created: {output_path}")
            
            # Create ICO file (16x16 and 32x32 combined)
            ico_path = os.path.join(static_dir, "favicon.ico")
            icon_sizes = [(16, 16), (32, 32)]
            icon_images = []
            
            for size in icon_sizes:
                resized = original.resize(size, Image.Resampling.LANCZOS)
                icon_images.append(resized)
            
            # Save as ICO
            icon_images[0].save(ico_path, format='ICO', sizes=[(16, 16), (32, 32)])
            print(f"Created: {ico_path}")
            
            print("All favicon files created successfully!")
            
        except Exception as e:
            print(f"Error processing image: {e}")
    
    if __name__ == "__main__":
        create_favicon_files()

except ImportError:
    print("PIL (Pillow) not available, installing...")
    import subprocess
    import sys
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("Pillow installed successfully. Please run the script again.")
    except Exception as e:
        print(f"Failed to install Pillow: {e}")
        print("Please install Pillow manually: pip install Pillow")
