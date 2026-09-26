import ctypes
import tkinter as tk
import tkinter.font as tkfont
from functools import partial

from calculator import Calculator, format_number

BG = "#ffffff"
PANEL = "#f3f3f3"
HOVER = "#e6e6e6"
NUM = ("#f0f0f0", "#e4e4e4", "#d6d6d6")
FN = ("#d9d9d9", "#cccccc", "#bdbdbd")
ACCENT = ("#1a1a1a", "#383838", "#000000")
TEXT = "#111111"
ACCENT_TEXT = "#ffffff"
MUTED = "#6b6b6b"
DISABLED = "#b5b5b5"

KEYPAD = [
    [("%", "percent", FN), ("CE", "ce", FN), ("C", "clear", FN), ("back", "back", FN)],
    [("¹⁄ₓ", "recip", FN), ("x²", "square", FN), ("²√x", "sqrt", FN), ("÷", "/", FN)],
    [("7", "7", NUM), ("8", "8", NUM), ("9", "9", NUM), ("×", "*", FN)],
    [("4", "4", NUM), ("5", "5", NUM), ("6", "6", NUM), ("−", "-", FN)],
    [("1", "1", NUM), ("2", "2", NUM), ("3", "3", NUM), ("+", "+", FN)],
    [("⁺∕₋", "negate", NUM), ("0", "0", NUM), (".", ".", NUM), ("=", "=", ACCENT)],
]

KEYS = {
    "plus": "+", "KP_Add": "+", "minus": "-", "KP_Subtract": "-",
    "asterisk": "*", "KP_Multiply": "*", "slash": "/", "KP_Divide": "/",
    "Return": "=", "KP_Enter": "=", "equal": "=",
    "BackSpace": "back", "Escape": "clear", "Delete": "ce", "percent": "percent",
    "period": ".", "comma": ".", "KP_Decimal": ".",
    "r": "recip", "q": "square", "at": "sqrt", "F9": "negate",
}
DISABLED_ON_ERROR = {"percent", "recip", "square", "sqrt", "/", "*", "-", "+", "negate", "."}


class RoundButton(tk.Canvas):
    def __init__(self, master, text, command, colors, fg=TEXT, font=None, radius=5):
        super().__init__(master, width=1, height=1, bg=master["bg"], bd=0,
                         highlightthickness=0, cursor="hand2")
        self.text = text
        self.command = command
        self.colors = colors
        self.fg = fg
        self.font = font
        self.radius = radius
        self.enabled = True
        self.state = 0
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._set_state(1))
        self.bind("<Leave>", lambda e: self._set_state(0))
        self.bind("<ButtonPress-1>", lambda e: self._set_state(2))
        self.bind("<ButtonRelease-1>", self._release)

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        r = min(self.radius, w // 2, h // 2)
        x1, y1, x2, y2 = 1, 1, w - 2, h - 2
        points = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
                  x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
                  x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]
        color = self.colors[self.state]
        self.create_polygon(points, smooth=True, fill=color, outline=color)
        self.create_text(w / 2, h / 2, text=self.text, font=self.font,
                         fill=self.fg if self.enabled else DISABLED)

    def flash(self):
        if self.enabled:
            self._set_state(2)
            self.after(110, lambda: self._set_state(0))

    def set_enabled(self, enabled):
        if enabled != self.enabled:
            self.enabled = enabled
            self.state = 0
            self.configure(cursor="hand2" if enabled else "arrow")
            self.draw()

    def _set_state(self, state):
        self.state = state if self.enabled else 0
        self.draw()

    def _release(self, event):
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self._set_state(1 if inside else 0)
        if inside and self.enabled:
            self.command()


class TextButton(tk.Label):
    def __init__(self, master, text, command, font, hover=HOVER, **kwargs):
        super().__init__(master, text=text, font=font, bg=master["bg"], fg=TEXT,
                         cursor="hand2", **kwargs)
        self.command = command
        self.normal_bg = master["bg"]
        self.hover_bg = hover
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=self.normal_bg))
        self.bind("<Button-1>", lambda e: self.command())


