from PIL import Image
import os

def convert():
    input_png = "livylogs.png"
    output_ico = "livylogs.ico"
    if not os.path.exists(input_png):
        print(f"Error: {input_png} not found.")
        return
    
    print(f"Converting {input_png} to {output_ico}...")
    img = Image.open(input_png)
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico, sizes=icon_sizes)
    if os.path.exists(output_ico):
        print(f"Success! {output_ico} created.")
    else:
        print("Failed to create ico file.")

if __name__ == "__main__":
    convert()
