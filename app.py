import tkinter as tk
import logging
from datetime import datetime, date, timedelta
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import Font
from accounting import AccountingManager
from database import DatabaseManager, DatabaseError, DatabaseOperationError, DatabaseConnectionError
from reports_manager import ReportsManager
from reports_tab import ReportsTab
from patient_list_dialog import PatientListDialog, PatientSelectionDialog
from logging_config import setup_logging
from babel.dates import format_date
from tkcalendar import DateEntry
from ttkthemes import ThemedTk
from ui_theme import theme

try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')  # Set French locale
except:
    try:
        locale.setlocale(locale.LC_ALL, 'fr_FR')
    except:
        pass  # If French locale is not available, use system default
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showwarning("Information", "Pour une meilleure interface, installez PIL: pip install Pillow")
    Image = None

# Simple tooltip class for Tkinter widgets
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        import logging
        if self.tipwindow or not self.text:
            return
        widget_type = type(self.widget).__name__
        has_bbox = hasattr(self.widget, "bbox")
        x = y = cy = 0
        if has_bbox:
            try:
                x, y, _, cy = self.widget.bbox("insert")
            except Exception as e:
                logging.getLogger("UserAction").warning(
                    f"Tooltip bbox('insert') failed for widget type {widget_type}: {e}"
                )
                x, y, cy = 0, 0, 0
        else:
            x, y, cy = 0, 0, 0
        x = x + self.widget.winfo_rootx() + 20
        y = y + self.widget.winfo_rooty() + cy + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ServiceSettingsDialog:
    # Keep original functionality, but saving will be handled by the main app based on role
    def __init__(self, parent, services):
        self.top = tk.Toplevel(parent)
        self.top.title("Paramètres des services")
        self.top.geometry("400x500")
        self.services = services.copy()
        self.original_services = services.copy()  # Keep original for comparison
        self.create_widgets()

        # Make dialog modal
        self.top.transient(parent)
        self.top.grab_set()

        # Add closing confirmation
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Service list frame
        list_frame = ttk.LabelFrame(self.top, text="Services disponibles", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Services list with sorting
        self.services_list = ttk.Treeview(list_frame,
                                        columns=("service", "price"),
                                        show="headings",
                                        height=10)
        self.services_list.heading("service", text="Service", command=lambda: self.sort_services("service"))
        self.services_list.heading("price", text="Prix (DA)", command=lambda: self.sort_services("price"))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.services_list.yview)
        self.services_list.configure(yscrollcommand=scrollbar.set)

        self.services_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection event
        self.services_list.bind('<<TreeviewSelect>>', self.on_select)
        # Inline editing event
        self.services_list.bind('<Double-1>', self.on_treeview_double_click)

        # Add/Edit frame
        edit_frame = ttk.LabelFrame(self.top, text="Ajouter/Modifier un service", padding="10")
        edit_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(edit_frame, text="Service:").grid(row=0, column=0, padx=5, pady=5)
        self.service_entry = ttk.Entry(edit_frame)
        self.service_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(edit_frame, text="Prix (DA):").grid(row=1, column=0, padx=5, pady=5)
        vcmd = (self.top.register(self.validate_price), '%P')
        self.price_entry = ttk.Entry(edit_frame, validate='key', validatecommand=vcmd)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        edit_frame.columnconfigure(1, weight=1)

        # Buttons frame
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Ajouter/Modifier",
                  command=self.add_update_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer",
                  command=self.delete_service).pack(side=tk.LEFT, padx=5)
        # Changed "Enregistrer" to "OK" - saving happens in main app
        ttk.Button(btn_frame, text="OK",
                  command=self.save_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.on_closing).pack(side=tk.RIGHT, padx=5)

        self.update_service_list()

        # Tooltips
        Tooltip(self.services_list, "Double-click a cell to edit the service name or price.")
        Tooltip(self.service_entry, "Enter the name of the service.")
        Tooltip(self.price_entry, "Enter the price in DA (must be a positive integer).")
        Tooltip(btn_frame.winfo_children()[0], "Add or update the service in the list.")
        Tooltip(btn_frame.winfo_children()[1], "Delete the selected service from the list.")
        Tooltip(btn_frame.winfo_children()[2], "Save changes and close the dialog.")
        Tooltip(btn_frame.winfo_children()[3], "Cancel and close the dialog without saving.")

        # For inline editing
        self._edit_entry = None
        self._edit_column = None
        self._edit_item = None

    def on_treeview_double_click(self, event):
        # Identify the row and column
        region = self.services_list.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.services_list.identify_row(event.y)
        col_id = self.services_list.identify_column(event.x)
        if not row_id or not col_id:
            return

        col = int(col_id.replace("#", "")) - 1
        if col not in (0, 1):
            return  # Only allow editing service or price

        # Get cell bbox
        bbox = self.services_list.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox

        # Get current value
        values = self.services_list.item(row_id, "values")
        current_value = values[col]

        # Create entry widget
        if self._edit_entry:
            self._edit_entry.destroy()
        self._edit_entry = tk.Entry(self.services_list)
        self._edit_entry.insert(0, current_value)
        self._edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_entry.focus_set()
        self._edit_column = col
        self._edit_item = row_id

        def on_confirm(event=None):
            new_value = self._edit_entry.get().strip()
            service, price = values
            if col == 0:
                # Editing service name
                if not new_value:
                    messagebox.showerror("Erreur", "Le nom du service est obligatoire", parent=self.top)
                    return
                if new_value != service and new_value.lower() in (s.lower() for s in self.services if s != service):
                    messagebox.showerror("Erreur", "Ce service existe déjà", parent=self.top)
                    return
                # Update key in dict
                self.services[new_value] = self.services.pop(service)
                self.update_service_list()
            else:
                # Editing price
                try:
                    price_val = int(new_value)
                    if price_val < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Erreur", "Le prix doit être un nombre positif", parent=self.top)
                    return
                self.services[service] = price_val
                self.update_service_list()
            self._edit_entry.destroy()
            self._edit_entry = None
            self._edit_column = None
            self._edit_item = None

        def on_cancel(event=None):
            if self._edit_entry:
                self._edit_entry.destroy()
                self._edit_entry = None
                self._edit_column = None
                self._edit_item = None

        self._edit_entry.bind("<Return>", on_confirm)
        self._edit_entry.bind("<FocusOut>", on_cancel)
        self._edit_entry.bind("<Escape>", on_cancel)

    def validate_price(self, value):
        """Validate price input to allow only positive integers"""
        if value == "":
            return True
        try:
            price = int(value)
            return price >= 0
        except ValueError:
            return False

    def sort_services(self, column):
        """Sort services list by column"""
        items = [(self.services_list.set(item, column), item)
                for item in self.services_list.get_children("")]

        items.sort(reverse=getattr(self, f"sort_{column}_reverse", False))
        setattr(self, f"sort_{column}_reverse", not getattr(self, f"sort_{column}_reverse", False))

        for index, (_, item) in enumerate(items):
            self.services_list.move(item, "", index)

    def on_select(self, event):
        """Handle service selection"""
        selection = self.services_list.selection()
        if selection:
            item = self.services_list.item(selection[0])
            service, price = item["values"]
            self.service_entry.delete(0, tk.END)
            self.service_entry.insert(0, service)
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, str(price))

    def update_service_list(self):
        """Update services list with current data"""
        self.services_list.delete(*self.services_list.get_children())
        for service, price in sorted(self.services.items()):
            self.services_list.insert("", tk.END, values=(service, price))

    def add_update_service(self):
        """Add or update a service in the dialog's internal list"""
        service = self.service_entry.get().strip()
        price = self.price_entry.get().strip()

        if not service or not price:
            messagebox.showerror("Erreur", "Le service et le prix sont obligatoires", parent=self.top)
            return

        try:
            price = int(price)
            if price < 0:
                raise ValueError("Prix négatif")
        except ValueError:
            messagebox.showerror("Erreur", "Le prix doit être un nombre positif", parent=self.top)
            return

        # Check for duplicate service names (case-insensitive)
        existing_services = {s.lower(): s for s in self.services.keys()}
        if service.lower() in existing_services and existing_services[service.lower()] != service:
            messagebox.showerror("Erreur", "Ce service existe déjà", parent=self.top)
            return

        self.services[service] = price
        self.update_service_list()
        self.service_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

    def delete_service(self):
        """Delete selected service from the dialog's internal list"""
        selection = self.services_list.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un service à supprimer", parent=self.top)
            return

        service = self.services_list.item(selection[0])["values"][0]
        if messagebox.askyesno("Confirmation",
                             f"Voulez-vous vraiment supprimer le service '{service}'?", parent=self.top):
            del self.services[service]
            self.update_service_list()
            self.service_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)

    def has_changes(self):
        """Check if there are unsaved changes"""
        return self.services != self.original_services

    def on_closing(self):
        """Handle dialog closing"""
        if self.has_changes():
            if messagebox.askyesno("Confirmation",
                                 "Des modifications non sauvegardées existent. "
                                 "Voulez-vous vraiment quitter sans sauvegarder?", parent=self.top):
                # Don't update self.services, just close
                self.top.destroy()
        else:
            self.top.destroy()

    def save_changes(self):
        """Closes the dialog, saving is handled by the caller."""
        # No confirmation needed here as saving is external
        self.top.destroy()


