import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import logging

class ModernTheme:
    def __init__(self):
        # Professional medical color palette
        self.colors = {
            'primary': '#00ACC1',     # Calm Teal
            'secondary': '#4CAF50',   # Soft Green
            'surface': '#FFFFFF',     # Pure White
            'background': '#F5F5F5',  # Light Gray
            'text': '#37474F',       # Dark Blue-Gray
            'text_secondary': '#78909C', # Light Blue-Gray
            'accent': '#FF5722',      # Warm Orange
            'error': '#EF5350',       # Soft Red
            'warning': '#FFB74D',     # Soft Orange
            'success': '#66BB6A',     # Soft Green
            'card': '#FFFFFF',        # Card Background
            'hover': '#E0F7FA',      # Light Teal (Hover)
            'selected': '#B2EBF2'     # Selected State
        }
        
        # Font configurations
        self.fonts = {
            'title': ('Segoe UI', 22, 'bold'),
            'header': ('Segoe UI', 16, 'bold'),
            'body': ('Segoe UI', 11),
            'small': ('Segoe UI', 9)
        }

    def apply_theme(self, style):
        # Main application style
        style.configure('.',
                       background=self.colors['background'],
                       foreground=self.colors['text'],
                       font=self.fonts['body'])

        # Frames
        style.configure('Sidebar.TFrame', 
                       background=self.colors['surface'])
        style.configure('Content.TFrame', 
                       background=self.colors['background'])
        
        # Enhanced buttons with modern styling
        style.theme_use('clam')  # Enable advanced styling features
        
        # Primary button - Solid with subtle gradient
        style.configure('Primary.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       background=self.colors['primary'],
                       foreground='white',
                       padding=(25, 12),
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor='none',
                       relief='flat',
                       anchor='center',
                       bordercolor=self.darken_color(self.colors['primary'], 0.1),
                       darkcolor=self.darken_color(self.colors['primary'], 0.1),
                       lightcolor=self.colors['primary'],
                       borderradius=8)
        style.map('Primary.TButton',
                 background=[
                     ('active', self.darken_color(self.colors['primary'], 0.1)),
                     ('pressed', self.darken_color(self.colors['primary'], 0.2))
                 ],
                 lightcolor=[
                     ('pressed', self.darken_color(self.colors['primary'], 0.2)),
                     ('active', self.colors['primary'])
                 ])

        # Secondary button - Outlined with hover effect
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       background=self.colors['surface'],
                       foreground=self.colors['primary'],
                       padding=(25, 12),
                       borderwidth=2,
                       bordercolor=self.colors['primary'],
                       focusthickness=0,
                       relief='flat',
                       anchor='center',
                       borderradius=8)
        style.map('Secondary.TButton',
            background=[
                ('active', self.colors['hover']),
                ('pressed', self.darken_color(self.colors['surface'], 0.1))
            ],
            foreground=[
                ('active', self.darken_color(self.colors['primary'], 0.2)),
                ('pressed', self.darken_color(self.colors['primary'], 0.3))
            ]
        )
                       
        # Cards with subtle shadow effect
        style.configure('Card.TFrame',
                       background=self.colors['card'],
                       relief='solid',
                       borderwidth=1)
                       
        # Labels
        style.configure('Header.TLabel',
                       font=self.fonts['header'],
                       background=self.colors['surface'],
                       foreground=self.colors['text'])

        style.configure('Info.TLabel',
                       font=self.fonts['body'],
                       background=self.colors['surface'],
                       foreground=self.colors['text_secondary'])

        # List styling
        style.configure('Treeview',
                       background=self.colors['surface'],
                       fieldbackground=self.colors['surface'],
                       foreground=self.colors['text'],
                       rowheight=40,
                       font=self.fonts['body'],
                       bordercolor=self.colors['background'],
                       borderwidth=0)
        style.map('Treeview',
                 background=[('selected', self.colors['selected'])],
                 foreground=[('selected', self.colors['text'])])
        style.configure('Treeview.Heading',
                       background=self.colors['background'],
                       foreground=self.colors['text_secondary'],
                       font=self.fonts['small'],
                       padding=(15, 10),
                       relief='flat')

        # Entry fields with modern styling
        style.configure('TEntry',
                       fieldbackground=self.colors['surface'],
                       foreground=self.colors['text'],
                       padding=10,
                       bordercolor=self.colors['text_secondary'],
                       relief='flat',
                       font=self.fonts['body'])
        style.map('TEntry',
                 bordercolor=[('focus', self.colors['primary']),
                             ('hover', self.colors['text_secondary'])],
                 relief=[('focus', 'solid'),
                        ('!focus', 'flat')])

        # Notebook (tabs)
        style.configure('TNotebook',
                       background=self.colors['background'])
        style.configure('TNotebook.Tab',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       padding=[10, 5])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', '#FFFFFF')])

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import logging

