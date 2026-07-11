from PIL import Image, ImageDraw
import os

def generate_template():
    # Target resolution 638x154
    w, h = 638, 154
    img = Image.new("RGB", (w, h), (15, 15, 15))
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Define clear zones for the requested features
    # Format: (x1, y1, x2, y2), Label, Color, Number
    zones = [
        # Functional Buttons
        {"box": (10, 10, 80, 40),   "label": "SETTINGS",    "color": (50, 50, 150, 180), "num": "6"},
        {"box": (500, 10, 570, 40),  "label": "EXIT",        "color": (255, 50, 50, 150), "num": ""},
        {"box": (530, 105, 630, 135), "label": "ALEXA",       "color": (0, 200, 255, 150), "num": "7"},
        
        # Navigation / Action
        {"box": (500, 60, 570, 100), "label": "SKIP",        "color": (255, 255, 0, 150), "num": "5"},
        
        # Data Readouts (Displays)
        {"box": (170, 10, 250, 40),  "label": "XP",          "color": (50, 255, 50, 100), "num": "10"},
        {"box": (260, 10, 315, 40),  "label": "XP/H",        "color": (50, 200, 50, 100), "num": "11"},
        {"box": (325, 10, 380, 40),  "label": "DMG",         "color": (255, 50, 50, 100), "num": "8"},
        {"box": (390, 10, 445, 40),  "label": "DPS",         "color": (255, 100, 50, 100), "num": "9"},
        
        # Mode Selection Buttons (Bottom Row)
        {"box": (200, 105, 300, 135), "label": "DMG METER",   "color": (255, 100, 255, 150), "num": "1"},
        {"box": (310, 105, 410, 135), "label": "DETAILS",     "color": (200, 100, 255, 150), "num": "2"},
        {"box": (420, 105, 520, 135), "label": "SKIMMERS",    "color": (100, 255, 255, 150), "num": "4"},
        
        # Main Central Display Area
        {"box": (200, 50, 580, 105), "label": "MAIN RADIO DISPLAY", "color": (255, 255, 255, 30), "num": ""},
    ]
    
    for z in zones:
        draw.rectangle(z["box"], fill=z["color"], outline="white")
        # Draw text
        label = z["label"]
        if z["num"]: label = f"[{z['num']}] {label}"
        draw.text((z["box"][0]+5, z["box"][1]+5), label, fill="white")

    out_path = "design_template.png"
    img.save(out_path)
    print(f"Template saved to {out_path}")

if __name__ == "__main__":
    generate_template()
