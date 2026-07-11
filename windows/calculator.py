import tkinter as tk
import math
from windows.base_window import BasePopoutWindow
from constants import (
    WINDOW_BG, BORDER_COLOR, PANEL_DARK, TEXT_SECONDARY, TEXT_PRIMARY,
    ACCENT_BLUE, BUTTON_BG, BUTTON_HOVER, TEXT_ACCENT, TITLE_GRADIENT_END
)

class CalculatorWindow(BasePopoutWindow):
    def __init__(self, app):
        super().__init__(app, "Calculator", "CalculatorWindow", 320, 480, fixed_size=True)
        self.expression = ""

    def show(self, force_open=False):
        super().show(force_open)
        # Content container is only available after show() creates the window
        if not hasattr(self, 'calc_built') or not self.calc_built:
            self.build_calc_layout()
            self.calc_built = True

    def build_calc_layout(self):
        # Display Area
        display_frame = tk.Frame(self.content_container, bg=PANEL_DARK, padx=10, pady=10)
        display_frame.pack(fill=tk.X, pady=(0, 10))

        self.display_var = tk.StringVar(value="0")
        self.display_label = tk.Label(display_frame, textvariable=self.display_var, bg=PANEL_DARK, fg=TEXT_PRIMARY,
                                      font=("Consolas", 18, "bold"), anchor="e")
        self.display_label.pack(fill=tk.X)

        self.history_var = tk.StringVar(value="")
        self.history_label = tk.Label(display_frame, textvariable=self.history_var, bg=PANEL_DARK, fg=TEXT_SECONDARY,
                                       font=("Consolas", 9), anchor="e")
        self.history_label.pack(fill=tk.X)

        # Buttons Grid
        buttons_frame = tk.Frame(self.content_container, bg=WINDOW_BG)
        buttons_frame.pack(fill=tk.BOTH, expand=True)

        # Adjusting layout for more scientific buttons
        buttons = [
            ('sin', 0, 0), ('cos', 0, 1), ('tan', 0, 2), ('log', 0, 3), ('ln', 0, 4),
            ('sqrt', 1, 0), ('^', 1, 1), ('(', 1, 2), (')', 1, 3), ('C', 1, 4),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('/', 2, 3), ('DEL', 2, 4),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('*', 3, 3), ('pi', 3, 4),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('-', 4, 3), ('e', 4, 4),
            ('0', 5, 0), ('.', 5, 1), ('ans', 5, 2), ('+', 5, 3), ('=', 5, 4),
        ]

        for i in range(5):
            buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(6):
            buttons_frame.grid_rowconfigure(i, weight=1)

        for (text, r, c) in buttons:
            btn = tk.Button(buttons_frame, text=text, bg=BUTTON_BG, fg=TEXT_PRIMARY,
                            activebackground=BUTTON_HOVER, activeforeground=TEXT_ACCENT,
                            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2",
                            command=lambda t=text: self.on_button_click(t))
            btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
            btn.bind("<Enter>", lambda e: e.widget.configure(bg=BUTTON_HOVER))
            btn.bind("<Leave>", lambda e: e.widget.configure(bg=BUTTON_BG))

        self.last_ans = "0"

    def on_button_click(self, char):
        if char == '=':
            self.calculate()
        elif char == 'C':
            self.expression = ""
            self.display_var.set("0")
            self.history_var.set("")
        elif char == 'DEL':
            self.expression = self.expression[:-1]
            self.display_var.set(self.expression if self.expression else "0")
        elif char == 'ans':
            self.expression += self.last_ans
            self.display_var.set(self.expression)
        else:
            if char in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt']:
                self.expression += char + "("
            elif char == '^':
                self.expression += "**"
            elif char == 'pi':
                self.expression += str(math.pi)
            elif char == 'e':
                self.expression += str(math.e)
            else:
                self.expression += char
            self.display_var.set(self.expression)

    def calculate(self):
        try:
            expr = self.expression
            if not expr: return
            
            # Replace functions with math. equivalents
            safe_dict = {
                'sin': lambda x: math.sin(math.radians(float(x))),
                'cos': lambda x: math.cos(math.radians(float(x))),
                'tan': lambda x: math.tan(math.radians(float(x))),
                'log': lambda x: math.log10(float(x)),
                'ln': lambda x: math.log(float(x)),
                'sqrt': lambda x: math.sqrt(float(x)),
                'pi': math.pi,
                'e': math.e,
                'math': math
            }
            
            # Simple sanitization and eval
            result = eval(expr, {"__builtins__": None}, safe_dict)
            
            # Format result
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)
            
            self.history_var.set(self.expression + " =")
            self.display_var.set(str(result))
            self.last_ans = str(result)
            self.expression = str(result)
        except Exception as e:
            self.display_var.set("Error")
            self.expression = ""

    def close(self):
        super().close()
        self.calc_built = False
        if hasattr(self.app, 'calc_win'):
            self.app.calc_win = None

    def refresh(self, force=False):
        # Calculator doesn't need periodic data refresh
        if not self.window or self.window.state() == "withdrawn": return
        super().refresh(force=force)
