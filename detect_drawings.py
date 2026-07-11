from PIL import Image
import os

def detect_markings():
    img_path = "realradio.jpg"
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        return

    img = Image.open(img_path).convert("RGB")
    pixels = img.load()
    w, h = img.size
    
    # We look for bright colors (like red, yellow, green) that stand out from the black/grey hardware
    marks = []
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            # Heuristic for detecting "drawn" markings (saturated or bright colors)
            # Red markings
            if r > 150 and g < 100 and b < 100:
                marks.append((x, y, "RED"))
            # Yellow markings
            elif r > 150 and g > 150 and b < 100:
                marks.append((x, y, "YELLOW"))
            # Blue/Cyan markings
            elif r < 100 and g > 150 and b > 150:
                marks.append((x, y, "CYAN"))

    if not marks:
        print("No specific color markings detected. Checking for high-contrast white...")
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                if r > 200 and g > 200 and b > 200:
                    marks.append((x, y, "WHITE"))

    # Group pixels into clusters (very simple bounding box)
    if marks:
        print(f"Detected {len(marks)} marked pixels.")
        # Print a 20x10 grid of where marks are to visualize in console
        grid_w, grid_h = 20, 10
        for gy in range(grid_h):
            line = ""
            for gx in range(grid_w):
                found = False
                for mx, my, mc in marks:
                    if mx // (w // grid_w) == gx and my // (h // grid_h) == gy:
                        found = True
                        break
                line += "X" if found else "."
            print(line)
    else:
        print("No markings found.")

if __name__ == "__main__":
    detect_markings()
