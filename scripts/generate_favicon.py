#!/usr/bin/env python3
"""
Generate favicon.ico from lock icon
Creates a favicon with a lock icon for the Identity Manager application
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_lock_icon(size=32, bg_color=(52, 73, 94), lock_color=(255, 255, 255)):
    """Create a lock icon as an image"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate dimensions
    padding = size // 8
    lock_width = size - (padding * 2)
    lock_height = lock_width * 0.8
    
    # Draw lock body (rectangle with rounded top)
    x1, y1 = padding, padding + lock_height * 0.3
    x2, y2 = padding + lock_width, padding + lock_height
    
    # Draw the lock body
    draw.rectangle([x1, y1, x2, y2], fill=lock_color, outline=lock_color)
    
    # Draw the lock shackle (semi-circle on top)
    shackle_width = lock_width * 0.6
    shackle_height = lock_height * 0.4
    shackle_x = padding + (lock_width - shackle_width) / 2
    shackle_y = padding
    
    # Draw shackle as a rectangle with rounded top
    draw.rectangle([shackle_x, shackle_y + shackle_height * 0.5, 
                   shackle_x + shackle_width, shackle_y + shackle_height], 
                  fill=lock_color, outline=lock_color)
    
    # Draw the keyhole
    keyhole_x = padding + lock_width * 0.5
    keyhole_y = padding + lock_height * 0.6
    keyhole_size = lock_width * 0.15
    
    # Draw keyhole circle
    draw.ellipse([keyhole_x - keyhole_size, keyhole_y - keyhole_size,
                  keyhole_x + keyhole_size, keyhole_y + keyhole_size], 
                 fill=bg_color, outline=bg_color)
    
    # Draw keyhole rectangle
    rect_width = keyhole_size * 0.3
    rect_height = keyhole_size * 0.8
    draw.rectangle([keyhole_x - rect_width, keyhole_y,
                   keyhole_x + rect_width, keyhole_y + rect_height], 
                  fill=bg_color, outline=bg_color)
    
    return img

def create_favicon():
    """Create favicon.ico with multiple sizes"""
    # Create images for different favicon sizes
    sizes = [16, 32, 48]
    images = []
    
    for size in sizes:
        img = create_lock_icon(size)
        images.append(img)
    
    # Save as ICO file
    favicon_path = os.path.join('app', 'static', 'favicon.ico')
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(favicon_path), exist_ok=True)
    
    # Save the first image as ICO (PIL will handle multiple sizes)
    images[0].save(favicon_path, format='ICO', sizes=[(size, size) for size in sizes])
    
    print(f"Favicon created at: {favicon_path}")
    print(f"Generated sizes: {sizes}")

if __name__ == "__main__":
    create_favicon() 