class ModernUITheme:
    """
    A theme manager class that provides consistent modern styling for the application.
    This class handles styling for both Tkinter widgets and matplotlib charts.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Modern color palette
        self.primary_color = '#007BFF'  # Vibrant Blue
        self.secondary_color = '#28A745'  # Lighter Green
        self.accent_color = '#DC3545'  # More prominent Red
        self.background_color = '#F8F9FA'  # Even Lighter gray
        self.text_color = '#495057'  # Slightly lighter dark blue-gray
        
        # Chart colors
        self.chart_colors = [
            self.primary_color,
            self.secondary_color,
            self.accent_color,
            '#f1c40f',  # Yellow
            '#9b59b6',  # Purple
            '#1abc9c',  # Turquoise
            '#34495e'   # Dark gray
        ]
        
        # Font configurations
        self.title_font = ("Arial", 16, "bold")
        self.header_font = ("Arial", 14, "bold")
        self.text_font = ("Arial", 12)
        self.small_font = ("Arial", 10)
        
    def apply_to_window(self, window):
        """
        Apply the theme to a tkinter window and its children
        """
        try:
            # Configure the window
            window.configure(background=self.background_color)
            
            # Configure ttk styles
            style = ttk.Style(window)
            
            # Configure common elements
            style.configure('TFrame', background=self.background_color)
            style.configure('TLabel', background=self.background_color, foreground=self.text_color)
            style.configure('TButton', background=self.primary_color, foreground=self.text_color) # Changed from 'white'
            style.map('TButton', 
                     background=[('active', self.secondary_color), ('disabled', '#cccccc')],
                     foreground=[('disabled', '#999999')])
            
            # Configure entry fields
            style.configure('TEntry', fieldbackground='white', foreground=self.text_color)
            
            # Configure comboboxes
            style.configure('TCombobox', fieldbackground='white', background=self.background_color)
            
            # Configure notebooks (tabs)
            style.configure('TNotebook', background=self.background_color)
            style.configure('TNotebook.Tab', background=self.background_color, 
                           foreground=self.text_color, padding=[10, 2])
            style.map('TNotebook.Tab',
                     background=[('selected', self.primary_color)],
                     foreground=[('selected', self.text_color)]) # Changed from 'white'
            
            # Configure treeviews (tables)
            style.configure('Treeview', 
                          background='white',
                          foreground=self.text_color,
                          rowheight=25,
                          fieldbackground='white')
            style.map('Treeview',
                     background=[('selected', self.primary_color)],
                     foreground=[('selected', self.text_color)]) # Changed from 'white'
            style.configure('Treeview.Heading', 
                          background=self.background_color,
                          foreground=self.text_color,
                          font=self.header_font)
            
            self.logger.info("Applied modern UI theme to window")
            return True
        except Exception as e:
            self.logger.error(f"Error applying theme: {str(e)}")
            return False
    
    def configure_matplotlib(self):
        """
        Configure matplotlib to use the theme's styling
        """
        try:
            # Use a clean, modern style
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Set font family
            plt.rcParams['font.family'] = 'DejaVu Sans'
            
            # Set colors
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=self.chart_colors)
            
            # Set font sizes
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['figure.titlesize'] = 16
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
            
            # Set grid style
            plt.rcParams['grid.alpha'] = 0.3
            plt.rcParams['grid.linestyle'] = '--'
            
            # Set figure background
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['axes.facecolor'] = 'white'
            
            self.logger.info("Configured matplotlib with modern styling")
            return True
        except Exception as e:
            self.logger.error(f"Error configuring matplotlib: {str(e)}")
            return False
    
    def create_custom_widget(self, parent, widget_type, **kwargs):
        """
        Create a custom styled widget
        """
        try:
            # Set default styling based on widget type
            if widget_type == 'button':
                # Create a custom styled button
                button = tk.Button(parent, 
                                 bg=self.primary_color,
                                 fg=self.text_color, # Changed from 'white'
                                 activebackground=self.secondary_color,
                                 activeforeground=self.text_color, # Changed from 'white'
                                 relief=tk.RAISED,
                                 borderwidth=1,
                                 padx=10,
                                 pady=5,
                                 font=self.text_font,
                                 **kwargs)
                return button
                
            elif widget_type == 'label':
                # Create a custom styled label
                label = tk.Label(parent,
                               bg=self.background_color,
                               fg=self.text_color,
                               font=self.text_font,
                               **kwargs)
                return label
                
            elif widget_type == 'entry':
                # Create a custom styled entry
                entry = tk.Entry(parent,
                               bg='white',
                               fg=self.text_color,
                               insertbackground=self.text_color,  # Cursor color
                               relief=tk.SOLID,
                               borderwidth=1,
                               **kwargs)
                return entry
                
            elif widget_type == 'frame':
                # Create a custom styled frame
                frame = tk.Frame(parent,
                               bg=self.background_color,
                               relief=kwargs.pop('relief', tk.FLAT),
                               borderwidth=kwargs.pop('borderwidth', 0),
                               **kwargs)
                return frame
                
            else:
                self.logger.warning(f"Unknown widget type: {widget_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating custom widget: {str(e)}")
            return None

    def create_card_frame(self, parent, title=None, **kwargs):
        """
        Create a modern card-like frame with optional title
        """
        try:
            # Create the main card frame
            card = tk.Frame(parent,
                          bg='white',
                          relief=tk.RAISED,
                          borderwidth=1,
                          padx=15,
                          pady=15,
                          **kwargs)
            
            # If title is provided, add a title label
            if title:
                title_label = tk.Label(card,
                                     text=title,
                                     bg='white',
                                     fg=self.text_color,
                                     font=self.header_font)
                title_label.pack(anchor='w', pady=(0, 10))
            
            return card
        except Exception as e:
            self.logger.error(f"Error creating card frame: {str(e)}")
            return None

# Create a global theme instance for easy access
    def darken_color(self, color, factor=0.1):
        """Darken a hex color by specified factor"""
        rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(comp * (1 - factor))) for comp in rgb)
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'

# Create a global theme instance for easy access
theme = ModernUITheme()
