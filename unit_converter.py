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
    # Use built-in 'clam' for consistency
    style.theme_use("clam")
    if theme == "light":
        bg = "#f6f8fb"
        card_bg = "#ffffff"
        fg = "#222222"
        subtle = "#6b7280"
        accent = "#2563eb"
        entry_bg = "#ffffff"
        tree_bg_even = "#ffffff"
        tree_bg_odd = "#f3f4f6"
    else:
        bg = "#111827"
        card_bg = "#1f2937"
        fg = "#e5e7eb"
        subtle = "#9ca3af"
        accent = "#60a5fa"
        entry_bg = "#111827"
        tree_bg_even = "#1f2937"
        tree_bg_odd = "#111827"

    root.configure(bg=bg)
    card.configure(style="Card.TFrame")
    style.configure("Card.TFrame", background=card_bg, relief="flat")
    style.configure("TFrame", background=card_bg)
    style.configure("TLabel", background=card_bg, foreground=fg, font=("Segoe UI", 11))
    style.configure("Title.TLabel", background=card_bg, foreground=fg, font=("Segoe UI", 18, "bold"))
    style.configure("Subtle.TLabel", background=card_bg, foreground=subtle)
    style.configure("TButton", font=("Segoe UI", 11), padding=8)
    style.map("TButton", foreground=[("disabled", subtle)], background=[("active", accent)])
    style.configure("Accent.TButton", padding=10)
    style.configure("TEntry", fieldbackground=entry_bg)
    style.configure("TCombobox", fieldbackground=entry_bg)
    style.configure("Status.TLabel", background=bg, foreground=subtle)

    # Treeview theme (for history)
    style.configure("Treeview",
                    background=tree_bg_even,
                    fieldbackground=tree_bg_even,
                    foreground=fg,
                    rowheight=26,
                    bordercolor="#d1d5db" if theme == "light" else "#374151")
    style.configure("Treeview.Heading",
                    background=card_bg,
                    foreground=fg,
                    font=("Segoe UI", 10, "bold"))
    # Row colors applied via tags when inserting rows
    tree_colors["even"] = tree_bg_even
    tree_colors["odd"] = tree_bg_odd

# ===============================
# UI Behaviors
# ===============================
def validate_number(action, value_if_allowed):
    if action == "0":  # deletion always ok
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

        # Convert to base, then to target
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
    # Re-convert with swapped units if there is a value
    if value_var.get().strip() != "":
        convert()

def clear_all(event=None):
    value_var.set("")
    result_var.set("—")
    status_var.set("Cleared.")

def show_history():
    hist = tk.Toplevel(root)
    hist.title("Conversion History")
    hist.geometry("900x520")
    hist.configure(bg=root["bg"])

    wrapper = ttk.Frame(hist, padding=16, style="Card.TFrame")
    wrapper.pack(fill="both", expand=True, padx=12, pady=12)

    # Search Row
    row = ttk.Frame(wrapper)
    row.pack(fill="x", pady=(0, 10))

    ttk.Label(row, text="Search").pack(side="left", padx=(0, 8))
    search_text = tk.StringVar()
    search_entry = ttk.Entry(row, textvariable=search_text, width=30)
    search_entry.pack(side="left")
    search_by = ttk.Combobox(row, values=["All", "Input", "From Unit", "To Unit", "Result", "Category ID", "Timestamp"], width=14, state="readonly")
    search_by.current(0)
    search_by.pack(side="left", padx=8)
    ttk.Button(row, text="Search", command=lambda: load_history(tree, search_text.get(), search_by.get()), style="Accent.TButton").pack(side="left", padx=(6, 0))

    # Action Row - Clear History
    action_row = ttk.Frame(wrapper)
    action_row.pack(fill="x", pady=(0, 10))
    def clear_history():
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            with sqlite3.connect(DB_FILE) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM ConversionHistory")
                conn.commit()
            load_history(tree)
            messagebox.showinfo("History Cleared", "All conversion history has been deleted.")
    ttk.Button(action_row, text="Clear History", command=clear_history, style="Accent.TButton").pack(side="left")

    # Treeview
    cols = ("ID", "Input", "From", "To", "Result", "Category ID", "Timestamp")
    tree = ttk.Treeview(wrapper, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        w = 90 if col not in ("Timestamp", "Result") else 160
        tree.column(col, width=w, anchor="center")
    tree.pack(fill="both", expand=True)

    yscroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=yscroll.set)
    yscroll.place(in_=tree, relx=1.0, x=0, y=0, relheight=1.0, anchor="ne")

    # Load initial
    load_history(tree)
    search_entry.focus()

