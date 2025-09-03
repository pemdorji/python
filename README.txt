Unit Converter Application
==========================

Overview:
---------
The Unit Converter is a desktop application built with Python, Tkinter, and SQLite. 
It allows users to convert values between different units in categories such as:
- Length
- Weight
- Temperature

The app stores a history of conversions and allows searching or clearing it. 
It also supports light and dark themes for user preference.

Features:
---------
1. Category-based conversion.
2. Convert between units with linear or offset formulas (e.g., Celsius to Kelvin).
3. View conversion history with search and filtering options.
4. Clear all history with a single click.
5. Light/Dark mode toggle.
6. Keyboard support: press Enter to perform conversion.

Database:
---------
- Uses SQLite (converter.db) for storage.
- Tables: Categories, Units, ConversionHistory.
- Automatically initializes with sample data if empty.

How to Run:
-----------
1. Ensure lates python version is installed.
2. Make sure Tkinter is available (usually included in Python).
3. Run the script from the terminal or an IDE:
   python converter.py
4. Use the GUI to select category, units, enter value, and convert.

Author:
-------
Pem Dorji
