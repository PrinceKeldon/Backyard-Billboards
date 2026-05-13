"""
Generate default Open Graph image for Happy Hour Hub
"""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_default_og_image():
    """Generate a default Open Graph image for social media sharing"""
    try:
        # Create a 1200x630 image (standard OG image size)
        width, height = 1200, 630
        img = Image.new('RGB', (width, height), color=(33, 37, 41))  # Dark background
        
        # Draw on the image
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fallback to default if not available
        try:
            title_font = ImageFont.truetype("Arial.ttf", 60)
            subtitle_font = ImageFont.truetype("Arial.ttf", 40)
        except IOError:
            # Fallback to default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Draw a cocktail glass shape
        glass_color = (220, 53, 69)  # Bootstrap danger red
        
        # Simplified cocktail glass
        glass_top_width = 300
        glass_height = 350
        stem_width = 80
        base_width = 180
        
        # Position the glass
        glass_x = (width - glass_top_width) // 2
        glass_y = 120
        
        # Draw the glass top (trapezoid)
        glass_top_points = [
            (glass_x, glass_y),
            (glass_x + glass_top_width, glass_y),
            (glass_x + glass_top_width - 40, glass_y + glass_height - 50),
            (glass_x + 40, glass_y + glass_height - 50)
        ]
        draw.polygon(glass_top_points, fill=glass_color)
        
        # Draw the stem
        stem_x = glass_x + (glass_top_width - stem_width) // 2
        stem_y = glass_y + glass_height - 50
        draw.rectangle(
            (stem_x, stem_y, stem_x + stem_width, stem_y + 70), 
            fill=glass_color
        )
        
        # Draw the base
        base_x = glass_x + (glass_top_width - base_width) // 2
        base_y = glass_y + glass_height + 20
        draw.ellipse(
            (base_x, base_y, base_x + base_width, base_y + 40), 
            fill=glass_color
        )
        
        # Draw title text
        title_text = "BACKYARD BILLBOARDS"
        title_width = draw.textlength(title_text, font=title_font)
        title_position = ((width - title_width) // 2, 30)
        draw.text(
            title_position, 
            title_text, 
            font=title_font, 
            fill=(248, 249, 250)  # Light text
        )
        
        # Draw subtitle
        subtitle_text = "Happy Hour Deals in Berlin"
        subtitle_width = draw.textlength(subtitle_text, font=subtitle_font)
        subtitle_position = ((width - subtitle_width) // 2, height - 120)
        draw.text(
            subtitle_position, 
            subtitle_text, 
            font=subtitle_font, 
            fill=(248, 249, 250)  # Light text
        )
        
        # Save the image
        if not os.path.exists("static/img"):
            os.makedirs("static/img")
        
        img.save("static/img/og-default.jpg")
        print("Generated default Open Graph image at static/img/og-default.jpg")
        return True
    
    except Exception as e:
        print(f"Error generating OG image: {str(e)}")
        return False

if __name__ == "__main__":
    generate_default_og_image()