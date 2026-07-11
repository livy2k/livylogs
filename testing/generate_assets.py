import random
from PIL import Image, ImageDraw, ImageFilter

def generate_brushed_metal(width, height, color=(60, 60, 60)):
    # Create base gray image
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Add noise
    for _ in range(width * height // 2):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        c = random.randint(-20, 20)
        base = color[0]
        nc = max(0, min(255, base + c))
        draw.point((x, y), fill=(nc, nc, nc))
    
    # Motion blur for "brushed" effect (horizontal)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Manual horizontal streaks
    for _ in range(100):
        y = random.randint(0, height - 1)
        length = random.randint(50, width)
        x = random.randint(0, width - length)
        c = random.randint(-10, 10)
        base = color[0]
        nc = max(0, min(255, base + c))
        draw.line((x, y, x + length, y), fill=(nc, nc, nc), width=1)
        
    return img

def generate_knob_texture(size):
    # Circular brushed metal
    img = Image.new('RGB', (size, size), (40, 40, 40))
    draw = ImageDraw.Draw(img)
    center = size // 2
    
    # Radial noise/lines
    for i in range(0, 360, 2):
        import math
        angle = math.radians(i)
        c = random.randint(30, 60)
        draw.line((center, center, center + size * math.cos(angle), center + size * math.sin(angle)), 
                  fill=(c, c, c), width=1)
    
    # Add some concentric circles for detail
    for r in range(size // 4, size // 2, 5):
        c = random.randint(40, 70)
        draw.ellipse((center - r, center - r, center + r, center + r), outline=(c, c, c), width=1)
        
    return img

if __name__ == "__main__":
    # Generate assets
    bezel = generate_brushed_metal(400, 80, (50, 50, 50))
    bezel.save("radio_bezel_texture.png")
    
    knob = generate_knob_texture(100)
    knob.save("radio_knob_texture.png")
    
    print("Generated radio_bezel_texture.png and radio_knob_texture.png")