class PaymentDialog:
    def __init__(self, parent, patient, services_list):
        self.top = tk.Toplevel(parent)
        self.top.title("Paiement")
        self.top.geometry("400x600")

        self.patient = patient
        self.services_list = services_list
        self.selected_services = []
        self.total = 0
        self.service_vars = {}  # To store checkbox variables

        self.create_widgets()
        self.top.transient(parent)
        self.top.grab_set() # Make modal

    def create_widgets(self):
        # Header
        ttk.Label(self.top, text=f"Paiement pour: {self.patient}", style="Header.TLabel").pack(pady=10)

        # Services selection frame with scrollbar
        select_frame = ttk.LabelFrame(self.top, text="Sélectionner Services", padding="10")
        select_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create scrollable frame
        canvas = tk.Canvas(select_frame)
        scrollbar = ttk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add checkboxes for each service
        if self.services_list:
            # Sort services by name for better organization
            sorted_services = dict(sorted(self.services_list.items()))
            for service, price in sorted_services.items():
                # Create frame for each service
                service_frame = ttk.Frame(scrollable_frame)
                service_frame.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar()
                self.service_vars[service] = var

                cb = ttk.Checkbutton(service_frame,
                                   text=service,
                                   variable=var,
                                   command=self.calculate_total)
                cb.pack(side=tk.LEFT, padx=(5, 10))

                # Price label
                ttk.Label(service_frame,
                         text=f"{price} DA",
                         foreground='green').pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Label(scrollable_frame,
                     text="Aucun service disponible",
                     foreground='red').pack(pady=10)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Total frame
        self.total_frame = ttk.LabelFrame(self.top, text="Résumé", padding="10")
        self.total_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Confirmer paiement",
                  command=self.confirm, style="Success.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.cancel, style="Secondary.TButton").pack(side=tk.RIGHT, padx=5)

        # Initial calculation
        self.calculate_total()

    def calculate_total(self):
        for widget in self.total_frame.winfo_children():
            widget.destroy()

        self.selected_services = []
        self.total = 0

        for service, var in self.service_vars.items():
            if var.get():
                price = self.services_list[service]
                self.selected_services.append(service)
                self.total += price

                ttk.Label(self.total_frame, text=f"{service}:").pack(anchor=tk.W)
                ttk.Label(self.total_frame, text=f"{price} DA", style="Info.TLabel").pack(anchor=tk.E) # Use Info style

        ttk.Separator(self.total_frame, orient='horizontal').pack(fill='x', pady=5)
        ttk.Label(self.total_frame, text="Total:", style="Header.TLabel").pack(anchor=tk.W, pady=(5,0))
        ttk.Label(self.total_frame, text=f"{self.total} DA", style="Header.TLabel").pack(anchor=tk.E)

    def confirm(self):
        self.result = True
        self.top.destroy()

    def cancel(self):
        self.result = False

# --- Removed internal PatientListDialog class definition ---

class AutocompleteEntry(ttk.Entry):
    def __init__(self, parent, completevalues, **kwargs):
        super().__init__(parent, **kwargs)
        self.completevalues = completevalues
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = tk.StringVar()
            
        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Return>", self.selection)
        self.listbox = None
        self.hideid = None

    def changed(self, *args):
        if self.hideid:
            self.after_cancel(self.hideid)
        self.hideid = self.after(300, self.update_list)

    def update_list(self):
        if not self.var.get():
            if self.listbox:
                self.listbox.destroy()
                self.listbox = None
            return
        
        if not self.listbox:
            self.listbox = tk.Listbox(width=self["width"], height=4)
            # Fix the bbox error by getting widget position instead
            x = self.winfo_x()
            y = self.winfo_y() + self.winfo_height()
            self.listbox.place(x=x, y=y, width=self.winfo_width())
            
        search = self.var.get().lower()
        self.listbox.delete(0, tk.END)
        for item in self.completevalues:
            if search in item.lower():
                self.listbox.insert(tk.END, item)

    def selection(self, event):
        if self.listbox and self.listbox.size() > 0:
            if self.listbox.curselection():
                self.var.set(self.listbox.get(self.listbox.curselection()))
            else:
                self.var.set(self.listbox.get(0))
            self.listbox.destroy()
            self.listbox = None
            return "break"

from sidebar import Sidebar

import json
import os

class LoginDialog:
    CREDENTIALS_FILE = "user_credentials.json"

    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Connexion")
        self.db = db
        self.result = None
        self.save_password_var = tk.BooleanVar() # Variable for checkbox state

        # Center dialog
        window_width = 300
        window_height = 150
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.create_widgets()

        # Load saved credentials if any
        self.load_saved_credentials()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Username
        ttk.Label(main_frame, text="Utilisateur:").grid(row=0, column=0, sticky=tk.W)
        self.username = ttk.Entry(main_frame)
        self.username.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # Password
        ttk.Label(main_frame, text="Mot de passe:").grid(row=1, column=0, sticky=tk.W)
        self.password = ttk.Entry(main_frame, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Save Password Checkbox
        save_check = ttk.Checkbutton(main_frame, text="Enregistrer le mot de passe", variable=self.save_password_var)
        save_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20, sticky=tk.EW)  # Ensure frame expands

        # Apply dark text color to buttons for better contrast on pale backgrounds
        style = ttk.Style()
        style.configure('Login.TButton', foreground='#111111')

        ttk.Button(btn_frame, text="Connexion", command=self.login, style='Login.TButton').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel, style='Login.TButton').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Bind enter key
        self.password.bind('<Return>', lambda e: self.login())

        # Set a minimum size for the dialog to avoid clipping
        self.top.minsize(340, 180)  # Set a minimum size for the dialog

    def load_saved_credentials(self):
        if os.path.exists(self.CREDENTIALS_FILE):
            try:
                with open(self.CREDENTIALS_FILE, "r") as f:
                    data = json.load(f)
                    username = data.get("username", "")
                    password = data.get("password", "")
                    self.username.insert(0, username)
                    self.password.insert(0, password)
                    self.save_password_var.set(bool(username and password))
            except Exception as e:
                # Log error or ignore
                pass

    def save_credentials(self, username, password):
        try:
            with open(self.CREDENTIALS_FILE, "w") as f:
                json.dump({"username": username, "password": password}, f)
        except Exception as e:
            # Log error or ignore
            pass

    def clear_saved_credentials(self):
        if os.path.exists(self.CREDENTIALS_FILE):
            try:
                os.remove(self.CREDENTIALS_FILE)
            except Exception as e:
                # Log error or ignore
                pass

    def login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()

        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs", parent=self.top)
            return

        user = self.db.verify_user_credentials(username, password)
        if user:
            if self.save_password_var.get():
                self.save_credentials(username, password)
            else:
                self.clear_saved_credentials()
            self.result = user
            self.top.destroy()
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects", parent=self.top)
            self.password.delete(0, tk.END)

    def cancel(self):
        self.top.destroy()

