from PIL import Image, ImageDraw
import os

def visualize_regions():
    # Priority for base image
    if os.path.exists("realradioBASE.jpg"):
        img_path = "realradioBASE.jpg"
    elif os.path.exists("realradio.jpg"):
        img_path = "realradio.jpg"
    else:
        img_path = None
        
    if img_path:
        img = Image.open(img_path).convert("RGB")
    else:
        img = Image.new("RGB", (638, 154), (20, 20, 20))
    
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Zones from design_template.py / livylogs_main.py
    regions = [
        {"box": (10, 10, 80, 40),   "label": "SETTINGS",    "color": (50, 50, 150, 180)},
        {"box": (500, 10, 570, 40), "label": "EXIT",        "color": (255, 50, 50, 100)},
        {"box": (530, 105, 630, 135), "label": "ALEXA",       "color": (0, 200, 255, 100)},
        {"box": (500, 60, 570, 100), "label": "SKIP",        "color": (255, 255, 0, 100)},
        {"box": (170, 10, 250, 40),  "label": "XP",          "color": (50, 255, 50, 100)},
        {"box": (260, 10, 315, 40),  "label": "XP/H",        "color": (50, 200, 50, 100)},
        {"box": (325, 10, 380, 40),  "label": "DMG",         "color": (255, 50, 50, 100)},
        {"box": (390, 10, 445, 40),  "label": "DPS",         "color": (255, 100, 50, 100)},
        {"box": (200, 105, 300, 135), "label": "DMG METER",   "color": (255, 100, 255, 100)},
        {"box": (310, 105, 410, 135), "label": "DETAILS",     "color": (200, 100, 255, 100)},
        {"box": (420, 105, 520, 135), "label": "SKIMMERS",    "color": (100, 255, 255, 100)},
        {"box": (200, 50, 580, 105), "label": "LCD SCREEN", "color": (255, 255, 255, 40)},
    ]
    
    for r in regions:
        draw.rectangle(r["box"], fill=r["color"], outline="white")
        draw.text((r["box"][0]+3, r["box"][1]+3), r["label"], fill="black")
        draw.text((r["box"][0]+2, r["box"][1]+2), r["label"], fill="white")

    out_path = "region_map.png"
    img.save(out_path)
    print(f"Region map updated at {out_path}")

if __name__ == "__main__":
    visualize_regions()
