#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

def create_welcome_back_image():
    """Create a welcome back icon for returning players"""
    # Create a new image with a transparent background
    size = (240, 240)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a circular background
    circle_color = (30, 64, 175, 255)  # Blue-600
    padding = 20
    draw.ellipse([padding, padding, size[0]-padding, size[1]-padding], 
                 fill=circle_color)
    
    # Draw a smaller inner circle
    inner_padding = 40
    draw.ellipse([inner_padding, inner_padding, size[0]-inner_padding, size[1]-inner_padding], 
                 fill=(255, 255, 255, 255))
    
    # Draw a decorative pattern
    pattern_color = (30, 64, 175, 100)  # Lighter blue
    for i in range(8):  # Draw 8 decorative arcs
        angle = i * 45
        arc_bbox = [padding+10, padding+10, size[0]-padding-10, size[1]-padding-10]
        draw.arc(arc_bbox, angle, angle+30, fill=pattern_color, width=3)
    
    # Add a star symbol in the center
    star_color = (30, 64, 175, 255)
    center = size[0] // 2
    star_size = 60
    points = []
    
    # Create a 5-pointed star
    for i in range(10):
        angle = i * 36 - 90  # -90 to start at top
        radius = star_size if i % 2 == 0 else star_size * 0.4
        x = center + radius * cos(angle * pi / 180)
        y = center + radius * sin(angle * pi / 180)
        points.append((x, y))
    
    draw.polygon(points, fill=star_color)
    
    # Save the image
    os.makedirs('static/images/ui', exist_ok=True)
    image.save('static/images/ui/welcome_back.png')

if __name__ == '__main__':
    from math import cos, sin, pi
    create_welcome_back_image() 