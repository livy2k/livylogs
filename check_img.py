from PIL import Image

def analyze_regions(img_path):
    img = Image.open(img_path).convert('L')
    w, h = img.size
    
    rows = 10
    cols = 10
    rh = h // rows
    cw = w // cols
    
    print(f"Analysis of {img_path} ({w}x{h}):")
    for y in range(0, h - rh + 1, rh):
        row = []
        for x in range(0, w - cw + 1, cw):
            # Calculate average manually to avoid numpy dependency
            region = img.crop((x, y, x + cw, y + rh))
            pixels = list(region.getdata())
            avg = sum(pixels) / len(pixels)
            row.append(f"{int(avg):3}")
        print(" ".join(row))

try:
    analyze_regions('realradio.jpg')
except Exception as e:
    print(e)