def load_history(tree, query="", selected="All"):
    for item in tree.get_children():
        tree.delete(item)

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM ConversionHistory ORDER BY timestamp DESC")
        rows = cur.fetchall()

    query = (query or "").lower()
    col_map = {
        "ID": 0, "Input": 1, "From Unit": 2, "To Unit": 3,
        "Result": 4, "Category ID": 5, "Timestamp": 6
    }

    filtered = []
    for row in rows:
        if not query:
            filtered.append(row)
            continue
        if selected == "All":
            if any(query in str(x).lower() for x in row):
                filtered.append(row)
        else:
            idx = col_map[selected]
            if query in str(row[idx]).lower():
                filtered.append(row)

    # Insert with zebra stripes
    for i, r in enumerate(filtered):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=r, tags=(tag,))
    tree.tag_configure("even", background=tree_colors["even"])
    tree.tag_configure("odd", background=tree_colors["odd"])

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
root.geometry("560x560")
root.minsize(520, 520)

style = ttk.Style()
tree_colors = {"even": "#ffffff", "odd": "#f3f4f6"}
theme_var = tk.StringVar(value="light")

# Card container
card = ttk.Frame(root, padding=16, style="Card.TFrame")
card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

# Title
title = ttk.Label(card, text="🔄 Unit Converter", style="Title.TLabel")
title.grid(row=0, column=0, columnspan=3, pady=(4, 10), sticky="w")

# Category
ttk.Label(card, text="Category").grid(row=1, column=0, sticky="w", pady=(2, 2))
category = ttk.Combobox(card, state="readonly", width=26)
category.grid(row=2, column=0, sticky="we", padx=(0, 10))
category.bind("<<ComboboxSelected>>", update_units)

# From / To with swap
ttk.Label(card, text="From").grid(row=3, column=0, sticky="w", pady=(10, 2))
from_unit = ttk.Combobox(card, state="readonly")
from_unit.grid(row=4, column=0, sticky="we", padx=(0, 10))

swap_btn = ttk.Button(card, text="↔ Swap", command=swap_units)
swap_btn.grid(row=4, column=1, sticky="we", padx=4)

ttk.Label(card, text="To").grid(row=3, column=2, sticky="w", pady=(10, 2))
to_unit = ttk.Combobox(card, state="readonly")
to_unit.grid(row=4, column=2, sticky="we", padx=(10, 0))

# Value
ttk.Label(card, text="Value").grid(row=5, column=0, sticky="w", pady=(14, 2))
value_var = tk.StringVar()
vcmd = (root.register(validate_number), "%d", "%P")
value_entry = ttk.Entry(card, textvariable=value_var, validate="key", validatecommand=vcmd)
value_entry.grid(row=6, column=0, columnspan=3, sticky="we")

# Buttons row
btn_row = ttk.Frame(card)
btn_row.grid(row=7, column=0, columnspan=3, sticky="we", pady=(16, 8))
convert_btn = ttk.Button(btn_row, text="Convert", command=convert, style="Accent.TButton")
convert_btn.pack(side="left")
clear_btn = ttk.Button(btn_row, text="Clear", command=clear_all)
clear_btn.pack(side="left", padx=8)
hist_btn = ttk.Button(btn_row, text="History", command=show_history)
hist_btn.pack(side="left", padx=8)
theme_btn = ttk.Button(btn_row, text="Toggle Theme", command=toggle_theme)
theme_btn.pack(side="right")

# Result (Copy button removed)
ttk.Label(card, text="Result").grid(row=8, column=0, sticky="w", pady=(8, 2))
result_var = tk.StringVar(value="—")
result_label = ttk.Label(card, textvariable=result_var, font=("Segoe UI", 14, "bold"))
result_label.grid(row=9, column=0, columnspan=3, sticky="w")

# Status bar
status_var = tk.StringVar(value="Ready.")
status_bar = ttk.Label(root, textvariable=status_var, style="Status.TLabel", anchor="w")
status_bar.pack(side="bottom", fill="x", padx=10, pady=6)

# Grid weights for responsiveness
card.columnconfigure(0, weight=1)
card.columnconfigure(1, weight=0, minsize=84)
card.columnconfigure(2, weight=1)

# Populate initial data
cats = get_categories()
category["values"] = cats
if cats:
    category.set(cats[0])
    update_units()

# Key bindings
root.bind("<Return>", convert)
root.bind("<Control-h>", lambda e: show_history())
root.bind("<Control-H>", lambda e: show_history())
root.bind("<Control-l>", clear_all)
root.bind("<Control-L>", clear_all)
root.bind("<Control-j>", swap_units)
root.bind("<Control-J>", swap_units)

# Apply initial theme and start
apply_theme(theme_var.get())
value_entry.focus()
root.mainloop()
