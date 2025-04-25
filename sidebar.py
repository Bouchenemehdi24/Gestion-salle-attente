import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class Sidebar(ttk.Frame):
    def __init__(self, parent, width=240, theme_switcher=None, **kwargs):
        self.theme_switcher = theme_switcher
        super().__init__(parent, **kwargs)
        self.width = width
        self.buttons = {}
        self.selected = None
        self.style = ttk.Style()
        
        # Configure styles first
        self.setup_style()
        
        # Apply style using style configuration
        self.configure(style='Sidebar.TFrame')
        self['padding'] = (10, 20)
        
        # App logo/title
        title_frame = ttk.Frame(self, style='Sidebar.TFrame')
        title_frame.pack(fill='x', pady=(0, 25))
        
        ttk.Label(title_frame, 
                 text="Cabinet Médical",
                 style='SidebarTitle.TLabel').pack(pady=5)
        
        self.setup_ui()

    def setup_style(self):
        # Configure frame style with professional colors
        self.style.configure('Sidebar.TFrame', 
                       background='#FFFFFF')  # Clean white background
        
        # Configure title label style
        self.style.configure('SidebarTitle.TLabel',
                       background='#FFFFFF',
                       foreground='#00ACC1',  # Calm teal
                       font=('Segoe UI', 20, 'bold'))
        
        # Configure button styles for a clean medical look
        self.style.configure('Sidebar.TButton',
                       padding=(15, 10),
                       width=20,
                       font=('Segoe UI', 11),
                       background='#FFFFFF',
                       foreground='#111111',  # Dark text for pale background
                       anchor='w')  # Left-align text
                       
        # Selected button style with teal highlight
        self.style.configure('Sidebar.Selected.TButton',
                       background='#E0F7FA',  # Light teal background
                       foreground='#111111')  # Dark text for pale background
                       
        # Hover effect for buttons
        self.style.map('Sidebar.TButton',
                 background=[('active', '#F5F5F5')],  # Light gray on hover
                 foreground=[('active', '#00ACC1')])  # Teal text on hover
        
    def setup_ui(self):
        # Add spacer frame at the bottom
        spacer = ttk.Frame(self)
        spacer.pack(fill=tk.Y, expand=True)

        # Create a container frame for the bottom section
        self.bottom_frame = ttk.Frame(self, style='Sidebar.TFrame')
        self.bottom_frame.pack(side='bottom', fill='x', pady=10)
        
    def add_button(self, text, command, icon=None, required_roles=None):
        # Get current user from application context
        current_user = self.master.current_user if hasattr(self.master, 'current_user') else None
        
        # Skip button creation if role requirements not met
        if required_roles and (not current_user or current_user.role.lower() not in [r.lower() for r in required_roles]):
            return None

        btn = ttk.Button(
            self,
            text=f" {text}" if icon else text,
            style="Sidebar.TButton",
            command=lambda: self._handle_click(text, command)
        )
        btn.pack(fill='x', pady=1, padx=5)
        self.buttons[text] = btn
        return btn
        
    def _handle_click(self, text, command):
        # Deselect previous button
        if self.selected:
            self.buttons[self.selected].configure(style="Sidebar.TButton")
            
        # Select new button
        self.selected = text
        self.buttons[text].configure(style="Sidebar.Selected.TButton")
        
        # Execute command
        command()
