import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_FILE = "unit_converter.db"

# ===============================
# Database Setup
# ===============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Units (
        unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        unit_name TEXT NOT NULL,
        unit_symbol TEXT,
        conversion_factor REAL NOT NULL,
        offset REAL DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ConversionHistory (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_value REAL NOT NULL,
        from_unit TEXT NOT NULL,
        to_unit TEXT NOT NULL,
        result_value REAL NOT NULL,
        category_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Settings (
        setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
        theme_mode TEXT DEFAULT 'light',
        default_category INTEGER,
        FOREIGN KEY (default_category) REFERENCES Categories(category_id)
    );
    """)

    # Seed sample data if empty
    cur.execute("SELECT COUNT(*) FROM Categories")
    if cur.fetchone()[0] == 0:
        cur.executescript("""
        INSERT INTO Categories (category_name, description) VALUES
        ('Length', 'Units of distance and size'),
        ('Weight', 'Units of mass and weight'),
        ('Temperature', 'Units of temperature measurement');

        -- Length (base = meter)
        INSERT INTO Units (category_id, unit_name, unit_symbol, conversion_factor, offset) VALUES
        (1, 'Meter', 'm', 1.0, 0),
        (1, 'Kilometer', 'km', 1000.0, 0),
        (1, 'Centimeter', 'cm', 0.01, 0),
        (1, 'Mile', 'mi', 1609.34, 0);

        -- Weight (base = kilogram)
        INSERT INTO Units (category_id, unit_name, unit_symbol, conversion_factor, offset) VALUES
        (2, 'Kilogram', 'kg', 1.0, 0),
        (2, 'Gram', 'g', 0.001, 0),
        (2, 'Pound', 'lb', 0.453592, 0);

        -- Temperature (base = Kelvin)
        INSERT INTO Units (category_id, unit_name, unit_symbol, conversion_factor, offset) VALUES
        (3, 'Kelvin', 'K', 1.0, 0),
        (3, 'Celsius', '°C', 1.0, 273.15),
        (3, 'Fahrenheit', '°F', 0.5555555556, 255.3722222);
        """)
    conn.commit()
    conn.close()
# ===============================
# Data Access Helpers
# ===============================
def get_categories():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT category_name FROM Categories ORDER BY category_name")
        return [r[0] for r in cur.fetchall()]

def get_units(category_name):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.unit_name
            FROM Units u
            JOIN Categories c ON u.category_id = c.category_id
            WHERE c.category_name = ?
            ORDER BY u.unit_name
        """, (category_name,))
        return [r[0] for r in cur.fetchall()]

def get_conversion_data(unit_name):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT conversion_factor, offset, category_id FROM Units WHERE unit_name = ?", (unit_name,))
        return cur.fetchone()  # (factor, offset, category_id) or None

def save_history(inp, f, t, res, cat_id):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ConversionHistory (input_value, from_unit, to_unit, result_value, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (inp, f, t, res, cat_id))
        conn.commit()

# ===============================
# Styling
# ===============================
def apply_theme(theme="light"):
    style.theme_use("clam")
    if theme == "light":
        bg = "#f0f2f5"
        card_bg = "#ffffff"
        fg = "#222222"
        subtle = "#6b7280"
        accent = "#2563eb"
        entry_bg = "#ffffff"
    else:
        bg = "#111827"
        card_bg = "#1f2937"
        fg = "#e5e7eb"
        subtle = "#9ca3af"
        accent = "#60a5fa"
        entry_bg = "#111827"

    root.configure(bg=bg)
    style.configure("Card.TFrame", background=card_bg, relief="flat")
    style.configure("TLabel", background=card_bg, foreground=fg, font=("Segoe UI", 11))
    style.configure("Title.TLabel", background=card_bg, foreground=fg, font=("Segoe UI", 18, "bold"))
    style.configure("TButton", font=("Segoe UI", 11), padding=6)
    style.map("TButton", foreground=[("disabled", subtle)], background=[("active", accent)])
    style.configure("Convert.TButton", background="#22c55e", foreground="white")
    style.map("Convert.TButton", background=[("active", "#16a34a")])
    style.configure("Clear.TButton", background="#ef4444", foreground="white")
    style.map("Clear.TButton", background=[("active", "#dc2626")])
    style.configure("History.TButton", background="#8b5cf6", foreground="white")
    style.map("History.TButton", background=[("active", "#7c3aed")])
    style.configure("Theme.TButton", background="#fbbf24", foreground="white")
    style.map("Theme.TButton", background=[("active", "#f59e0b")])
    style.configure("Status.TLabel", background=bg, foreground=subtle)

# ===============================
# UI Behaviors
# ===============================
def validate_number(action, value_if_allowed):
    if action == "0":
        return True
    try:
        float(value_if_allowed)
        return True
    except ValueError:
        return False

