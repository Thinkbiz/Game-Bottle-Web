from PIL import Image
import io
import os
import base64

def create_favicon():
    # Create the favicon directory if it doesn't exist
    os.makedirs('static/favicon', exist_ok=True)
    
    # Create a 32x32 version of the image for the favicon
    img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
    
    # Colors
    blue = (173, 216, 230, 255)  # Light blue for body
    white = (255, 255, 255, 255)  # White for eyes
    black = (0, 0, 0, 255)  # Black for pupils
    
    # Draw the circular base for the creature
    for x in range(32):
        for y in range(32):
            # Calculate distance from center
            dx = x - 16
            dy = y - 16
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Create a circular shape
            if distance < 14:
                img.putpixel((x, y), blue)
    
    # Add two white circular eyes with black pupils
    # Left eye
    for x in range(8, 15):  # Eye position
        for y in range(10, 17):  # Eye position
            dx = x - 11.5  # Eye center
            dy = y - 13.5  # Eye center
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 3:  # Eye size
                img.putpixel((x, y), white)
                # Add black pupil
                if distance < 1.5:  # Pupil size
                    img.putpixel((x, y), black)
    
    # Right eye
    for x in range(17, 24):  # Eye position
        for y in range(10, 17):  # Eye position
            dx = x - 20.5  # Eye center
            dy = y - 13.5  # Eye center
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 3:  # Eye size
                img.putpixel((x, y), white)
                # Add black pupil
                if distance < 1.5:  # Pupil size
                    img.putpixel((x, y), black)
    
    # Save as PNG
    img.save('static/favicon/favicon.png', 'PNG')

if __name__ == '__main__':
    create_favicon() 