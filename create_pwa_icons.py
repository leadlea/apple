#!/usr/bin/env python3
"""
Script to create PWA icons for Mac Status PWA
Creates simple placeholder icons with the Mac Status logo
"""

import os
from PIL import Image, ImageDraw, ImageFont
import math

def create_icon(size, output_path, is_maskable=False):
    """Create a PWA icon with the specified size"""
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Apple blue color
    apple_blue = (0, 122, 255, 255)
    white = (255, 255, 255, 255)
    
    # Calculate dimensions
    if is_maskable:
        # For maskable icons, use safe area (80% of total size)
        safe_area = int(size * 0.8)
        offset = (size - safe_area) // 2
        icon_size = safe_area
    else:
        icon_size = size
        offset = 0
    
    # Draw background circle
    circle_radius = icon_size // 2 - 4
    circle_center = (offset + icon_size // 2, offset + icon_size // 2)
    
    # Draw main circle background
    draw.ellipse([
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ], fill=apple_blue)
    
    # Draw computer monitor icon
    monitor_width = int(icon_size * 0.4)
    monitor_height = int(icon_size * 0.25)
    monitor_x = circle_center[0] - monitor_width // 2
    monitor_y = circle_center[1] - monitor_height // 2 - int(icon_size * 0.05)
    
    # Monitor screen
    draw.rectangle([
        monitor_x,
        monitor_y,
        monitor_x + monitor_width,
        monitor_y + monitor_height
    ], fill=white, outline=white, width=2)
    
    # Monitor stand
    stand_width = int(monitor_width * 0.3)
    stand_height = int(icon_size * 0.08)
    stand_x = circle_center[0] - stand_width // 2
    stand_y = monitor_y + monitor_height
    
    draw.rectangle([
        stand_x,
        stand_y,
        stand_x + stand_width,
        stand_y + stand_height
    ], fill=white)
    
    # Monitor base
    base_width = int(monitor_width * 0.6)
    base_height = int(icon_size * 0.04)
    base_x = circle_center[0] - base_width // 2
    base_y = stand_y + stand_height
    
    draw.rectangle([
        base_x,
        base_y,
        base_x + base_width,
        base_y + base_height
    ], fill=white)
    
    # Add status bars on screen
    bar_width = int(monitor_width * 0.6)
    bar_height = 2
    bar_x = monitor_x + (monitor_width - bar_width) // 2
    
    # CPU bar
    cpu_y = monitor_y + int(monitor_height * 0.3)
    draw.rectangle([bar_x, cpu_y, bar_x + int(bar_width * 0.7), cpu_y + bar_height], fill=apple_blue)
    
    # Memory bar
    mem_y = cpu_y + 6
    draw.rectangle([bar_x, mem_y, bar_x + int(bar_width * 0.5), mem_y + bar_height], fill=apple_blue)
    
    # Disk bar
    disk_y = mem_y + 6
    draw.rectangle([bar_x, disk_y, bar_x + int(bar_width * 0.3), disk_y + bar_height], fill=apple_blue)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path} ({size}x{size})")

def create_shortcut_icon(size, output_path, icon_type):
    """Create shortcut icons"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    apple_blue = (0, 122, 255, 255)
    white = (255, 255, 255, 255)
    
    # Draw background
    draw.ellipse([4, 4, size-4, size-4], fill=apple_blue)
    
    center = size // 2
    
    if icon_type == 'status':
        # Draw chart/status icon
        bar_width = 4
        bar_spacing = 6
        bars = [
            (center - bar_spacing, center + 8, 12),  # Short bar
            (center, center + 4, 16),                # Medium bar
            (center + bar_spacing, center - 2, 20)   # Tall bar
        ]
        
        for x, y_bottom, height in bars:
            draw.rectangle([
                x - bar_width//2,
                y_bottom - height,
                x + bar_width//2,
                y_bottom
            ], fill=white)
    
    elif icon_type == 'chat':
        # Draw chat bubble icon
        bubble_size = size // 3
        bubble_x = center - bubble_size // 2
        bubble_y = center - bubble_size // 2 - 2
        
        # Main bubble
        draw.ellipse([
            bubble_x,
            bubble_y,
            bubble_x + bubble_size,
            bubble_y + bubble_size
        ], fill=white)
        
        # Bubble tail
        tail_points = [
            (bubble_x + bubble_size // 3, bubble_y + bubble_size),
            (bubble_x + bubble_size // 4, bubble_y + bubble_size + 6),
            (bubble_x + bubble_size // 2, bubble_y + bubble_size)
        ]
        draw.polygon(tail_points, fill=white)
    
    img.save(output_path, 'PNG')
    print(f"Created shortcut icon: {output_path} ({size}x{size})")

def main():
    """Main function to create all PWA icons"""
    
    # Create icons directory
    icons_dir = 'frontend/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Standard icon sizes
    icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Create standard icons
    for size in icon_sizes:
        create_icon(size, f'{icons_dir}/icon-{size}x{size}.png')
    
    # Create maskable icons
    maskable_sizes = [192, 512]
    for size in maskable_sizes:
        create_icon(size, f'{icons_dir}/icon-maskable-{size}x{size}.png', is_maskable=True)
    
    # Create shortcut icons
    create_shortcut_icon(96, f'{icons_dir}/shortcut-status.png', 'status')
    create_shortcut_icon(96, f'{icons_dir}/shortcut-chat.png', 'chat')
    
    print("\nAll PWA icons created successfully!")
    print(f"Icons saved in: {icons_dir}/")

if __name__ == '__main__':
    main()