class App:
    def __init__(self, root):
        self.root = root
        self.calc = Calculator()
        self.history_open = False
        self.buttons = {}

        families = set(tkfont.families())
        icon_family = next((f for f in ("Segoe Fluent Icons", "Segoe MDL2 Assets") if f in families), None)
        self.icon_font = (icon_family, 12) if icon_family else ("Segoe UI", 12)
        self.glyphs = {
            "back": "", "history": "", "trash": "",
        } if icon_family else {
            "back": "⌫", "history": "↺", "trash": "✕",
        }

        scale = root.winfo_fpixels("1i") / 96
        root.title("Calculator")
        root.configure(bg=BG)
        root.geometry(f"{int(340 * scale)}x{int(560 * scale)}")
        root.minsize(int(300 * scale), int(500 * scale))
        self.icon = make_icon()
        root.iconphoto(True, self.icon)

        self.actions = {
            "percent": self.calc.percent, "ce": self.calc.clear_entry, "clear": self.calc.clear,
            "back": self.calc.backspace, "recip": self.calc.reciprocal, "square": self.calc.square,
            "sqrt": self.calc.square_root, "negate": self.calc.negate, ".": self.calc.input_decimal,
            "=": self.calc.equals,
        }
        for op in "+-*/":
            self.actions[op] = partial(self.calc.set_operator, op)
        for digit in "0123456789":
            self.actions[digit] = partial(self.calc.input_digit, digit)

        self._build_header()
        self._build_display()
        self._build_body()
        self._build_history()

        root.bind("<Key>", self.on_key)
        root.bind("<MouseWheel>", self._on_wheel)
        self.refresh()

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=8, pady=(8, 0))
        TextButton(header, self.glyphs["history"], self.toggle_history, self.icon_font,
                   width=3, pady=6).pack(side="right")

    def _build_display(self):
        self.display = tk.Frame(self.root, bg=BG)
        self.display.pack(fill="x", padx=12, pady=(10, 4))
        self.expression_label = tk.Label(self.display, text="", anchor="e", bg=BG, fg=MUTED,
                                         font=("Segoe UI", 12))
        self.expression_label.pack(fill="x", padx=4)
        self.display_font = tkfont.Font(family="Segoe UI Semibold", size=40)
        result_box = tk.Frame(self.display, bg=BG, height=self.display_font.metrics("linespace"))
        result_box.pack(fill="x", padx=4)
        result_box.pack_propagate(False)
        self.result_label = tk.Label(result_box, text="0", anchor="e", bg=BG, fg=TEXT,
                                     font=self.display_font)
        self.result_label.pack(fill="both", expand=True)
        self.display.bind("<Configure>", lambda e: self._fit_display())

    def _build_body(self):
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        keypad = tk.Frame(self.body, bg=BG)
        keypad.pack(fill="both", expand=True)
        for row, keys in enumerate(KEYPAD):
            keypad.rowconfigure(row, weight=1, uniform="keys")
            for col, (label, action, colors) in enumerate(keys):
                keypad.columnconfigure(col, weight=1, uniform="keys")
                if action == "back":
                    label, font = self.glyphs["back"], self.icon_font
                elif action.isdigit() or action == ".":
                    font = ("Segoe UI Semibold", 15)
                elif action in "+-*/=":
                    font = ("Segoe UI", 17)
                else:
                    font = ("Segoe UI", 13)
                fg = ACCENT_TEXT if colors is ACCENT else TEXT
                button = RoundButton(keypad, label, partial(self.run, action), colors, fg=fg, font=font)
                button.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                self.buttons[action] = button

    def _build_history(self):
        self.history_panel = tk.Frame(self.body, bg=PANEL)
        tk.Label(self.history_panel, text="History", font=("Segoe UI Semibold", 12), bg=PANEL,
                 fg=TEXT, anchor="w").pack(fill="x", padx=14, pady=(12, 6))
        self.trash_button = TextButton(self.history_panel, self.glyphs["trash"], self.clear_history,
                                       self.icon_font, width=3, pady=6)
        self.trash_button.pack(side="bottom", anchor="e", padx=8, pady=8)

        self.history_canvas = tk.Canvas(self.history_panel, bg=PANEL, bd=0, highlightthickness=0)
        self.history_canvas.pack(fill="both", expand=True)
        self.history_list = tk.Frame(self.history_canvas, bg=PANEL)
        window = self.history_canvas.create_window(0, 0, window=self.history_list, anchor="nw")
        self.history_canvas.bind("<Configure>", lambda e: self.history_canvas.itemconfigure(window, width=e.width))
        self.history_list.bind("<Configure>", lambda e: self.history_canvas.configure(
            scrollregion=self.history_canvas.bbox("all")))

    def run(self, action):
        self.actions[action]()
        self.refresh()

    def refresh(self):
        calc = self.calc
        self.expression_label.configure(text=calc.expression)
        self._fit_display(calc.display)
        for action, button in self.buttons.items():
            button.set_enabled(not (calc.error and action in DISABLED_ON_ERROR))
        if self.history_open:
            self._render_history()

    def _fit_display(self, text=None):
        if text is not None:
            self.result_label.configure(text=text)
        text = self.result_label.cget("text")
        available = self.display.winfo_width() - 16
        if available <= 0:
            return
        size = 26 if self.calc.error else 40
        self.display_font.configure(size=size)
        while size > 12 and self.display_font.measure(text) > available:
            size -= 2
            self.display_font.configure(size=size)

    def on_key(self, event):
        if event.state & 0x4:
            key = event.keysym.lower()
            if key == "h":
                self.toggle_history()
            elif key == "c":
                self.root.clipboard_clear()
                self.root.clipboard_append(self.calc.display.replace(",", ""))
            elif key == "v":
                try:
                    pasted = self.root.clipboard_get()
                except tk.TclError:
                    pasted = ""
                if self.calc.paste(pasted):
                    self.refresh()
            return "break"

        if event.keysym == "Escape" and self.history_open:
            self.toggle_history()
            return "break"
        action = event.char if event.char.isdigit() else KEYS.get(event.keysym)
        if action:
            self._press(action)
            return "break"

    def _press(self, action):
        button = self.buttons.get(action)
        if button and not button.enabled:
            return
        if button:
            button.flash()
        self.run(action)

    def toggle_history(self):
        self.history_open = not self.history_open
        if self.history_open:
            self._render_history()
            self.history_panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.history_panel.lift()
        else:
            self.history_panel.place_forget()

    def clear_history(self):
        self.calc.clear_history()
        self._render_history()

    def _render_history(self):
        for child in self.history_list.winfo_children():
            child.destroy()
        self.history_canvas.yview_moveto(0)
        if not self.calc.history:
            tk.Label(self.history_list, text="There's no history yet", font=("Segoe UI", 11),
                     bg=PANEL, fg=MUTED, anchor="w").pack(fill="x", padx=14, pady=4)
            self.trash_button.pack_forget()
            return
        self.trash_button.pack(side="bottom", anchor="e", padx=8, pady=8)
        for index, (expression, value) in enumerate(self.calc.history):
            item = tk.Frame(self.history_list, bg=PANEL, cursor="hand2")
            item.pack(fill="x", padx=6, pady=1)
            labels = [
                tk.Label(item, text=expression, font=("Segoe UI", 11), bg=PANEL, fg=MUTED, anchor="e"),
                tk.Label(item, text=format_number(value), font=("Segoe UI Semibold", 20), bg=PANEL,
                         fg=TEXT, anchor="e"),
            ]
            for label in labels:
                label.pack(fill="x", padx=10)
            for widget in (item, *labels):
                widget.bind("<Enter>", partial(self._hover_item, item, labels, HOVER))
                widget.bind("<Leave>", partial(self._hover_item, item, labels, PANEL))
                widget.bind("<Button-1>", partial(self._use_history, index))

    def _hover_item(self, item, labels, color, event=None):
        for widget in (item, *labels):
            widget.configure(bg=color)

    def _use_history(self, index, event=None):
        self.calc.use_history(index)
        self.toggle_history()
        self.refresh()

    def _on_wheel(self, event):
        if self.history_open:
            self.history_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")


def make_icon():
    icon = tk.PhotoImage(width=32, height=32)
    icon.put("#1a1a1a", to=(3, 2, 29, 30))
    icon.put("#ffffff", to=(6, 5, 26, 11))
    for row in range(3):
        for col in range(3):
            x, y = 6 + col * 7, 14 + row * 5
            color = "#ffffff" if (row, col) == (2, 2) else "#8a8a8a"
            icon.put(color, to=(x, y, x + 5, y + 3))
    return icon


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