def convert(event=None):
    try:
        if not from_unit.get() or not to_unit.get():
            messagebox.showinfo("Select Units", "Please choose both From and To units.")
            return
        text = value_var.get().strip()
        if text == "":
            messagebox.showinfo("Input Required", "Please enter a value to convert.")
            return

        input_val = float(text)
        f_data = get_conversion_data(from_unit.get())
        t_data = get_conversion_data(to_unit.get())
        if not f_data or not t_data:
            messagebox.showerror("Unit Error", "Could not load conversion data for the selected units.")
            return

        f_factor, f_offset, cat_id_f = f_data
        t_factor, t_offset, cat_id_t = t_data
        if cat_id_f != cat_id_t:
            messagebox.showerror("Category Mismatch", "Please choose units from the same category.")
            return

        base_val = (input_val * f_factor) + f_offset
        result = (base_val - t_offset) / t_factor

        result_var.set(f"{result:.6g} {to_unit.get()}")
        status_var.set(f"Converted at {datetime.now().strftime('%H:%M:%S')}")
        save_history(input_val, from_unit.get(), to_unit.get(), float(f"{result:.10f}"), cat_id_f)
    except Exception as e:
        messagebox.showerror("Conversion Error", str(e))

def update_units(event=None):
    cat = category.get()
    units = get_units(cat)
    from_unit["values"] = units
    to_unit["values"] = units
    if units:
        from_unit.set(units[0])
        to_unit.set(units[1] if len(units) > 1 else units[0])

def swap_units(event=None):
    if not from_unit.get() or not to_unit.get():
        return
    f = from_unit.get()
    t = to_unit.get()
    from_unit.set(t)
    to_unit.set(f)
    if value_var.get().strip() != "":
        convert()

def clear_all(event=None):
    value_var.set("")
    result_var.set("—")
    status_var.set("Cleared.")

def toggle_theme():
    current = theme_var.get()
    theme_var.set("dark" if current == "light" else "light")
    apply_theme(theme_var.get())

# ===============================
# App Bootstrap
# ===============================
init_db()

root = tk.Tk()
root.title("✨ Modern Unit Converter")
root.geometry("700x500")
root.minsize(680, 480)

style = ttk.Style()
theme_var = tk.StringVar(value="light")
root.configure(bg="#f0f2f5")

# Main card frame
main_card = ttk.Frame(root, padding=20, style="Card.TFrame")
main_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.92)

# Title
title = ttk.Label(main_card, text="🔄 Modern Unit Converter", style="Title.TLabel")
title.pack(pady=(0,20))

# Panels container
panels = ttk.Frame(main_card)
panels.pack(fill="both", expand=True)

# ===== Left Panel =====
left_panel = ttk.Frame(panels, style="Card.TFrame")
left_panel.pack(side="left", fill="both", expand=True, padx=(0,10))

ttk.Label(left_panel, text="Select Category").pack(anchor="w")
category = ttk.Combobox(left_panel, state="readonly")
category.pack(fill="x", pady=6)

units_frame = ttk.Frame(left_panel)
units_frame.pack(fill="x", pady=12)
from_unit = ttk.Combobox(units_frame, state="readonly", width=15)
from_unit.pack(side="left", expand=True, fill="x")
swap_btn = ttk.Button(units_frame, text="⇄", width=3, command=swap_units)
swap_btn.pack(side="left", padx=6)
to_unit = ttk.Combobox(units_frame, state="readonly", width=15)
to_unit.pack(side="left", expand=True, fill="x")

ttk.Label(left_panel, text="Enter Value").pack(anchor="w", pady=(10,0))
value_var = tk.StringVar()
vcmd = (root.register(validate_number), "%d", "%P")
value_entry = ttk.Entry(left_panel, textvariable=value_var, validate="key", validatecommand=vcmd, font=("Segoe UI",12))
value_entry.pack(fill="x", pady=6)

convert_btn = ttk.Button(left_panel, text="Convert", command=convert, style="Convert.TButton")
convert_btn.pack(fill="x", pady=12)

# ===== Right Panel =====
right_panel = ttk.Frame(panels, style="Card.TFrame")
right_panel.pack(side="left", fill="both", expand=True, padx=(10,0))

ttk.Label(right_panel, text="Result").pack(anchor="w")
result_var = tk.StringVar(value="—")
result_label = ttk.Label(right_panel, textvariable=result_var, font=("Segoe UI",20,"bold"), foreground="#2563eb")
result_label.pack(fill="both", expand=True, pady=12)

action_frame = ttk.Frame(right_panel)
action_frame.pack(fill="x", pady=10)
clear_btn = ttk.Button(action_frame, text="Clear", command=clear_all, style="Clear.TButton")
clear_btn.pack(side="left", expand=True, fill="x", padx=4)
hist_btn = ttk.Button(action_frame, text="History", command=lambda: messagebox.showinfo("Info","History not implemented"), style="History.TButton")
hist_btn.pack(side="left", expand=True, fill="x", padx=4)
theme_btn = ttk.Button(action_frame, text="🌙 Toggle Theme", command=toggle_theme, style="Theme.TButton")
theme_btn.pack(side="left", expand=True, fill="x", padx=4)

# Status Bar
status_var = tk.StringVar(value="Ready.")
status_bar = ttk.Label(root, textvariable=status_var, style="Status.TLabel", anchor="w")
status_bar.pack(side="bottom", fill="x", padx=10, pady=6)

# Initialize Data
cats = get_categories()
category["values"] = cats
if cats:
    category.set(cats[0])
    update_units()

root.bind("<Return>", convert)
root.bind("<Control-l>", clear_all)
root.bind("<Control-j>", swap_units)

apply_theme(theme_var.get())
value_entry.focus()
root.mainloop()
