"""
LivyLogs - Combat Log Analyzer
Copyright (c) 2026 Livy
Licensed under the GNU General Public License v3.0.
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import os
from constants import (
    WINDOW_BG, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY, ACCENT_BLUE, 
    BUTTON_BG, BUTTON_HOVER, BORDER_COLOR, PANEL_BG
)
from windows.base_window import BasePopoutWindow

class LabelEditorWindow(BasePopoutWindow):
    def __init__(self, app):
        # Increased size for almost full screen
        sw = app.root.winfo_screenwidth()
        sh = app.root.winfo_screenheight()
        w = int(sw * 0.9)
        h = int(sh * 0.9)
        super().__init__(app, "Label Editor", "LabelEditorWindow", w, h, centered=True)
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.labels_file = os.path.join(self.base_dir, "ui_labels_map.txt")
        self.current_window_key = "Main"
        self.selected_label_index = -1
        self.label_data = []
        self.canvas_labels = {} # canvas_id -> label_data_index
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.tool_mode = tk.StringVar(value="Select") # Tool modes: Select, Text, Rectangle, Circle
        self.history = [] # For undo: list of label_data snapshots
        self.zoom_level = 1.0
        self.bg_image = None
        self.window_options = {
            "Main": {"file": os.path.join(self.base_dir, "ui_labels_map.txt"), "img": "livylogs.png", "size": (638, 154)},
            "Alexa": {"file": os.path.join(self.base_dir, "ui_labels_alexawindow.txt"), "img": "livylogs.png", "size": (600, 500)},
            "Damage": {"file": os.path.join(self.base_dir, "ui_labels_damagemeterwindow.txt"), "img": "livylogs.png", "size": (500, 400)},
            "Details": {"file": os.path.join(self.base_dir, "ui_labels_detailswindow.txt"), "img": "livylogs.png", "size": (600, 450)},
            "Skimmers": {"file": os.path.join(self.base_dir, "ui_labels_skimmerswindow.txt"), "img": "livylogs.png", "size": (500, 400)},
            "Loot": {"file": os.path.join(self.base_dir, "ui_labels_leaderboardwindow.txt"), "img": "livylogs.png", "size": (500, 400)},
            "UKN": {"file": os.path.join(self.base_dir, "ui_labels_uknview.txt"), "img": "livylogs.png", "size": (600, 500)},
            "Livius": {"file": os.path.join(self.base_dir, "ui_labels_liviuswindow.txt"), "img": "livylogs.png", "size": (750, 600)},
            "Options": {"file": os.path.join(self.base_dir, "ui_labels_optionswindow.txt"), "img": "livylogs.png", "size": (400, 500)}
        }

    def refresh(self, force=False):
        if not self.window or not self.window.winfo_exists(): return
        if self.window.state() == "withdrawn": return
        
        is_resizing = getattr(self, "_is_resizing", False) or getattr(self.window, "_is_resizing", False)
        is_dragging = getattr(self, "_is_dragging", False)
        
        if force or len(self.content_container.winfo_children()) == 0:
            if force and not is_resizing and not is_dragging:
                # Cancel pending rebuilds if we are forcing a refresh
                if hasattr(self, "_rebuild_timer") and self._rebuild_timer:
                    try:
                        self.window.after_cancel(self._rebuild_timer)
                    except: pass
                    self._rebuild_timer = None
                
                # Full rebuild only if not interacting
                self.load_labels()
                self._safe_rebuild()
            elif len(self.content_container.winfo_children()) == 0:
                self._safe_rebuild()
            elif is_resizing:
                # Fast update during resize - just adjust scaling
                self.update_canvas_scaling()

    def _safe_rebuild(self):
        if not self.window or not self.window.winfo_exists(): return
        if not self.content_container or not self.content_container.winfo_exists(): return
        
        # Cancel all pending tasks to avoid race conditions
        self._cancel_all_timers()

        try:
            with open("crash_log.txt", "a") as f:
                f.write(f"--- LabelEditor SAFE REBUILD START {__import__('datetime').datetime.now()} for {self.current_window_key} ---\n")
            
            # Clear selection and drag data before rebuild
            self.selected_label_index = -1
            self.drag_data = {"item": None, "start_cx": 0, "start_cy": 0}
            self.canvas_labels = {}
            self.bg_image = None
            
            # Ensure data is loaded
            try:
                self.load_labels()
            except Exception as load_err:
                 with open("crash_log.txt", "a") as f:
                    f.write(f"--- LabelEditor REBUILD LOAD_LABELS ERROR: {load_err}\n")
            
            # Ensure the window is visible
            alpha = max(0.9, self.app.current_alpha)
            try:
                self.window.attributes("-alpha", alpha)
            except: pass
            
            # Use try-except for build_ui
            try:
                self.build_ui()
            except Exception as build_err:
                 with open("crash_log.txt", "a") as f:
                    f.write(f"--- LabelEditor BUILD_UI CRASH: {build_err}\n{__import__('traceback').format_exc()}\n")
                 raise build_err
            
            # Bind shortcuts
            try:
                self.window.bind("<Alt-z>", lambda e: self.undo_action())
                self.window.bind("<Control-z>", lambda e: self.undo_action())
            except: pass
            
            # Use a staggered rendering to avoid race conditions
            if self.window and self.window.winfo_exists():
                self._render_timer = self.window.after(350, self.render_canvas_labels)
            
            with open("crash_log.txt", "a") as f:
                f.write(f"--- LabelEditor SAFE REBUILD DONE {__import__('datetime').datetime.now()} ---\n")
        except Exception as e:
            print(f"CRITICAL Error in _safe_rebuild: {e}")
            import traceback
            traceback.print_exc()
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- LabelEditor SAFE REBUILD CRASH {__import__('datetime').datetime.now()} ---\n{traceback.format_exc()}\n")
            except: pass

    def _cancel_all_timers(self):
        if not self.window or not self.window.winfo_exists(): return
        for timer_attr in ["_render_timer", "_rebuild_timer", "_resize_timer"]:
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer:
                    try:
                        self.window.after_cancel(timer)
                        with open("crash_log.txt", "a") as f:
                             f.write(f"--- CANCELLED {timer_attr} ---\n")
                    except: pass
                setattr(self, timer_attr, None)
        
        # Also clean up image references to avoid memory leaks or access errors
        self.bg_image = None

    def close(self):
        try:
            with open("crash_log.txt", "a") as f:
                f.write(f"--- LabelEditor CLOSING {__import__('datetime').datetime.now()} ---\n")
        except: pass
        self._cancel_all_timers()
        super().close()

    def on_window_change(self, event=None):
        if not self.window or not self.window.winfo_exists(): return
        
        # Debounce to prevent rapid destruction/recreation
        import time
        current_time = time.time()
        if hasattr(self, "_last_change_time") and current_time - self._last_change_time < 0.3:
            return
        self._last_change_time = current_time
        
        try:
            with open("crash_log.txt", "a") as f:
                f.write(f"--- LabelEditor WINDOW CHANGE {__import__('datetime').datetime.now()} ---\n")
            
            if not hasattr(self, "win_var") or not self.win_var: return
            self.current_window_key = self.win_var.get()
            opts = self.window_options.get(self.current_window_key)
            if not opts: return
            
            self.labels_file = opts["file"]
            
            # Cancel any pending tasks
            self._cancel_all_timers()

            # Ensure data is LOADED before we trigger any rebuild
            try:
                self.load_labels()
            except Exception as load_err:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- LabelEditor LOAD_LABELS CRASH: {load_err}\n")

            # Use after to allow the dropdown to close/finish before rebuilding the entire UI
            self._rebuild_timer = self.window.after(200, self._safe_rebuild)
        except Exception as e:
            print(f"Error in on_window_change: {e}")
            try:
                with open("crash_log.txt", "a") as f:
                    f.write(f"--- LabelEditor WINDOW CHANGE CRASH {__import__('datetime').datetime.now()} ---\n{e}\n")
            except: pass

    def load_labels(self):
        self.label_data = []
        if not self.labels_file or not os.path.exists(self.labels_file):
            # Try to resolve labels_file if it's missing or None
            if not self.labels_file:
                self.labels_file = self.window_options[self.current_window_key]["file"]
            
            # Create the file if it doesn't exist to avoid errors
            if self.labels_file and not os.path.exists(self.labels_file):
                try:
                    with open(self.labels_file, "w") as f:
                        f.write("# Name, X, Y, [FG], [Shape], [W], [H], [Font], [Size]\n")
                except: pass
            
            if not self.labels_file or not os.path.exists(self.labels_file):
                return

        try:
            with open(self.labels_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    # Format: Name, X, Y, [FG], [Shape], [W], [H], [Font], [Size]
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        name = parts[0]
                        try:
                            x = float(parts[1])
                            y = float(parts[2])
                            fg = parts[3] if len(parts) > 3 else "#FFFFFF"
                            shape = parts[4] if len(parts) > 4 else "None"
                            w = float(parts[5]) if len(parts) > 5 else 0
                            h = float(parts[6]) if len(parts) > 6 else 0
                            font_fam = parts[7] if len(parts) > 7 else "Segoe UI"
                            font_size = parts[8] if len(parts) > 8 else "9"
                            
                            self.label_data.append({
                                "name": name, "x": x, "y": y, 
                                "fg": fg if fg else "#FFFFFF",
                                "shape": shape if shape else "None", 
                                "w": w, "h": h,
                                "font": font_fam if font_fam else "Segoe UI",
                                "size": font_size if font_size else "9"
                            })
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            print(f"Error loading labels: {e}")

    def save_labels(self):
        # Format the data into lines before saving
        try:
            lines = ["# Name, X, Y, [FG], [Shape], [W], [H], [Font], [Size]\n"]
            for ld in self.label_data:
                # Ensure we use 'None' if shape is empty
                shape_val = ld.get('shape', 'None')
                if not shape_val: shape_val = 'None'
                line = f"{ld['name']}, {ld['x']}, {ld['y']}, {ld['fg']}, {shape_val}, {ld.get('w', 0)}, {ld.get('h', 0)}, {ld.get('font', 'Segoe UI')}, {ld.get('size', '9')}\n"
                lines.append(line)
            
            # Use absolute path for saving
            save_path = self.window_options[self.current_window_key]["file"]
            with open(save_path, "w") as f:
                f.writelines(lines)
            
            # Verify file was written
            if os.path.getsize(save_path) == 0:
                print("Warning: Label file was written but is empty.")
        except Exception as e:
            print(f"Error saving labels: {e}")
            return
        
        # Trigger UI refresh
        try:
            if self.current_window_key == "Main":
                self.app.refresh_ui_only(force=True)
            elif self.current_window_key == "UKN":
                if hasattr(self.app.alexa_win, "_load_dynamic_labels"):
                    self.app.alexa_win._load_dynamic_labels()
                if hasattr(self.app.alexa_win, "show_ukn_view"):
                    self.app.alexa_win.show_ukn_view()
            else:
                mapping = {
                    "Livius": self.app.livius_win,
                    "Alexa": self.app.alexa_win,
                    "Damage": self.app.damage_meter_win,
                    "Details": self.app.details_win,
                    "Skimmers": self.app.skimmers_win,
                    "Loot": self.app.leaderboard_win,
                    "Options": self.app.options_win
                }
                win_obj = mapping.get(self.current_window_key)
                if win_obj:
                    if hasattr(win_obj, "_load_dynamic_labels"):
                        win_obj._load_dynamic_labels()
                    if hasattr(win_obj, "refresh"):
                        win_obj.refresh(force=True)
        except Exception as e:
            print(f"Error refreshing UI after save: {e}")

    def build_ui(self):
        if not self.window or not self.window.winfo_exists(): return
        if not self.content_container or not self.content_container.winfo_exists():
            return
            
        # Clean up existing widgets
        for child in self.content_container.winfo_children():
            try:
                child.destroy()
            except: pass

        # Force update to ensure container is cleared and ready
        try:
            self.content_container.update_idletasks()
        except: return

        # Update window size based on selected window to fit canvas
        # But only if we aren't currently being resized by the user
        is_resizing = getattr(self, "_is_resizing", False) or getattr(self.window, "_is_resizing", False)
        is_dragging = getattr(self, "_is_dragging", False)
        
        if not is_resizing and not is_dragging:
            opts = self.window_options[self.current_window_key]
            img_w, img_h = opts["size"]
            # Add space for controls (approx 300px width) and padding
            new_w = max(950, img_w + 350)
            new_h = max(500, img_h + 100)
            
            # For 90% screen size on first open or explicit switch
            try:
                sw = self.window.winfo_screenwidth()
                sh = self.window.winfo_screenheight()
                new_w = min(new_w, int(sw * 0.95))
                new_h = min(new_h, int(sh * 0.95))
            except:
                new_w = min(new_w, 1600)
                new_h = min(new_h, 900)
            
            # Only resize if needed to avoid flickering
            try:
                self.window.update_idletasks()
                curr_w = self.window.winfo_width()
                curr_h = self.window.winfo_height()
                if abs(curr_w - new_w) > 50 or abs(curr_h - new_h) > 50:
                     self.window.geometry(f"{new_w}x{new_h}")
            except: pass

        # Main Layout
        main_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top Bar: Window Selector and Tool Palette
        top_bar = tk.Frame(main_frame, bg=WINDOW_BG)
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        selector_frame = tk.Frame(top_bar, bg=WINDOW_BG)
        selector_frame.pack(side=tk.LEFT)
        
        tk.Label(selector_frame, text="WINDOW:", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        
        self.win_var = tk.StringVar(value=self.current_window_key)
        self.win_dropdown = ttk.Combobox(selector_frame, textvariable=self.win_var, values=list(self.window_options.keys()), state="readonly", width=10)
        self.win_dropdown.pack(side=tk.LEFT, padx=5)
        self.win_dropdown.bind("<<ComboboxSelected>>", self.on_window_change)

        # Palette
        palette_frame = tk.Frame(top_bar, bg=PANEL_DARK, padx=5, pady=2)
        palette_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(palette_frame, text="TOOLS:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        for mode in ["Select", "Text", "Rectangle", "Circle"]:
            rb = tk.Radiobutton(palette_frame, text=mode.upper(), variable=self.tool_mode, value=mode,
                                bg=PANEL_DARK, fg=TEXT_PRIMARY, selectcolor=ACCENT_BLUE,
                                activebackground=PANEL_DARK, activeforeground=TEXT_PRIMARY,
                                font=("Segoe UI", 8, "bold"), indicatoron=0, padx=8, pady=2, borderwidth=0)
            rb.pack(side=tk.LEFT, padx=2)
            # Help user realize what's selected
            def on_mode_change(m=mode):
                 try:
                    with open("crash_log.txt", "a") as f:
                        f.write(f"--- LabelEditor MODE CHANGE: {m} ---\n")
                 except: pass
            rb.config(command=on_mode_change)

        # Zoom Controls
        zoom_frame = tk.Frame(top_bar, bg=PANEL_DARK, padx=5, pady=2)
        zoom_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(zoom_frame, text="ZOOM:", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        for z in [0.5, 1.0, 1.5, 2.0, "Fit"]:
            z_text = f"{int(z*100)}%" if isinstance(z, (int, float)) else "FIT"
            z_btn = tk.Label(zoom_frame, text=z_text, bg=PANEL_DARK, fg=TEXT_PRIMARY, 
                             font=("Segoe UI", 8, "bold"), padx=5, cursor="hand2")
            z_btn.pack(side=tk.LEFT)
            z_btn.bind("<Button-1>", lambda e, val=z: self.set_zoom(val))
            z_btn.bind("<Enter>", lambda e, b=z_btn: b.config(bg=BUTTON_HOVER))
            z_btn.bind("<Leave>", lambda e, b=z_btn: b.config(bg=PANEL_DARK))

        # Left side: Visual Editor
        visual_outer = tk.Frame(main_frame, bg=WINDOW_BG)
        visual_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        visual_frame = tk.Frame(visual_outer, bg=PANEL_DARK, borderwidth=1, relief="sunken")
        visual_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(visual_frame, text="VISUAL EDITOR (DRAG TO MOVE / CLICK TO ADD)", bg=PANEL_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=5, pady=5)

        # Scrollbars for large canvases
        self.canvas_scroll_x = tk.Scrollbar(visual_frame, orient=tk.HORIZONTAL)
        self.canvas_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_scroll_y = tk.Scrollbar(visual_frame, orient=tk.VERTICAL)
        self.canvas_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for background
        from PIL import Image, ImageTk
        opts = self.window_options[self.current_window_key]
        img_path = opts["img"]
        img_w, img_h = opts["size"]
        
        if img_path:
            full_img_path = os.path.join(self.base_dir, img_path) if not os.path.isabs(img_path) else img_path
            if not os.path.exists(full_img_path):
                 # Fallback to alternative image if requested one is missing
                 alt_img = "livylogs.png" if img_path != "livylogs.png" else "realradioBASE.jpg"
                 full_img_path = os.path.join(self.base_dir, alt_img)
            
            if os.path.exists(full_img_path):
                try:
                    img = Image.open(full_img_path)
                    img = img.resize((int(img_w * self.zoom_level), int(img_h * self.zoom_level)), Image.Resampling.LANCZOS)
                    self.bg_image = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Error loading bg image: {e}")
                    self.bg_image = None
            else:
                self.bg_image = None
        else:
            self.bg_image = None
        
        self.canvas_h = img_h * self.zoom_level
        self.canvas_w = img_w * self.zoom_level

        self.editor_canvas = tk.Canvas(visual_frame, width=self.canvas_w, height=self.canvas_h, bg="#000000", 
                                       highlightthickness=1, highlightbackground=BORDER_COLOR,
                                       xscrollcommand=self.canvas_scroll_x.set,
                                       yscrollcommand=self.canvas_scroll_y.set,
                                       scrollregion=(0, 0, self.canvas_w, self.canvas_h))
        self.editor_canvas.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        
        self.canvas_scroll_x.config(command=self.editor_canvas.xview)
        self.canvas_scroll_y.config(command=self.editor_canvas.yview)
        
        if self.bg_image:
            self.editor_canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg")
        else:
            # Placeholder for windows without background images - make it prominent
            self.editor_canvas.create_rectangle(0, 0, self.canvas_w, self.canvas_h, fill="#111111", outline=BORDER_COLOR, tags="bg")
            
            # Add a subtle grid to the placeholder
            for i in range(0, int(self.canvas_w), int(50 * self.zoom_level)):
                self.editor_canvas.create_line(i, 0, i, self.canvas_h, fill="#222222", tags="bg")
            for i in range(0, int(self.canvas_h), int(50 * self.zoom_level)):
                self.editor_canvas.create_line(0, i, self.canvas_w, i, fill="#222222", tags="bg")

            self.editor_canvas.create_text(self.canvas_w//2, self.canvas_h//2, text=f"{self.current_window_key.upper()} WINDOW LAYOUT", 
                                           fill=TEXT_PRIMARY, font=("Segoe UI", int(14 * self.zoom_level), "bold"), tags="bg")
            self.editor_canvas.create_text(self.canvas_w//2, self.canvas_h//2 + int(30 * self.zoom_level), text=f"({img_w} x {img_h})", 
                                           fill=TEXT_SECONDARY, font=("Segoe UI", int(10 * self.zoom_level)), tags="bg")
            self.editor_canvas.create_text(self.canvas_w//2, self.canvas_h - int(20 * self.zoom_level), text="0,0 (Bottom-Left Origin)", 
                                           fill=ACCENT_BLUE, font=("Segoe UI", int(8 * self.zoom_level), "italic"), tags="bg")

        self.editor_canvas.bind("<Button-1>", self.on_canvas_click)
        self.editor_canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.editor_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.editor_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Right side: Controls
        right_frame = tk.Frame(main_frame, bg=WINDOW_BG)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Listbox for labels
        list_frame = tk.Frame(right_frame, bg=WINDOW_BG)
        list_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(list_frame, text="LABELS", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        
        self.label_listbox = tk.Listbox(list_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, borderwidth=0, 
                                       highlightthickness=1, highlightbackground=BORDER_COLOR,
                                       selectbackground=ACCENT_BLUE, selectforeground=TEXT_PRIMARY,
                                       font=("Segoe UI", 9), width=30)
        self.label_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.label_listbox.bind("<<ListboxSelect>>", self.on_select_label)

        # Edit controls
        edit_frame = tk.Frame(right_frame, bg=WINDOW_BG)
        edit_frame.pack(fill=tk.X)

        tk.Label(edit_frame, text="EDIT SELECTED", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w")

        # Name
        tk.Label(edit_frame, text="TEXT", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w", pady=(5, 0))
        self.entry_name = tk.Entry(edit_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, borderwidth=0, font=("Segoe UI", 9))
        self.entry_name.pack(fill=tk.X, pady=2)

        # Coords
        coord_frame = tk.Frame(edit_frame, bg=WINDOW_BG)
        coord_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(coord_frame, text="X", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(side=tk.LEFT)
        self.entry_x = tk.Entry(coord_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, width=8, borderwidth=0, font=("Segoe UI", 9))
        self.entry_x.pack(side=tk.LEFT, padx=(5, 10))

        tk.Label(coord_frame, text="Y", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(side=tk.LEFT)
        self.entry_y = tk.Entry(coord_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, width=8, borderwidth=0, font=("Segoe UI", 9))
        self.entry_y.pack(side=tk.LEFT, padx=5)

        # Color
        tk.Label(edit_frame, text="COLOR", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w", pady=(2, 0))
        self.btn_color = tk.Button(edit_frame, text="PICK COLOR", bg=BUTTON_BG, fg=TEXT_PRIMARY, 
                                   borderwidth=0, font=("Segoe UI", 8, "bold"), command=self.pick_color)
        self.btn_color.pack(fill=tk.X, pady=2)

        # Shape
        tk.Label(edit_frame, text="SHAPE", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(anchor="w", pady=(2, 0))
        self.shape_var = tk.StringVar(value="None")
        self.shape_dropdown = ttk.Combobox(edit_frame, textvariable=self.shape_var, values=["None", "Rectangle", "Circle"], state="readonly")
        self.shape_dropdown.pack(fill=tk.X, pady=2)
        
        dim_frame = tk.Frame(edit_frame, bg=WINDOW_BG)
        dim_frame.pack(fill=tk.X, pady=2)
        tk.Label(dim_frame, text="W", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(side=tk.LEFT)
        self.entry_w = tk.Entry(dim_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, width=8, borderwidth=0, font=("Segoe UI", 9))
        self.entry_w.pack(side=tk.LEFT, padx=(5, 10))
        self.entry_w.insert(0, "0")
        
        tk.Label(dim_frame, text="H", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 7)).pack(side=tk.LEFT)
        self.entry_h = tk.Entry(dim_frame, bg=PANEL_DARK, fg=TEXT_PRIMARY, width=8, borderwidth=0, font=("Segoe UI", 9))
        self.entry_h.pack(side=tk.LEFT, padx=5)
        self.entry_h.insert(0, "0")

        # Action Buttons
        btn_box = tk.Frame(edit_frame, bg=WINDOW_BG)
        btn_box.pack(fill=tk.X, pady=5)

        def add_btn(text, cmd, color=BUTTON_BG):
            b = tk.Label(btn_box, text=text, bg=color, fg=TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), pady=5, cursor="hand2")
            b.pack(fill=tk.X, pady=2)
            b.bind("<Enter>", lambda e: b.config(bg=BUTTON_HOVER))
            b.bind("<Leave>", lambda e: b.config(bg=color))
            b.bind("<Button-1>", lambda e: cmd())

        add_btn("UPDATE / ADD", self.update_label, color=ACCENT_BLUE)
        add_btn("UNDO", self.undo_action, color="#555555")
        add_btn("DELETE", self.delete_label, color="#AA3333")
        add_btn("CLEAR ALL", self.clear_all_labels, color="#773333")
        add_btn("SAVE ALL", self.save_labels)

        # Font & Size
        tk.Label(edit_frame, text="FONT & SIZE", bg=WINDOW_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10, 0))
        font_frame = tk.Frame(edit_frame, bg=WINDOW_BG)
        font_frame.pack(fill=tk.X, pady=2)
        
        self.font_var = tk.StringVar(value="Segoe UI")
        self.font_dropdown = ttk.Combobox(font_frame, textvariable=self.font_var, 
                                          values=["Segoe UI", "Arial", "Courier New", "Verdana", "Impact", "Segoe UI Emoji", "Segoe UI Symbol"], 
                                          state="readonly", width=12)
        self.font_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.font_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_label() if self.selected_label_index >= 0 else None)
        
        self.size_var = tk.StringVar(value="9")
        self.size_dropdown = ttk.Combobox(font_frame, textvariable=self.size_var, 
                                          values=["6", "7", "8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"], 
                                          state="readonly", width=5)
        self.size_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        self.size_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_label() if self.selected_label_index >= 0 else None)

        self.populate_list()
        self.render_canvas_labels()

    def populate_list(self):
        if not hasattr(self, 'label_listbox') or not self.label_listbox.winfo_exists():
            return
        self.label_listbox.delete(0, tk.END)
        for ld in self.label_data:
            try:
                self.label_listbox.insert(tk.END, f"{ld['name']} ({ld['x']}, {ld['y']})")
            except: pass

    def set_zoom(self, val):
        if not hasattr(self, 'editor_canvas') or not self.editor_canvas.winfo_exists(): return
        
        # Cancel all active design tasks before changing zoom
        self._cancel_all_timers()
        
        if val == "Fit":
            opts = self.window_options[self.current_window_key]
            img_w, _ = opts["size"]
            try:
                self.editor_canvas.update_idletasks()
                canvas_avail_w = self.editor_canvas.winfo_width() - 20
                if canvas_avail_w > 50:
                    self.zoom_level = canvas_avail_w / img_w
                else:
                    self.zoom_level = 1.0
            except:
                self.zoom_level = 1.0
        else:
            self.zoom_level = val
        
        self._safe_rebuild()

    def render_canvas_labels(self):
        if not hasattr(self, 'editor_canvas') or not self.editor_canvas.winfo_exists():
            return
        
        # Ensure the window still exists before continuing
        if not self.window or not self.window.winfo_exists():
            return

        # Double check canvas is ready
        try:
            self.editor_canvas.update_idletasks()
        except: return
        
        try:
            # Clear existing labels (but keep background image and grid)
            # Instead of deleting all, we just delete those tagged as "labels"
            self.editor_canvas.delete("labels")
            self.canvas_labels = {}
        except: return

        for i, ld in enumerate(self.label_data):
            try:
                # Convert bottom-left to top-left for canvas, applying zoom
                cx = ld['x'] * self.zoom_level
                cy = self.canvas_h - (ld['y'] * self.zoom_level)
                
                fg = ld['fg']
                if i == self.selected_label_index:
                    fg = ACCENT_BLUE
                
                shape = ld.get('shape', '')
                w = ld.get('w', 0) * self.zoom_level
                h = ld.get('h', 0) * self.zoom_level
                font_fam = ld.get('font', 'Segoe UI')
                font_size = int(int(ld.get('size', 9)) * self.zoom_level)
                
                group_tag = f"label_group_{i}"
                tags = ("draggable", group_tag, "labels")
                
                if shape and shape != "None" and w > 0 and h > 0:
                    # Rect: x1, y1, x2, y2
                    if shape == "Rectangle":
                        sid = self.editor_canvas.create_rectangle(cx, cy - h, cx + w, cy, 
                                                              outline=fg, width=1, tags=tags)
                    elif shape == "Circle":
                        sid = self.editor_canvas.create_oval(cx, cy - h, cx + w, cy, 
                                                           outline=fg, width=1, tags=tags)
                    self.canvas_labels[sid] = i
                    
                    # Centered text in shape
                    tid = self.editor_canvas.create_text(cx + w/2, cy - h/2, text=ld['name'], fill=fg, 
                                                       font=(font_fam, font_size, "bold"), anchor="center", tags=tags)
                    self.canvas_labels[tid] = i
                else:
                    # Standard text label
                    tid = self.editor_canvas.create_text(cx, cy, text=ld['name'], fill=fg, 
                                                       font=(font_fam, font_size, "bold"), anchor="sw", tags=tags)
                    self.canvas_labels[tid] = i
            except Exception as e:
                print(f"Error rendering label on canvas: {e}")

    def on_canvas_click(self, event):
        if not self.editor_canvas or not self.editor_canvas.winfo_exists(): return
        
        # Ensure focus is on canvas for keyboard shortcuts
        try:
            self.editor_canvas.focus_set()
        except: pass
        
        # Adjust for scroll position
        cx = self.editor_canvas.canvasx(event.x)
        cy = self.editor_canvas.canvasy(event.y)
        
        mode = self.tool_mode.get()
        
        if mode == "Select":
            # Better selection detection: find closest with a generous halo
            item_list = self.editor_canvas.find_closest(cx, cy, halo=10)
            item = item_list[0] if item_list else None
            
            # Verify if it's draggable
            if item and "draggable" not in self.editor_canvas.gettags(item):
                # Fallback to overlapping for more precision on small things
                items = self.editor_canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5)
                item = next((i for i in reversed(items) if "draggable" in self.editor_canvas.gettags(i)), None)
            
            if item:
                self.drag_data["item"] = item
                # Store absolute click position relative to canvas
                self.drag_data["start_cx"] = cx
                self.drag_data["start_cy"] = cy
                
                # Select it in listbox too
                idx = self.canvas_labels.get(item, -1)
                if idx != -1:
                    self.selected_label_index = idx
                    self.label_listbox.selection_clear(0, tk.END)
                    self.label_listbox.selection_set(idx)
                    self.on_select_label(None)
                return
        elif mode == "Text":
            self.selected_label_index = -1
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, f"{(cx / self.zoom_level):.1f}")
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, f"{((self.canvas_h - cy) / self.zoom_level):.1f}")
            self.shape_var.set("None")
            self.entry_w.delete(0, tk.END)
            self.entry_w.insert(0, "0")
            self.entry_h.delete(0, tk.END)
            self.entry_h.insert(0, "0")
            
            # Immediately create a placeholder text if name is empty
            if not self.entry_name.get().strip():
                count = len(self.label_data) + 1
                self.entry_name.insert(0, f"Text_{count}")
            
            # Create the label immediately so it can be dragged
            self.update_label()
            
            # Now find the item we just created to start dragging it
            self.render_canvas_labels()
            self.selected_label_index = len(self.label_data) - 1
            self.populate_list()
            self.label_listbox.selection_set(self.selected_label_index)
            
            # Try to start dragging it immediately
            # Use find_closest with a halo to ensure we grab the text we just made
            item = self.editor_canvas.find_closest(cx, cy, halo=5)
            if item and "draggable" in self.editor_canvas.gettags(item[0]):
                self.drag_data["item"] = item[0]
                self.drag_data["start_cx"] = cx
                self.drag_data["start_cy"] = cy
            
            # Focus text entry for easy renaming
            self.entry_name.focus_set()
            self.entry_name.select_range(0, tk.END)
        else:
            # Rectangle or Circle
            self.selected_label_index = -1
            self.shape_var.set(mode)
            self.drag_data["draw_start_x"] = cx
            self.drag_data["draw_start_y"] = cy
            self.drag_data["drawing"] = True
            
            fg = self.btn_color.cget("fg") or TEXT_PRIMARY
            if mode == "Rectangle":
                self.drag_data["draw_item"] = self.editor_canvas.create_rectangle(cx, cy, cx, cy, outline=fg, dash=(2, 2))
            else:
                self.drag_data["draw_item"] = self.editor_canvas.create_oval(cx, cy, cx, cy, outline=fg, dash=(2, 2))

    def on_canvas_right_click(self, event):
        if not self.editor_canvas or not self.editor_canvas.winfo_exists(): return
        cx = self.editor_canvas.canvasx(event.x)
        cy = self.editor_canvas.canvasy(event.y)
        
        # Find if we clicked a label
        items = self.editor_canvas.find_overlapping(cx-2, cy-2, cx+2, cy+2)
        item = None
        for i in reversed(items):
            if "draggable" in self.editor_canvas.gettags(i):
                item = i
                break
        
        if item:
            idx = self.canvas_labels.get(item, -1)
            if idx != -1:
                self.selected_label_index = idx
                self.label_listbox.selection_clear(0, tk.END)
                self.label_listbox.selection_set(idx)
                self.on_select_label(None)
                
                # Highlight and focus name entry for renaming
                self.entry_name.focus_set()
                self.entry_name.select_range(0, tk.END)

    def on_canvas_drag(self, event):
        if not self.editor_canvas or not self.editor_canvas.winfo_exists(): return
            
        try:
            cx = self.editor_canvas.canvasx(event.x)
            cy = self.editor_canvas.canvasy(event.y)
            
            if self.drag_data.get("drawing") and self.drag_data.get("draw_item"):
                # Handle shape drawing
                start_x = self.drag_data["draw_start_x"]
                start_y = self.drag_data["draw_start_y"]
                
                # Canvas coordinates
                x1, y1 = min(start_x, cx), min(start_y, cy)
                x2, y2 = max(start_x, cx), max(start_y, cy)
                
                self.editor_canvas.coords(self.drag_data["draw_item"], x1, y1, x2, y2)
                
                # Update W/H entries
                self.entry_x.delete(0, tk.END)
                self.entry_x.insert(0, f"{(x1 / self.zoom_level):.1f}")
                self.entry_y.delete(0, tk.END)
                self.entry_y.insert(0, f"{((self.canvas_h - y2) / self.zoom_level):.1f}")
                
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, f"{((x2-x1) / self.zoom_level):.0f}")
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, f"{((y2-y1) / self.zoom_level):.0f}")
                return

            if self.tool_mode.get() != "Select": return
            if not self.drag_data.get("item"): return
            
            delta_x = cx - self.drag_data["start_cx"]
            delta_y = cy - self.drag_data["start_cy"]
            
            # Find the group tag to move both shape and text
            tags = self.editor_canvas.gettags(self.drag_data["item"])
            group_tag = next((t for t in tags if t.startswith("label_group_")), None)
            
            if group_tag:
                self.editor_canvas.move(group_tag, delta_x, delta_y)
            else:
                self.editor_canvas.move(self.drag_data["item"], delta_x, delta_y)
            
            self.drag_data["start_cx"] = cx
            self.drag_data["start_cy"] = cy
            
            # Update entries in real-time
            idx = self.canvas_labels.get(self.drag_data["item"])
            if idx is not None:
                ld = self.label_data[idx]
                ld['x'] += delta_x / self.zoom_level
                ld['y'] -= delta_y / self.zoom_level # Inverted Y
                
                self.entry_x.delete(0, tk.END)
                self.entry_x.insert(0, f"{ld['x']:.1f}")
                self.entry_y.delete(0, tk.END)
                self.entry_y.insert(0, f"{ld['y']:.1f}")
        except: pass

    def on_canvas_release(self, event):
        if self.drag_data.get("drawing"):
            if "draw_item" in self.drag_data and self.drag_data["draw_item"]:
                self.editor_canvas.delete(self.drag_data["draw_item"])
            self.drag_data["drawing"] = False
            self.drag_data["draw_item"] = None
            
            # If width or height is too small, just treat as a click to position
            try:
                w = float(self.entry_w.get())
                h = float(self.entry_h.get())
                if w < 5 or h < 5:
                    return
            except: return

            # Finalize the new label coordinates and dimensions
            # Automatically set a name if empty
            if not self.entry_name.get().strip():
                count = len(self.label_data) + 1
                self.entry_name.insert(0, f"Label_{count}")
            
            self.save_history()
            # Trigger update to list
            self.update_label()
            
            # Start dragging the new shape immediately
            self.render_canvas_labels()
            self.selected_label_index = len(self.label_data) - 1
            self.populate_list()
            self.label_listbox.selection_set(self.selected_label_index)
            
        elif self.drag_data.get("item"):
            self.save_history()

        self.drag_data["item"] = None
        try:
            self.populate_list() # Sync listbox
        except: pass

    def on_select_label(self, event):
        if not hasattr(self, 'label_listbox') or not self.label_listbox.winfo_exists():
            return
        selection = self.label_listbox.curselection()
        if selection:
            self.selected_label_index = selection[0]
            if self.selected_label_index >= len(self.label_data): return
            
            ld = self.label_data[self.selected_label_index]
            try:
                self.entry_name.delete(0, tk.END)
                self.entry_name.insert(0, ld['name'])
                self.entry_x.delete(0, tk.END)
                self.entry_x.insert(0, f"{ld['x']:.1f}")
                self.entry_y.delete(0, tk.END)
                self.entry_y.insert(0, f"{ld['y']:.1f}")
                self.btn_color.config(fg=ld['fg'])
                
                # New shape fields
                self.shape_var.set(ld.get('shape', 'None') or 'None')
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, str(ld.get('w', 0)))
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, str(ld.get('h', 0)))
                
                # New font fields
                self.font_var.set(ld.get('font', 'Segoe UI'))
                self.size_var.set(str(ld.get('size', 9)))
                
                self.render_canvas_labels() # Redraw to highlight selected
            except: pass

    def pick_color(self):
        if not hasattr(self, 'entry_name') or not self.entry_name.winfo_exists(): return
        
        # Get current color for initialcolor, handle empty/default
        curr_fg = self.btn_color.cget("fg")
        if not curr_fg or curr_fg == TEXT_PRIMARY:
            curr_fg = "#ffffff" # Fallback to white for picker
            
        color = colorchooser.askcolor(title="Choose Label Color", initialcolor=curr_fg)[1]
        if color:
            try:
                self.btn_color.config(fg=color)
            except: pass

    def update_label(self, skip_history=False):
        if not hasattr(self, 'entry_name') or not self.entry_name.winfo_exists(): return
        name = self.entry_name.get()
        if not name: return

        try:
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            w = float(self.entry_w.get())
            h = float(self.entry_h.get())
            fg = self.btn_color.cget("fg")
            shape = self.shape_var.get()
            font_fam = self.font_var.get()
            font_size = self.size_var.get()
        except ValueError:
            return

        if fg == TEXT_PRIMARY: # Default
             fg = "" # Will be saved as blank in file which defaults to TEXT_PRIMARY

        new_data = {
            "name": name, "x": x, "y": y, 
            "fg": fg if fg else TEXT_PRIMARY,
            "shape": shape if shape != "None" else "",
            "w": w, "h": h,
            "font": font_fam,
            "size": font_size
        }

        if not skip_history:
            self.save_history()
        
        if self.selected_label_index >= 0 and self.selected_label_index < len(self.label_data):
            self.label_data[self.selected_label_index] = new_data
        else:
            self.label_data.append(new_data)
            self.selected_label_index = len(self.label_data) - 1
        
        self.populate_list()
        self.render_canvas_labels()

    def delete_label(self):
        if self.selected_label_index >= 0:
            self.save_history()
            del self.label_data[self.selected_label_index]
            self.populate_list()
            self.render_canvas_labels()
            self.selected_label_index = -1
            try:
                self.entry_name.delete(0, tk.END)
                self.entry_x.delete(0, tk.END)
                self.entry_y.delete(0, tk.END)
            except: pass

    def clear_all_labels(self):
        from tkinter import messagebox
        if messagebox.askyesno("Clear All", f"Are you sure you want to delete ALL labels for the {self.current_window_key} window?"):
            self.save_history()
            self.label_data = []
            self.populate_list()
            self.render_canvas_labels()
            self.selected_label_index = -1
            try:
                self.entry_name.delete(0, tk.END)
                self.entry_x.delete(0, tk.END)
                self.entry_y.delete(0, tk.END)
            except: pass

    def save_history(self):
        import copy
        # Keep last 50 states
        self.history.append(copy.deepcopy(self.label_data))
        if len(self.history) > 50:
            self.history.pop(0)

    def undo_action(self):
        if not self.history: return
        self.label_data = self.history.pop()
        self.populate_list()
        self.render_canvas_labels()
        self.selected_label_index = -1
        try:
            self.entry_name.delete(0, tk.END)
            self.entry_x.delete(0, tk.END)
            self.entry_y.delete(0, tk.END)
        except: pass

    def update_canvas_scaling(self):
        if not hasattr(self, 'editor_canvas') or not self.editor_canvas.winfo_exists():
            return
            
        # Cancel any pending resize update
        if hasattr(self, "_resize_timer") and self._resize_timer:
            try:
                self.window.after_cancel(self._resize_timer)
            except: pass
        
        # Debounce the scaling update during resize
        self._resize_timer = self.window.after(100, self._perform_canvas_scaling)

    def _perform_canvas_scaling(self):
        if not self.window or not self.window.winfo_exists(): return
        if not hasattr(self, 'editor_canvas') or not self.editor_canvas.winfo_exists(): return

        opts = self.window_options[self.current_window_key]
        img_w, img_h = opts["size"]
        
        self.canvas_w = img_w * self.zoom_level
        self.canvas_h = img_h * self.zoom_level
        try:
            self.editor_canvas.config(scrollregion=(0, 0, self.canvas_w, self.canvas_h))
            self.editor_canvas.update_idletasks()
        except: pass
        
        # Trigger re-render to ensure labels are at correct positions after scrollregion change
        self.render_canvas_labels()
