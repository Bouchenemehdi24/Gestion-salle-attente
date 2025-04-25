import json
import os
import tkinter as tk
from ui_theme import theme, ModernUITheme

CONFIG_FILE = "user_theme_config.json"

class ThemeSwitcher:
    def __init__(self, root):
        self.root = root
        self.current_theme = "light"
        self.light_theme = theme
        self.dark_theme = self.create_dark_theme()
        self.load_theme()

    def create_dark_theme(self):
        dark = ModernUITheme()
        # Override colors for dark theme
        dark.primary_color = '#1E88E5'  # Bright Blue
        dark.secondary_color = '#43A047'  # Green
        dark.accent_color = '#E53935'  # Red
        dark.background_color = '#121212'  # Dark background
        dark.text_color = '#E0E0E0'  # Light text
        dark.chart_colors = [
            dark.primary_color,
            dark.secondary_color,
            dark.accent_color,
            '#f1c40f',
            '#9b59b6',
            '#1abc9c',
            '#34495e'
        ]
        return dark

    def apply_theme(self):
        if self.current_theme == "light":
            self.light_theme.apply_to_window(self.root)
        else:
            self.dark_theme.apply_to_window(self.root)
        self.root.update_idletasks()

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        self.save_theme()

    def save_theme(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"theme": self.current_theme}, f)
        except Exception as e:
            print(f"Error saving theme config: {e}")

    def load_theme(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.current_theme = data.get("theme", "light")
            except Exception as e:
                print(f"Error loading theme config: {e}")
        self.apply_theme()
