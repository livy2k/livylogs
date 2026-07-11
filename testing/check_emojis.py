import tkinter as tk
from tkinter import font as tkfont
import sys

root = tk.Tk()
root.title("Font and Emoji Diagnostic")
root.geometry("800x800")

icons = [
    ("Friend (🛡️)", "🛡️"),
    ("Enemy (⚔️)", "⚔️"),
    ("Knockdown (🛌)", "🛌"),
    ("Posture (🧎)", "🧎"),
    ("Intimidate (❗)", "❗"),
    ("Poison (⚗️)", "⚗️"),
    ("Incap (☹️)", "☹️"),
    ("Hourglass (⏳)", "⏳")
]

test_fonts = ["Segoe UI", "Segoe UI Emoji", "Arial", "Courier New", "MS Sans Serif", "Tahoma", "Verdana"]

# Header
tk.Label(root, text=f"Python: {sys.version.split()[0]} | OS: {sys.platform}", font=("Arial", 12, "bold")).pack(pady=5)

canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# List all available fonts
available_fonts = list(tkfont.families())
# tk.Label(scrollable_frame, text=f"Available Fonts: {', '.join(available_fonts[:10])}...", wraplength=700).pack()

for font_name in test_fonts:
    is_available = font_name in available_fonts
    color = "black" if is_available else "red"
    section = tk.LabelFrame(scrollable_frame, text=f"Font: {font_name} (Available: {is_available})", fg=color, font=("Arial", 10, "bold"))
    section.pack(fill=tk.X, padx=10, pady=5)
    
    # Test names
    name_test = tk.Label(section, text="Player Name Test: Livy, Autobahn, EnemyPlayer123", font=(font_name, 12, "bold"))
    name_test.pack(pady=2)
    
    # Test icons
    icon_row = tk.Frame(section)
    icon_row.pack()
    for name, icon in icons:
        tk.Label(icon_row, text=icon, font=(font_name, 14)).pack(side=tk.LEFT, padx=5)
        tk.Label(icon_row, text=name.split()[0], font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 10))

# Manual check for Symbol font or Wingdings as potential fallbacks if needed
fallback_section = tk.LabelFrame(scrollable_frame, text="System Fallbacks (Mixed)", font=("Arial", 10, "bold"))
fallback_section.pack(fill=tk.X, padx=10, pady=5)
tk.Label(fallback_section, text="⚔️🛡️🛌🧎❗⚗️☹️⏳ (No Font Specified)").pack()

# Quit after a reasonable time for the user to screenshot if they want, though we can't see it
# In a real scenario, the user would run this and tell us. 
# For Junie, we just prepare it.
# root.after(30000, root.destroy) 
root.mainloop()