class DoctorsWaitingRoomApp:
    def __init__(self, root):
        self.logger = logging.getLogger(__name__)
        self.root = root
        self.root.title("Cabinet Médical - Gestion")

        # Set application icon
        try:
            if os.path.exists("icon.png"):
                # Convert PNG to PhotoImage for the window icon
                icon = tk.PhotoImage(file="icon.png")
                self.root.iconphoto(True, icon)
            elif os.path.exists("app_icon.ico"):
                # Use ICO file directly if PNG is not available
                self.root.iconbitmap("app_icon.ico")
        except Exception as e:
            self.logger.warning(f"Failed to set application icon: {e}")

        # Initialize theme
        self.theme = theme
        
        # Apply the custom theme styles to the root window
        self.theme.apply_to_window(self.root)

        self.root.withdraw()  # Hide main window until login

        # Initialize theme switcher early
        from theme_switcher import ThemeSwitcher
        self.theme_switcher = ThemeSwitcher(root)
        self.theme_switcher.apply_theme()
        
        # Initialize colors with more vivid options
        self.colors = {
            'primary': '#2563EB',    # Vivid blue
            'secondary': '#4B5563',   # Dark gray
            'success': '#10B981',     # Vivid green
            'warning': '#F59E0B',     # Vivid orange
            'danger': '#DC2626',      # Vivid red
            'background': '#F3F4F6',  # Light gray background
            'surface': '#FFFFFF',     # Pure white
            'text': '#111827'         # Very dark gray, almost black
        }
        
        self.wait_colors = {
            'new': '#BFDBFE',      # Vivid light blue
            'waiting': '#FED7AA',   # Vivid light orange
            'long_wait': '#FEE2E2'  # Vivid light red
        }
        
        try:
            # Initialize database first
            self.db = DatabaseManager()
            
            # Check if any users exist, if not create default admin
            if not self.db.check_if_users_exist():
                self.db.add_user("admin", "admin123", "Doctor")
                messagebox.showinfo("Information", 
                    "Compte par défaut créé:\nUtilisateur: admin\nMot de passe: admin123")
            
            # Show login dialog
            self.show_login()
            
        except DatabaseError as e:
            self.logger.exception("Failed to initialize application")
            messagebox.showerror("Erreur Critique", 
                               "Impossible de démarrer l'application.")
            root.destroy()
            return
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_login(self):
        dialog = LoginDialog(self.root, self.db)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            self.current_user = dialog.result
            self.setup_application()
        else:
            self.root.destroy()
    
    def setup_application(self):
        """Initialize the main application after successful login"""
        self.root.deiconify()  # Show main window
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f6f7")
        self.search_results_listbox = None # Initialize search results listbox attribute
        
        # Initialize components
        self.accounting = AccountingManager()
        self.reports_manager = ReportsManager(self.db)
        self.waiting_queue = []
        self.visited_today = []
        self.with_doctor = None
        self.services = {}
        
        # Load data
        self.load_services()
        self.load_records()
        
        # Setup UI
        # self.setup_styles() # Theme is applied globally via ThemedTk, specific styles can be set if needed later
        self.setup_ui()
        
        # Status bar with logged in user
        self.status_var = tk.StringVar(value=f"Connecté en tant que: {self.current_user['username']}")
        self.status_bar = ttk.Label(self.root, 
                                  textvariable=self.status_var,
                                  relief=tk.SUNKEN,
                                  padding=(10, 5))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initialize attributes for dashboard stat labels
        self.stat_waiting_value_label = None
        self.stat_visited_value_label = None
        self.stat_avg_wait_value_label = None
        self.stat_payments_value_label = None
        
        # More frequent updates (every 2 seconds) for real-time feel
        self.update_interval = 2000  # 2 seconds
        
        # Initial update and schedule periodic refresh
        self.update_displays()  # Run once immediately
        self.schedule_next_update()  # Start the update cycle
        
        # Store update job ID for proper cleanup
        self.update_job = None

    def schedule_next_update(self):
        """Schedules the next call to update_displays."""
        self.update_displays()  # Update immediately
        # Schedule the next update and store the job ID
        if self.root.winfo_exists():
            self.update_job = self.root.after(self.update_interval, self.schedule_next_update)

    def load_records(self):
        """Load today's records from database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, v.called_at, v.checkout_at
                    FROM patients p
                    JOIN visits v ON p.patient_id = v.patient_id
                    WHERE date(v.date) = date('now') -- Get all visits for today
                    ORDER BY v.arrived_at ASC
                """)
                all_today_visits = cursor.fetchall()

                # Clear existing lists before repopulating
                self.waiting_queue.clear()
                self.visited_today.clear()
                self.with_doctor = None

                # Process all visits for today to determine status
                for visit in all_today_visits:
                    name = visit["name"]
                    called_at = visit["called_at"]
                    checkout_at = visit["checkout_at"]

                    if checkout_at:
                        # If checked out, add to visited_today (ensure no duplicates if multiple visits)
                        if name not in self.visited_today:
                            self.visited_today.append(name)
                    elif called_at:
                        # If called but not checked out, they are with the doctor
                        self.with_doctor = name
                    else:
                        # If not called and not checked out, they are waiting
                        if name not in self.waiting_queue: # Avoid duplicates if somehow registered twice
                            self.waiting_queue.append(name)

                self.logger.info(f"Loaded records: {len(self.waiting_queue)} waiting, "
                                 f"{1 if self.with_doctor else 0} with doctor, "
                                 f"{len(self.visited_today)} visited today.")
                
        except Exception as e:
            self.logger.exception("Error loading records")
            messagebox.showerror("Erreur", 
                               "Impossible de charger les données du jour")

    def save_records(self):
        """Save patient records to file."""
        with open(self.records_file, 'w') as file:
            json.dump(self.records, file, indent=4)

    def load_services(self):
        """Load services from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, price FROM services")
            services = cursor.fetchall()
            
            if not services:  # If no services exist, add defaults
                default_services = {
                    "Consultation": 500,
                    "Blood Test": 1000,
                    "X-Ray": 1500
                }
                for name, price in default_services.items():
                    cursor.execute(
                        "INSERT INTO services (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                conn.commit()
                self.services = default_services
            else:
                self.services = {row['name']: row['price'] for row in services}

    def save_services(self):
        """Save services to database by updating/inserting, avoiding deletion issues."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Get current services from DB
                cursor.execute("SELECT service_id, name, price FROM services")
                db_services = {row['name']: {'id': row['service_id'], 'price': row['price']} for row in cursor.fetchall()}

                # Get services from the dialog (self.services holds the state from the dialog)
                dialog_services = self.services

                # Identify services to add or update
                db_service_names = set(db_services.keys())
                dialog_service_names = set(dialog_services.keys())

                services_to_add = dialog_service_names - db_service_names
                services_to_update = db_service_names.intersection(dialog_service_names)
                # Note: We are intentionally NOT deleting services here to prevent FOREIGN KEY errors.
                # Services removed in the dialog will simply remain in the database but won't be shown
                # in the dialog next time unless re-added. A future improvement could be to mark them inactive.

                # Add new services
                for name in services_to_add:
                    price = dialog_services[name]
                    cursor.execute(
                        "INSERT INTO services (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                    self.logger.info(f"Added service: {name} ({price} DA)")

                # Update existing services (only if price changed)
                for name in services_to_update:
                    db_price = db_services[name]['price']
                    dialog_price = dialog_services[name]
                    if db_price != dialog_price:
                        service_id = db_services[name]['id']
                        cursor.execute(
                            "UPDATE services SET price = ? WHERE service_id = ?",
                            (dialog_price, service_id)
                        )
                        self.logger.info(f"Updated service price: {name} to {dialog_price} DA")

                conn.commit()
                self.logger.info("Services saved successfully (updates/inserts only).")
                # Reload services into the app's memory after saving to reflect changes
                self.load_services()

        except (DatabaseError, sqlite3.Error) as e:
            self.logger.exception("Failed to save services")
            # Use self.root as parent for messagebox if available
            parent_window = self.root if hasattr(self, 'root') else None
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les services:\n{e}", parent=parent_window)


    def show_settings(self):
        if self.current_user['role'] == 'Assistant':
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "You do not have permission to access this tab.")
            return
        dialog = ServiceSettingsDialog(self.root, self.services)
        self.root.wait_window(dialog.top)
        self.services = dialog.services
        self.save_services()  # Now saves to database

    def setup_ui(self):
        # Main container with modern padding
        main_container = ttk.Frame(self.root, style='Content.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Only one search bar: keep the second one with placeholder and event bindings
        search_bar_frame = ttk.Frame(main_container, padding=(0, 5, 0, 10)) # Add padding below
        search_bar_frame.pack(side=tk.TOP, fill=tk.X)

        self.global_search_var = tk.StringVar()
        self.global_search_entry = ttk.Entry(search_bar_frame,
                                             textvariable=self.global_search_var,
                                             width=50,
                                             font=('Arial', 11))
        self.global_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.global_search_entry.insert(0, "Rechercher un patient...")
        self.global_search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.global_search_entry.bind("<FocusOut>", self.restore_search_placeholder)
        self.global_search_entry.bind("<KeyRelease>", self.handle_global_search)
        self.global_search_entry.bind("<Down>", self.focus_search_results) # Navigate down to results

        # Create a frame to hold sidebar and content area below search bar
        lower_frame = ttk.Frame(main_container)
        lower_frame.pack(fill=tk.BOTH, expand=True)

        print("DEBUG: current_user role at sidebar creation:", self.current_user['role'])
        # Create sidebar (now inside lower_frame)
        self.sidebar = Sidebar(lower_frame, width=200, theme_switcher=self.theme_switcher)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Create main content area (now inside lower_frame)
        self.content_frame = ttk.Frame(lower_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add sidebar buttons
        self.sidebar.add_button("Dashboard", self.show_dashboard)
        self.sidebar.add_button("Liste d'attente", self.show_waiting)
        self.sidebar.add_button("Patients", self.show_patient_management)
        # Removed "Rendez-vous" button

        # Add role-specific buttons
        user_role = self.current_user['role']

        if user_role == 'Admin':
            self.sidebar.add_button("User Management", self.show_user_management)
            self.sidebar.add_button("Rapport", self.show_reports)
            self.sidebar.add_button("Paramètres", self.show_settings)
        elif user_role == 'Doctor':
            self.sidebar.add_button("Rapport", self.show_reports)
            self.sidebar.add_button("Paramètres", self.show_settings)
        elif user_role == 'Assistant':
            pass
        else:
            self.logger.warning(f"Unknown user role encountered: {user_role}")

        self.show_dashboard()

    def show_user_management(self):
        import logging
        logging.getLogger("UserAction").info(f"User management accessed by role: {self.current_user['role']}")
        from user_management_dialog import UserManagementDialog
        UserManagementDialog(self.root, self.db)

    def clear_search_placeholder(self, event=None):
        if self.global_search_entry.get() == "Rechercher un patient...":
            self.global_search_entry.delete(0, tk.END)
            self.global_search_entry.config(foreground='black') # Or your default text color

    def restore_search_placeholder(self, event=None):
        if not self.global_search_entry.get():
            self.global_search_entry.insert(0, "Rechercher un patient...")
            self.global_search_entry.config(foreground='grey')
            # Use after to delay hiding, allows click on listbox
            self.root.after(200, self.hide_search_results)

    def handle_global_search(self, event=None):
        """Handle global search input."""
        query = self.global_search_var.get().strip()
        if query == "Rechercher un patient..." or len(query) < 2:
            self.hide_search_results()
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM patients WHERE name LIKE ? ORDER BY name LIMIT 10",
                    (f"%{query}%",)
                )
                results = [row['name'] for row in cursor.fetchall()]
                self.update_search_results(results)
        except Exception as e:
            self.logger.error(f"Global search error: {e}")
            self.hide_search_results()

    def update_search_results(self, results):
        """Create or update the search results listbox."""
        if not results:
            self.hide_search_results()
            return

        if not self.search_results_listbox:
            # Calculate position relative to the entry widget
            x = self.global_search_entry.winfo_rootx() - self.root.winfo_rootx()
            y = self.global_search_entry.winfo_rooty() - self.root.winfo_rooty() + self.global_search_entry.winfo_height()
            width = self.global_search_entry.winfo_width()

            self.search_results_listbox = tk.Listbox(self.root, # Place in root to overlay other widgets
                                                     width=self.global_search_entry['width'], # Match entry width
                                                     height=min(len(results), 6), # Limit height
                                                     font=('Arial', 10))
            self.search_results_listbox.place(x=x, y=y) # Use place for specific positioning
            self.search_results_listbox.bind("<<ListboxSelect>>", self.on_search_result_select)
            self.search_results_listbox.bind("<FocusOut>", self.hide_search_results) # Hide on focus out
            self.search_results_listbox.bind("<Escape>", self.hide_search_results) # Hide on Escape

        self.search_results_listbox.delete(0, tk.END)
        for item in results:
            self.search_results_listbox.insert(tk.END, item)

        # Ensure listbox is visible
        self.search_results_listbox.lift()

    def focus_search_results(self, event=None):
        """Move focus to the search results listbox if visible.""" 
        if self.search_results_listbox and self.search_results_listbox.winfo_viewable():
            self.search_results_listbox.focus_set()
            self.search_results_listbox.selection_set(0) # Select the first item

    def on_search_result_select(self, event=None):
        """Handle selection from the search results."""
        if not self.search_results_listbox or not self.search_results_listbox.curselection():
            return

        selected_index = self.search_results_listbox.curselection()[0]
        selected_patient = self.search_results_listbox.get(selected_index)

        self.global_search_var.set(selected_patient) # Update entry
        self.hide_search_results()
        self.global_search_entry.icursor(tk.END) # Move cursor to end

        # Open patient list and potentially pre-filter
        self.show_patient_list(search_term=selected_patient)

    def hide_search_results(self, event=None):
        """Destroy the search results listbox.""" 
        if self.search_results_listbox:
            self.search_results_listbox.destroy()
            self.search_results_listbox = None

    def clear_content(self):
        """Clear all widgets from content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        print(f"DEBUG: show_dashboard called on instance of type {type(self)}")
        print(f"DEBUG: Available attributes: {dir(self)}")
        self.clear_content()
        dashboard = ttk.Frame(self.content_frame)
        dashboard.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Stats cards row
        stats_frame = ttk.Frame(dashboard)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1, pad=10)
        
        # Create stat cards with modern styling
        self.create_stat_card(stats_frame, 
            "Patients en attente", 
            len(self.waiting_queue),
            "⏰", 0) # Replaced unsupported emoji
        self.create_stat_card(stats_frame,
            "Vus aujourd'hui",
            self.calculate_patients_seen_today(), # Use DB query function
            "✓", 1)
        self.create_stat_card(stats_frame,
            "Temps moyen consultation", # Updated label
            self.calculate_avg_consultation_time_today(), # Updated function call
            "⏱️", 2)
        self.create_stat_card(stats_frame,
            "Total des paiements",
            f"{self.calculate_total_payments()} DA", # Use DB query function
            "(DA)", 3) # Replaced unsupported emoji with text

        # Quick actions section
        actions_frame = ttk.LabelFrame(dashboard, text="Actions rapides", padding="10")
        actions_frame.pack(fill=tk.X, pady=10)
        
        for i, (text, cmd, icon) in enumerate([
            ("Nouveau patient", self.show_patient_list, "➕"),
            # Removed "Nouveau rendez-vous" quick action
            ("Liste d'attente", self.show_waiting, "★")
            # Removed "Rapports" quick action button
        ]):

            btn = ttk.Button(actions_frame, text=f"{icon} {text}", command=cmd, style="Dashboard.TButton")
            btn.pack(side=tk.LEFT, padx=5)

        # Today's visits with tabs
        notebook = ttk.Notebook(dashboard)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # List view tab
        list_frame = ttk.Frame(notebook)
        self.create_visits_list(list_frame)
        notebook.add(list_frame, text="Liste des visites")
        
        # Summary chart tab
        chart_frame = ttk.Frame(notebook)
        self.create_visits_chart(chart_frame)
        notebook.add(chart_frame, text="Résumé")

    # --- Start: Renamed calculate_avg_wait_time to calculate_avg_consultation_time_today and updated logic ---
    def calculate_avg_consultation_time_today(self):
        """Calculate average consultation time (call to checkout) for visits completed today."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Calculate average difference in seconds for visits checked out today
                cursor.execute("""
                    SELECT AVG(strftime('%s', checkout_at) - strftime('%s', called_at)) as avg_seconds
                    FROM visits
                    WHERE date(checkout_at) = date('now')
                    AND called_at IS NOT NULL -- Ensure called_at exists
                    AND checkout_at IS NOT NULL -- Ensure checkout_at exists
                """)
                result = cursor.fetchone()
                avg_seconds = result['avg_seconds'] if result and result['avg_seconds'] is not None else 0
                if avg_seconds > 0:
                    minutes = int(avg_seconds // 60)
                    seconds = int(avg_seconds % 60)
                    return f"{minutes}m {seconds}s"
                else:
                    # Return "0m 0s" or similar if no completed visits today or avg is zero
                    return "0m 0s"
        except Exception as e:
            self.logger.exception("Error calculating average consultation time for today")
            return "N/A"
    # --- End: Renamed function and updated logic ---

    # --- Start: Moving calculate_total_payments to class level (already correct) ---
    def calculate_total_payments(self): 
        """Calculate total payments for today"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(total_paid) as total
                    FROM visits 
                    WHERE date(checkout_at) = date('now')
                """)
                result = cursor.fetchone()
                # If SUM returns NULL (no rows match), it should be treated as 0
                return result['total'] if result and result['total'] is not None else 0
        except Exception as e:
            # Log the error for debugging
            self.logger.exception("Error calculating total payments")
            return 0 # Return 0 in case of error
    # --- End: Moving calculate_total_payments ---

    def create_stat_card(self, parent, title, value, icon, column):
        """Create a modern statistics card"""
        card = ttk.Frame(parent, style="StatCard.TFrame")
        card.grid(row=0, column=column, padx=5, sticky="nsew")
        
        icon_label = ttk.Label(card, text=icon,
                             font=('Arial', 24),
                             style="StatIcon.TLabel")
        icon_label.pack(pady=(10,0))
        
        value_label = ttk.Label(card, text=str(value),
                               font=('Arial', 20, 'bold'),
                               style="StatValue.TLabel")
        value_label.pack()

        # Store reference based on title or column for real-time updates
        if column == 0: # Patients en attente
            self.stat_waiting_value_label = value_label
        elif column == 1: # Vus aujourd'hui
            self.stat_visited_value_label = value_label
        elif column == 2: # Temps moyen d'attente
            self.stat_avg_wait_value_label = value_label
        elif column == 3: # Total des paiements
            self.stat_payments_value_label = value_label
        
        title_label = ttk.Label(card, text=title,
                               style="StatTitle.TLabel")
        title_label.pack(pady=(0,10))

    def create_visits_list(self, parent):
        """Create enhanced visits list"""
        # Create scrollable frame container
        outer_frame = ttk.Frame(parent)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with better styling
        columns = ("time", "patient", "services", "duration", "payment", "status")
        tree = ttk.Treeview(outer_frame, columns=columns, show="headings", height=12)
        
        # Configure columns with better formatting
        tree.heading("time", text="Heure")
        tree.heading("patient", text="Patient")
        tree.heading("services", text="Services")
        tree.heading("duration", text="Durée")
        tree.heading("payment", text="Paiement")
        tree.heading("status", text="Statut")
        
        tree.column("time", width=80)
        tree.column("patient", width=200)
        tree.column("services", width=250)
        tree.column("duration", width=80)
        tree.column("payment", width=100, anchor="e")
        tree.column("status", width=100)
        
        # Add both scrollbars
        vsb = ttk.Scrollbar(outer_frame, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(outer_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for scrollbars
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        outer_frame.grid_columnconfigure(0, weight=1)
        outer_frame.grid_rowconfigure(0, weight=1)
        
        # Load and display data
        self.load_todays_visits(tree)
        
        return tree

    def load_todays_visits(self, tree):
        """Load today's visits into the treeview"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        v.arrived_at,
                        p.name,
                        GROUP_CONCAT(s.name) as services,
                        (strftime('%s', v.checkout_at) - strftime('%s', v.called_at))/60.0 as duration,
                        v.total_paid,
                        CASE 
                            WHEN v.checkout_at IS NOT NULL THEN 'Terminé'
                            WHEN v.called_at IS NOT NULL THEN 'En consultation'
                            ELSE 'En attente'
                        END as status
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    WHERE date(v.arrived_at) = date('now')
                    GROUP BY v.visit_id
                    ORDER BY v.arrived_at DESC
                """)
                
                tree.delete(*tree.get_children())
                for row in cursor.fetchall():
                    arrival = datetime.strptime(row['arrived_at'], "%Y-%m-%d %H:%M:%S")
                    duration = f"{int(row['duration'])} min" if row['duration'] else "N/A"
                    services = row['services'] if row['services'] else "Aucun"
                    payment = f"{row['total_paid']} DA" if row['total_paid'] else "N/A"
                    
                    tree.insert("", "end", values=(
                        arrival.strftime("%H:%M"),
                        row['name'],
                        services,
                        duration,
                        payment,
                        row['status']
                    ))
        except Exception as e:
            self.logger.exception("Error loading today's visits")

    def get_hourly_visits(self):
        """Get hourly visit counts for today's visits"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        strftime('%H', arrived_at) as hour,
                        COUNT(*) as visit_count
                    FROM visits
                    WHERE date(arrived_at) = date('now')
                    GROUP BY strftime('%H', arrived_at)
                    ORDER BY hour
                """)
                results = cursor.fetchall()
                hourly_counts = {str(h).zfill(2): 0 for h in range(24)}
                for row in results:
                    hour = row['hour']
                    count = row['visit_count']
                    hourly_counts[hour] = count
                hours = list(hourly_counts.keys())
                counts = list(hourly_counts.values())
                return hours, counts
        except Exception as e:
            self.logger.exception("Error getting hourly visits")
            return [], []

    def create_visits_chart(self, parent):
        """Create summary chart for today's visits"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Create figure and axis
            fig = Figure(figsize=(8, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # Get hourly visit data
            hours, counts = self.get_hourly_visits()
            
            # Create bar chart
            ax.bar(hours, counts, color=self.colors['primary'])
            ax.set_title("Visites par heure")
            ax.set_xlabel("Heure")
            ax.set_ylabel("Nombre de visites")
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
        except ImportError:
            ttk.Label(parent, text="matplotlib requis pour afficher le graphique").pack()

    def show_waiting(self):
        """Show waiting list view"""
        self.clear_content()
        # Build waiting list UI inline, no call to create_waiting_section
        waiting_frame = ttk.Frame(self.content_frame, padding="10")
        waiting_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(waiting_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Liste d'Attente", style="Header.TLabel").pack(side=tk.LEFT)

        # Current patient with doctor display
        current_patient_frame = ttk.Frame(waiting_frame)
        current_patient_frame.pack(fill=tk.X, pady=(0, 10))
        self.current_patient_label = ttk.Label(current_patient_frame, text="Patient Actuel: Aucun patient", style="Header.TLabel")
        self.current_patient_label.pack(side=tk.LEFT)
        self.consultation_time_label = ttk.Label(current_patient_frame, text="Durée: 0 min", style="Info.TLabel")
        self.consultation_time_label.pack(side=tk.LEFT, padx=(10, 0))

        # Listbox with Scrollbar
        list_container = ttk.Frame(waiting_frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        if not hasattr(self, 'colors'):
            self.colors = {'primary': '#3498db'}  # Default fallback

        self.waiting_list = tk.Listbox(list_container, font=('Arial', 12), height=15,
                                       selectbackground=self.colors.get('primary', '#3498db'),
                                       selectforeground='white')
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.waiting_list.yview)
        self.waiting_list.configure(yscrollcommand=scrollbar.set)

        self.waiting_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons Frame
        button_frame = ttk.Frame(waiting_frame)
        button_frame.pack(fill=tk.X)

        add_cmd = self.add_new_patient_to_waiting if hasattr(self, 'add_new_patient_to_waiting') else None
        call_cmd = self.call_selected_patient if hasattr(self, 'call_selected_patient') else None
        remove_cmd = self.remove_from_waiting if hasattr(self, 'remove_from_waiting') else None
        checkout_cmd = self.checkout_patient if hasattr(self, 'checkout_patient') else None

        ttk.Button(button_frame, text="➕ Ajouter Patient", command=add_cmd, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="▶️ Appeler Patient", command=call_cmd).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Retirer Patient", command=remove_cmd, style="Danger.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Terminer Consultation", command=checkout_cmd, style="Success.TButton").pack(side=tk.LEFT, padx=5)

        self.root.after(10, self.update_displays)  # Keep this to populate the list

    def show_patient_management(self):
        """Show patient list dialog."""
        # Note: This currently opens the list as a separate dialog window.
        # The original intent (based on comments) might have been to embed it.
        self.show_patient_list() # Opens PatientListDialog as a separate window

    # Removed show_appointments method

    def show_reports(self):
        """Show the new reports tab"""
        if self.current_user['role'] == 'Assistant':
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "You do not have permission to access this tab.")
            return
        self.clear_content()
        # Instantiate the new ReportsTab class with user_role argument
        ReportsTab(self.content_frame, self.reports_manager, user_role=self.current_user['role'])

    def show_patient_registration(self):
        self.clear_content()
        reg_frame = ttk.Frame(self.content_frame)
        reg_frame.pack(fill=tk.BOTH, expand=True)
        self.create_patient_section(reg_frame)

    def update_displays(self):
        """Update all displays."""
        try:
            # Reload records to ensure data is fresh
            self.load_records()
            
            # Update current patient display with consultation time
            if hasattr(self, 'current_patient_label') and self.current_patient_label and self.current_patient_label.winfo_exists():
                if self.with_doctor:
                    # Get consultation duration
                    try:
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT strftime('%s', 'now') - strftime('%s', called_at) as duration
                                FROM visits
                                WHERE patient_id = (SELECT patient_id FROM patients WHERE name = ?)
                                AND date(called_at) = date('now')
                                AND checkout_at IS NULL
                            """, (self.with_doctor,))
                            result = cursor.fetchone()
                            if result and result['duration']:
                                minutes = int(result['duration']) // 60
                                self.current_patient_label.config(text=f"Patient Actuel: {self.with_doctor}")
                                if hasattr(self, 'consultation_time_label') and self.consultation_time_label:
                                    self.consultation_time_label.config(text=f"Durée: {minutes} min")
                    except Exception as e:
                        self.logger.error(f"Error getting consultation duration: {e}")
                else:
                    self.current_patient_label.config(text="Patient Actuel: Aucun patient")
                    if hasattr(self, 'consultation_time_label') and self.consultation_time_label:
                        self.consultation_time_label.config(text="Durée: 0 min")
            
            # Update waiting list while preserving selection
            if hasattr(self, 'waiting_list') and self.waiting_list and self.waiting_list.winfo_exists():
                # Store current selection if any
                selected_indices = self.waiting_list.curselection()
                selected_values = [self.waiting_list.get(i) for i in selected_indices]
                
                self.waiting_list.delete(0, tk.END)
                current_time = datetime.now()
                new_selections = []  # To store new indices of previously selected items
                
                # Fetch waiting patients with their arrival times
                try:
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT p.name, v.arrived_at
                            FROM visits v
                            JOIN patients p ON v.patient_id = p.patient_id
                            WHERE date(v.arrived_at) = date('now')
                            AND v.called_at IS NULL
                            AND v.checkout_at IS NULL
                            ORDER BY v.arrived_at
                        """)
                        for idx, row in enumerate(cursor.fetchall()):
                            name = row['name']
                            arrived_at = datetime.strptime(row['arrived_at'], "%Y-%m-%d %H:%M:%S")
                            wait_time = current_time - arrived_at
                            wait_minutes = int(wait_time.total_seconds() / 60)
                            item_text = f"{name} (En attente: {wait_minutes}min)"
                            self.waiting_list.insert(tk.END, item_text)
                            
                            # If this was a selected item, store its new index
                            if any(selected_name in item_text for selected_name in selected_values):
                                new_selections.append(idx)
                                
                        # Restore selections at their new positions
                        for idx in new_selections:
                            self.waiting_list.selection_set(idx)
                            
                except Exception as e:
                    self.logger.error(f"Error updating waiting list: {e}")

            # Update dashboard stat cards - adding None checks
            if hasattr(self, 'stat_waiting_value_label') and self.stat_waiting_value_label and self.stat_waiting_value_label.winfo_exists():
                self.stat_waiting_value_label.config(text=str(len(self.waiting_queue)))
            
            if hasattr(self, 'stat_visited_value_label') and self.stat_visited_value_label and self.stat_visited_value_label.winfo_exists():
                patients_seen = self.calculate_patients_seen_today()
                self.stat_visited_value_label.config(text=str(patients_seen))
            
            if hasattr(self, 'stat_avg_wait_value_label') and self.stat_avg_wait_value_label and self.stat_avg_wait_value_label.winfo_exists():
                avg_time = self.calculate_avg_consultation_time_today()
                self.stat_avg_wait_value_label.config(text=str(avg_time))
            
            if hasattr(self, 'stat_payments_value_label') and self.stat_payments_value_label and self.stat_payments_value_label.winfo_exists():
                total_payments = self.calculate_total_payments()
                self.stat_payments_value_label.config(text=f"{total_payments} DA")

        except tk.TclError as e:
            self.logger.error(f"Tkinter error during display update: {e}")
        except Exception as e:
            self.logger.exception("Error updating displays")

    # Removed update_all_appointments method

    def show_patient_list(self):
        """Show patient list dialog and update displays safely"""
        try:
            dialog = PatientListDialog(self.root, self.db)
            self.root.wait_window(dialog.top)
            if dialog.top.winfo_exists():
                self.root.after(100, self.update_displays)
        except Exception as e:
            self.logger.exception("Error showing patient list")
            messagebox.showerror("Erreur", 
                               "Une erreur est survenue lors de l'affichage de la liste des patients")

    # --- Start: Indenting create_visited_panel ---
    def create_visited_panel(self, parent):
        visited_card = ttk.Frame(parent, style="Card.TFrame")
        visited_card.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(visited_card)
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(header_frame, 
                 text="Patients Vus Aujourd'hui", 
                 style="Header.TLabel").pack(side=tk.LEFT)
        self.visited_count = ttk.Label(header_frame, text="0", style="Info.TLabel")
        self.visited_count.pack(side=tk.RIGHT)
        
        notebook = ttk.Notebook(visited_card)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        list_frame = ttk.Frame(notebook)
        self.visited_list = tk.Listbox(list_frame, 
                                     font=('Arial', 12),
                                     selectmode=tk.SINGLE,
                                     activestyle='none',
                                     bg=self.colors['surface'],
                                     fg=self.colors['text'])
        
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                  command=self.visited_list.yview)
        self.visited_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.visited_list.config(yscrollcommand=list_scroll.set)
        
        details_frame = ttk.Frame(notebook)
        self.visited_text = scrolledtext.ScrolledText(details_frame, 
                                                    wrap=tk.WORD, 
                                                    height=10)
        self.visited_text.pack(fill=tk.BOTH, expand=True)
        
        notebook.add(list_frame, text="Liste")
        notebook.add(details_frame, text="Détails")
        
        self.update_visited_text() # This call remains inside create_visited_panel
    # --- End: Indenting create_visited_panel ---
    
    # --- Start: Moving calculate_avg_wait_time to class level (already correct) ---
    def calculate_avg_wait_time(self): 
        """Calculate average waiting time for today's patients"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG((strftime('%s', called_at) - strftime('%s', arrived_at)) / 60.0) as avg_wait
                    FROM visits 
                    WHERE date(arrived_at) = date('now')
                    AND called_at IS NOT NULL
                """)
                result = cursor.fetchone()
                avg_wait = result['avg_wait'] if result['avg_wait'] else 0
                return f"{int(avg_wait)} min"
        except Exception:
            return "N/A"
    # --- End: Moving calculate_avg_wait_time ---

    # --- Start: Moving calculate_total_payments to class level ---
    def calculate_total_payments(self): 
        """Calculate total payments for today"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(total_paid) as total
                    FROM visits 
                    WHERE date(checkout_at) = date('now')
                """)
                result = cursor.fetchone()
                # If SUM returns NULL (no rows match), it should be treated as 0
                return result['total'] if result and result['total'] is not None else 0
        except Exception as e:
            # Log the error for debugging
            self.logger.exception("Error calculating total payments")
            return 0 # Return 0 in case of error
    # --- End: Moving calculate_total_payments ---

    def calculate_patients_seen_today(self):
        """Calculate the number of unique patients checked out today."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(DISTINCT patient_id) as count
                    FROM visits
                    WHERE date(checkout_at) = date('now')
                """)
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            self.logger.exception("Error calculating patients seen today")
            return 0

    def calculate_avg_consultation_time(self):
        """Calculate average consultation time (call to checkout) for visits completed today."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Calculate average difference in seconds, then convert
                cursor.execute("""
                    SELECT AVG(strftime('%s', checkout_at) - strftime('%s', called_at)) as avg_seconds
                    FROM visits
                    WHERE date(checkout_at) = date('now')
                    AND called_at IS NOT NULL -- Ensure called_at exists
                    AND checkout_at IS NOT NULL -- Ensure checkout_at exists
                """)
                result = cursor.fetchone()
                avg_seconds = result['avg_seconds'] if result and result['avg_seconds'] is not None else 0
                if avg_seconds > 0:
                    minutes = int(avg_seconds // 60)
                    seconds = int(avg_seconds % 60)
                    return f"{minutes}m {seconds}s"
                else:
                    return "0m 0s"
        except Exception as e:
            self.logger.exception("Error calculating average consultation time")
            return "N/A"

    # --- Start: Moving update_waiting_list_colors to class level ---
    def update_waiting_list_colors(self): 
        """Apply alternating row colors to waiting list."""
        if hasattr(self, 'waiting_list') and self.waiting_list.winfo_exists():
            for i in range(self.waiting_list.size()):
                color = "#f5f5f5" if i % 2 == 0 else "#e0e7ef"
                self.waiting_list.itemconfig(i, background=color)
    # --- End: Moving update_waiting_list_colors ---

    # --- Start: Moving create_tooltip to class level ---
    def create_tooltip(self, widget, text): 
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = ttk.Label(tooltip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("Arial", 10))
        label.pack(ipadx=5, ipady=2)

        def enter(event):
            x = event.widget.winfo_rootx() + 20
            y = event.widget.winfo_rooty() + 20
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    # --- End: Moving create_tooltip ---

    # --- Start: Indenting add_new_patient_to_waiting (already correct) ---
    def add_new_patient_to_waiting(self):
        """Add new patient directly to waiting list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter à la Liste d'Attente")
        dialog.geometry("400x150")
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for new or existing patient
        ttk.Button(frame, text="Nouveau Patient", 
                  command=lambda: self.show_new_patient_dialog(dialog),
                  style="Primary.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(frame, text="Patient Existant",
                  command=lambda: self.show_patient_selection(dialog),
                  style="Secondary.TButton").pack(fill=tk.X, pady=5)
              
        ttk.Button(frame, text="Annuler", 
                  command=dialog.destroy).pack(fill=tk.X, pady=5)
    # --- End: Indenting add_new_patient_to_waiting ---

    # --- Start: Indenting show_new_patient_dialog ---
    def show_new_patient_dialog(self, parent_dialog):
        """Show dialog for new patient entry"""
        parent_dialog.destroy()
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouveau Patient")
        dialog.geometry("400x200") # Increased height for phone number
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Name Entry
        ttk.Label(frame, text="Nom du patient:").pack(anchor=tk.W)
        name_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        name_entry.pack(fill=tk.X, pady=(0, 10))
        name_entry.focus()
        
        # Phone Number Entry (Optional)
        ttk.Label(frame, text="Numéro de téléphone (Optionnel):").pack(anchor=tk.W)
        phone_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        phone_entry.pack(fill=tk.X, pady=(0, 10))
        
        def submit():
            name = name_entry.get().strip()
            phone_number = phone_entry.get().strip() or None # Get phone number, None if empty
            if name:
                # Pass phone number to register_patient_direct
                self.register_patient_direct(name, phone_number=phone_number) 
                dialog.destroy()
                
        name_entry.bind('<Return>', lambda e: phone_entry.focus()) # Move focus on Enter
        phone_entry.bind('<Return>', lambda e: submit()) # Submit on Enter from phone field
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Ajouter", style="Primary.TButton",
                  command=submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    # --- End: Indenting show_new_patient_dialog ---

    # --- Start: Indenting show_patient_selection ---
    def show_patient_selection(self, parent_dialog):
        """Show dialog for existing patient selection"""
        parent_dialog.destroy()
        dialog = PatientSelectionDialog(self.root, self.db, self.theme)
        self.root.wait_window(dialog.top)
        if dialog.selected_patient:
            self.register_patient_direct(dialog.selected_patient) # Phone number is not available here, will be None by default
    # --- End: Indenting show_patient_selection ---

    # --- Start: Indenting register_patient_direct ---
    def register_patient_direct(self, name, phone_number=None): # Added phone_number parameter
        """Register patient and add to waiting list directly"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    patient_id = existing['patient_id']
                    # Note: We might want to update the phone number for existing patients here,
                    # but for now, we only add it for new patients.
                else:
                    # Pass phone_number to db.add_patient
                    patient_id = self.db.add_patient(name, phone_number=phone_number) 
                
                # Pass the current user's ID from the login
                self.db.add_visit(patient_id, self.current_user['user_id'])
                conn.commit()
                
                self.waiting_queue.append(name)
                self.status_var.set(f"Patient {name} inscrit et ajouté à la liste d'attente.")
                self.update_displays()
                self.logger.info(f"Successfully added new patient to waiting list: {name}")
                
        except DatabaseError as e:
            self.logger.exception(f"Failed to register patient: {name}")
            messagebox.showerror("Erreur", 
                               "Impossible d'enregistrer le patient. "
                               "Veuillez réessayer plus tard.")
    # --- End: Indenting register_patient_direct ---

    # --- Start: Indenting call_selected_patient ---
    def call_selected_patient(self):
        """Call selected patient from waiting list"""
        selection = self.waiting_list.curselection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à appeler.")
            return

        if self.with_doctor:
            messagebox.showinfo("Information", 
                              f"Le médecin est actuellement avec {self.with_doctor}.")
            return

        idx = selection[0]
        patient = self.waiting_queue[idx]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Update visit status in database - now including user_id
            if self.db.update_patient_call(patient, now, self.current_user['user_id']):
                # Remove from waiting queue
                del self.waiting_queue[idx]
                self.with_doctor = patient
                self.status_var.set(f"Patient {patient} est maintenant avec le médecin.")
                self.update_displays()
            else:
                messagebox.showerror("Erreur", "Impossible de trouver la visite du patient")
                
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")
    # --- End: Indenting call_selected_patient ---

    # --- Start: Indenting register_patient ---
    def register_patient(self, phone_number=None): # Added phone_number parameter (though not used by its original UI)
        # This method might be less used now, but updating for consistency
        name = self.name_entry.get().strip() 
        if not name:
            self.logger.warning("Attempted to register patient with empty name")
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.")
            return
        try:
            with self.db.get_connection() as conn:
                # Check if patient already exists
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    patient_id = existing['patient_id']
                else:
                    # Pass phone_number (will likely be None here)
                    patient_id = self.db.add_patient(name, phone_number=phone_number) 
                
                # Pass the current user's ID here as well
                self.db.add_visit(patient_id, self.current_user['user_id'])
                conn.commit()
                
                self.waiting_queue.append(name)
                self.status_var.set(f"Patient {name} inscrit et ajouté à la liste d'attente.")
                self.name_entry.delete(0, tk.END)
                self.update_displays()
                self.logger.info(f"Successfully registered patient: {name}")
        except DatabaseError as e:
            self.logger.exception(f"Failed to register patient: {name}")
            messagebox.showerror("Erreur", 
                               "Impossible d'enregistrer le patient. "
                               "Veuillez réessayer plus tard.")
    # --- End: Indenting register_patient ---

    # --- Start: Indenting get_patient_visits ---
    def get_patient_visits(self, patient_name):
        """Get all visits for a patient from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, GROUP_CONCAT(s.name) as service_names
                FROM visits v
                JOIN patients p ON v.patient_id = p.patient_id
                LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                LEFT JOIN services s ON vs.service_id = s.service_id
                WHERE p.name = ?
                GROUP BY v.visit_id
                ORDER BY v.date DESC
            """, (patient_name,))
            return cursor.fetchall()
    # --- End: Indenting get_patient_visits ---

    # --- Start: Indenting next_patient ---
    def next_patient(self):
        if not self.waiting_queue:
            messagebox.showinfo("Information", "Aucun patient dans la liste d'attente.")
            return

        if self.with_doctor:
            messagebox.showinfo("Information", 
                              f"Le médecin est actuellement avec {self.with_doctor}.")
            return

        patient = self.waiting_queue.pop(0)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.process_payment()  # Simplified workflow - direct to payment
        try:
            # Update visit status in database - now including user_id
            if self.db.update_patient_call(patient, now, self.current_user['user_id']):
                self.with_doctor = patient
                self.status_var.set(f"Patient {patient} est maintenant avec le médecin.")
                self.update_displays()
            else:
                messagebox.showerror("Erreur", "Impossible de trouver la visite du patient")
                self.waiting_queue.insert(0, patient)  # Put patient back in queue
                
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")
            self.waiting_queue.insert(0, patient)  # Put patient back in queue
    # --- End: Indenting next_patient ---
            
    # --- Start: Indenting checkout_patient ---
    def checkout_patient(self):
        if not self.with_doctor:
            messagebox.showinfo("Information", "Aucun patient n'est avec le médecin.")
            return

        patient = self.with_doctor
        self.process_payment()  # Simplified workflow - direct to payment services
        self.update_displays()  # Ensure dashboard updates after checkout
    # --- End: Indenting checkout_patient ---

    # --- Start: Indenting process_payment ---
    def process_payment(self):
        if not self.with_doctor:
            messagebox.showinfo("Information", "Aucun patient n'est avec le médecin.")
            return

        patient = self.with_doctor
        
        try:
            # Get current visit from database
            current_visit = self.db.get_current_visit(patient)
            if not current_visit:
                messagebox.showerror("Erreur", "Impossible de trouver les détails de la visite actuelle")
                return
            
            # Show payment dialog with services list
            dialog = PaymentDialog(self.root, patient, self.services)
            self.root.wait_window(dialog.top)
            
            if hasattr(dialog, 'result') and dialog.result:
                # Get service IDs for selected services
                service_ids = [ 
                    self.db.get_service_id(service_name)
                    for service_name in dialog.selected_services
                ]
                
                # Update visit with checkout information
                self.db.update_visit_checkout(
                    current_visit['visit_id'],
                    dialog.total,
                    service_ids
                )
                
                # Add transaction to accounting
                self.accounting.add_transaction(
                    patient,
                    dialog.selected_services,
                    dialog.total
                )
                
                self.visited_today.append(patient)
                self.with_doctor = None
                self.status_var.set(
                    f"✓ Patient {patient} - Consultation terminée. "
                    f"Paiement: {dialog.total} DA"
                )
                self.update_displays()
                self.update_displays()  # Ensure dashboard updates after payment
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")
    # --- End: Indenting process_payment ---

    # --- Start: Indenting remove_from_waiting ---
    def remove_from_waiting(self):
        """Remove selected patient from waiting list."""
        selection = self.waiting_list.curselection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à retirer.")
            return
        
        idx = selection[0]
        patient = self.waiting_queue[idx]
        
        if messagebox.askyesno("Confirmation", 
                             f"Voulez-vous vraiment retirer {patient} de la liste d'attente?"):
            try:
                # Remove from queue
                del self.waiting_queue[idx]
                
                # Update database to mark visit as cancelled
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # First get the visit_id                        
                    cursor.execute("""
                        SELECT v.visit_id 
                        FROM visits v
                        JOIN patients p ON v.patient_id = p.patient_id
                        WHERE p.name = ?
                        AND date(v.date) = date('now')
                        AND v.called_at IS NULL
                        ORDER BY v.arrived_at DESC LIMIT 1
                    """, (patient,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Then update the visit
                        cursor.execute("""
                            UPDATE visits
                            SET checkout_at = ?,
                                called_at = ?,
                                total_paid = 0
                            WHERE visit_id = ?
                        """, (now, now, result['visit_id']))
                        conn.commit()
                self.status_var.set(f"Patient {patient} retiré de la liste d'attente")
                self.update_displays()
                self.logger.info(f"Removed patient from waiting list: {patient}")
            except Exception as e:
                self.logger.exception(f"Error removing patient from waiting list: {patient}")
                messagebox.showerror("Erreur",
                                   "Une erreur est survenue lors du retrait du patient.")
    # --- End: Indenting remove_from_waiting ---

    # --- Start: Indenting show_patient_list (already indented, just adding comment) ---
    def show_patient_list(self, search_term=None):
        """Show patient list dialog, optionally with a pre-filled search term."""
        dialog = PatientListDialog(self.root, self.db)

        # If a search term is provided, populate the dialog's search entry
        if search_term and hasattr(dialog, 'search_entry'):
            dialog.search_entry.insert(0, search_term)
            # Trigger the search function within the dialog
            dialog.on_search(None) # Pass None as event object

        self.root.wait_window(dialog.top)
        # Removed call to update_all_appointments
        self.update_displays()
    # --- End: Indenting show_patient_list ---

    # Removed show_financial_report method as it's replaced by show_reports

    # Removed update_all_appointments method
    # Removed show_appointment_dialog method

    # --- Start: Indenting calculate_avg_wait_time (already indented, just adding comment) ---
    def calculate_avg_wait_time(self):
        """Calculate average waiting time for today's patients"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG((strftime('%s', called_at) - strftime('%s', arrived_at)) / 60.0) as avg_wait
                    FROM visits 
                    WHERE date(arrived_at) = date('now')
                    AND called_at IS NOT NULL
                """)
                result = cursor.fetchone()
                avg_wait = result['avg_wait'] if result['avg_wait'] else 0
                return f"{int(avg_wait)} min"
        except Exception:
            return "N/A"
    # --- End: Indenting calculate_avg_wait_time ---

    # --- Start: Indenting calculate_total_payments (already indented, just adding comment) ---
    def calculate_total_payments(self):
        """Calculate total payments for today"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(total_paid) as total
                    FROM visits 
                    WHERE date(checkout_at) = date('now')
                """)
                result = cursor.fetchone()
                return result['total'] if result['total'] else 0
        except Exception:
            return 0
    # --- End: Indenting calculate_total_payments ---

    def on_closing(self):
        """Clean up resources and close the application"""
        # Cancel any pending update jobs
        if hasattr(self, 'update_job') and self.update_job:
            self.root.after_cancel(self.update_job)
        self.root.destroy()

if __name__ == "__main__":
    logger = setup_logging()
    try:
        logger.info("Starting application...")
        # Use ThemedTk and set the theme 'arc'
        root = ThemedTk(theme="arc") 
        app = DoctorsWaitingRoomApp(root)
        root.mainloop()
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        messagebox.showerror("Erreur Critique", 
                           "Une erreur inattendue s'est produite. "
                           "L'application va se fermer.")
        raise
