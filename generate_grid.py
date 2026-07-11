from PIL import Image, ImageDraw, ImageFont
import os

def create_grid(input_path, output_path, step=20):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    img = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Use a basic font
    try:
        font = ImageFont.load_default()
    except:
        font = None

    color = (255, 0, 0) # Red lines for visibility
    text_color = (255, 255, 255) # White text
    bg_color = (0, 0, 0) # Black text background

    # Draw vertical lines
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=color, width=1)
        # Label every 20 pixels for better precision, lines every 10.
        if x % 20 == 0:
            text = str(x)
            bbox = draw.textbbox((x + 2, 2), text, font=font)
            draw.rectangle(bbox, fill=bg_color)
            draw.text((x + 2, 2), text, fill=text_color, font=font)

    # Draw horizontal lines
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=color, width=1)
        if y % 20 == 0:
            text = str(y)
            bbox = draw.textbbox((2, y + 2), text, font=font)
            draw.rectangle(bbox, fill=bg_color)
            draw.text((2, y + 2), text, fill=text_color, font=font)

    img.save(output_path)
    print(f"Grid image saved to {output_path} ({width}x{height}) with step {step}")

if __name__ == "__main__":
    create_grid("realradioBASE.jpg", "radiogrid.jpg", step=10)
