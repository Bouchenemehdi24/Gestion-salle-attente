import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta  # Added timedelta import
import logging
from database import DatabaseError, DatabaseOperationError # Import DatabaseError and DatabaseOperationError
from tkcalendar import DateEntry  # Added import for date picker

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dialog for adding a new patient
class NewPatientDialog:
    def __init__(self, parent, db, on_success):
        self.top = tk.Toplevel(parent)
        self.top.title("Nouveau Patient")
        self.top.geometry("400x350")
        self.db = db
        self.on_success = on_success # Callback function after successful addition

        self.top.transient(parent)
        self.top.grab_set()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.top, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Name Entry
        ttk.Label(frame, text="Nom du patient:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        self.name_entry.focus()

        # Phone Number Entry (Optional)
        ttk.Label(frame, text="Numéro de téléphone (Optionnel):").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.phone_entry.pack(fill=tk.X, pady=(0, 10))

        # Blood Pressure Systolic Entry (Optional)
        ttk.Label(frame, text="Tension artérielle (mmHg) (Optionnel):").pack(anchor=tk.W)
        bp_frame = ttk.Frame(frame)
        bp_frame.pack(fill=tk.X, pady=(0, 10))

        self.bp_systolic_entry = ttk.Entry(bp_frame, width=14, font=('Arial', 12))
        self.bp_systolic_entry.pack(side=tk.LEFT, fill=tk.X)
        # Tooltip(self.bp_systolic_entry, "Entrez la pression systolique (ex: 120).") # Commented out

        ttk.Label(bp_frame, text=" / ").pack(side=tk.LEFT, padx=5)

        self.bp_diastolic_entry = ttk.Entry(bp_frame, width=14, font=('Arial', 12))
        self.bp_diastolic_entry.pack(side=tk.LEFT, fill=tk.X)
        # Tooltip(self.bp_diastolic_entry, "Entrez la pression diastolique (ex: 80).") # Commented out

        # Oxygen Saturation Entry (Optional)
        ttk.Label(frame, text="Saturation en oxygène (%) (Optionnel):").pack(anchor=tk.W)
        self.oxygen_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.oxygen_entry.pack(fill=tk.X, pady=(0, 10))
        # Tooltip(self.oxygen_entry, "Entrez la saturation en oxygène (ex: 98).") # Commented out

        # Heart Rate Entry (Optional)
        ttk.Label(frame, text="Fréquence cardiaque (bpm) (Optionnel):").pack(anchor=tk.W)
        self.heart_rate_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.heart_rate_entry.pack(fill=tk.X, pady=(0, 10))
        # Tooltip(self.heart_rate_entry, "Entrez la fréquence cardiaque (ex: 70).") # Commented out

        # Bind Enter key for navigation/submission
        self.name_entry.bind('<Return>', lambda e: self.phone_entry.focus())
        self.phone_entry.bind('<Return>', lambda e: self.bp_systolic_entry.focus())
        self.bp_systolic_entry.bind('<Return>', lambda e: self.bp_diastolic_entry.focus())
        self.bp_diastolic_entry.bind('<Return>', lambda e: self.oxygen_entry.focus())
        self.oxygen_entry.bind('<Return>', lambda e: self.heart_rate_entry.focus())
        self.heart_rate_entry.bind('<Return>', lambda e: self.submit())

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Ajouter", style='Primary.TButton',
                  command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", style='Secondary.TButton',
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def submit(self):
        name = self.name_entry.get().strip()
        phone_number = self.phone_entry.get().strip() or None # Use None if empty

        # Validate optional numeric fields
        def parse_int(value):
            try:
                return int(value)
            except ValueError:
                return None

        bp_systolic = parse_int(self.bp_systolic_entry.get().strip())
        bp_diastolic = parse_int(self.bp_diastolic_entry.get().strip())
        oxygen = parse_int(self.oxygen_entry.get().strip())
        heart_rate = parse_int(self.heart_rate_entry.get().strip())

        # Validate ranges if values are provided
        if bp_systolic is not None and not (50 <= bp_systolic <= 250):
            messagebox.showerror("Erreur", "La pression systolique doit être entre 50 et 250 mmHg.", parent=self.top)
            return
        if bp_diastolic is not None and not (30 <= bp_diastolic <= 150):
            messagebox.showerror("Erreur", "La pression diastolique doit être entre 30 et 150 mmHg.", parent=self.top)
            return
        if oxygen is not None and not (50 <= oxygen <= 100):
            messagebox.showerror("Erreur", "La saturation en oxygène doit être entre 50 et 100%.", parent=self.top)
            return
        if heart_rate is not None and not (30 <= heart_rate <= 220):
            messagebox.showerror("Erreur", "La fréquence cardiaque doit être entre 30 et 220 bpm.", parent=self.top)
            return

        if not name:
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.", parent=self.top)
            return

        try:
            # Attempt to add the patient via the database manager
            patient_id = self.db.add_patient(
                name,
                phone_number=phone_number,
                blood_pressure_systolic=bp_systolic,
                blood_pressure_diastolic=bp_diastolic,
                oxygen_saturation=oxygen,
                heart_rate=heart_rate
            )
            if patient_id:
                messagebox.showinfo("Succès", f"Patient '{name}' ajouté avec succès.", parent=self.top)
                self.on_success() # Call the success callback (e.g., reload patient list)
                self.top.destroy()
            # The db.add_patient method should raise DatabaseError for duplicates or other issues
        except DatabaseError as e:
            # Catch specific database errors (like duplicates)
            messagebox.showerror("Erreur", f"Impossible d'ajouter le patient:\n{e}", parent=self.top)
        except Exception as e:
            # Catch any other unexpected errors
            messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue: {e}", parent=self.top)

# Dialog for editing an existing patient
class EditPatientDialog:
    def __init__(self, parent, db, patient_data, on_success):
        self.top = tk.Toplevel(parent)
        self.top.title("Modifier Patient")
        self.top.geometry("400x400") # Increase height for new fields
        self.db = db
        self.patient_data = patient_data # Store initial patient data
        self.on_success = on_success # Callback function after successful update

        self.top.transient(parent)
        self.top.grab_set()

        self.create_widgets()
        self.populate_fields()

    def create_widgets(self):
        frame = ttk.Frame(self.top, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Name Entry
        ttk.Label(frame, text="Nom du patient:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        self.name_entry.focus()

        # Phone Number Entry (Optional)
        ttk.Label(frame, text="Numéro de téléphone (Optionnel):").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.phone_entry.pack(fill=tk.X, pady=(0, 10))

        # Blood Pressure Systolic/Diastolic Entry (Optional)
        ttk.Label(frame, text="Tension artérielle (mmHg) (Optionnel):").pack(anchor=tk.W)
        bp_frame = ttk.Frame(frame)
        bp_frame.pack(fill=tk.X, pady=(0, 10))

        self.bp_systolic_entry = ttk.Entry(bp_frame, width=14, font=('Arial', 12))
        self.bp_systolic_entry.pack(side=tk.LEFT, fill=tk.X)
        # Tooltip(self.bp_systolic_entry, "Entrez la pression systolique (ex: 120).") # Tooltip class might not be defined here, add if needed

        ttk.Label(bp_frame, text=" / ").pack(side=tk.LEFT, padx=5)

        self.bp_diastolic_entry = ttk.Entry(bp_frame, width=14, font=('Arial', 12))
        self.bp_diastolic_entry.pack(side=tk.LEFT, fill=tk.X)
        # Tooltip(self.bp_diastolic_entry, "Entrez la pression diastolique (ex: 80).") # Tooltip class might not be defined here, add if needed

        # Oxygen Saturation Entry (Optional)
        ttk.Label(frame, text="Saturation en oxygène (%) (Optionnel):").pack(anchor=tk.W)
        self.oxygen_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.oxygen_entry.pack(fill=tk.X, pady=(0, 10))
        # Tooltip(self.oxygen_entry, "Entrez la saturation en oxygène (ex: 98).") # Tooltip class might not be defined here, add if needed

        # Heart Rate Entry (Optional)
        ttk.Label(frame, text="Fréquence cardiaque (bpm) (Optionnel):").pack(anchor=tk.W)
        self.heart_rate_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.heart_rate_entry.pack(fill=tk.X, pady=(0, 10))
        # Tooltip(self.heart_rate_entry, "Entrez la fréquence cardiaque (ex: 70).") # Tooltip class might not be defined here, add if needed

        # Bind Enter key for navigation/submission
        self.name_entry.bind('<Return>', lambda e: self.phone_entry.focus())
        self.phone_entry.bind('<Return>', lambda e: self.bp_systolic_entry.focus())
        self.bp_systolic_entry.bind('<Return>', lambda e: self.bp_diastolic_entry.focus())
        self.bp_diastolic_entry.bind('<Return>', lambda e: self.oxygen_entry.focus())
        self.oxygen_entry.bind('<Return>', lambda e: self.heart_rate_entry.focus())
        self.heart_rate_entry.bind('<Return>', lambda e: self.submit())

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Enregistrer", style='Primary.TButton',
                  command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", style='Secondary.TButton',
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def populate_fields(self):
        """Populate the entry fields with the existing patient data."""
        self.name_entry.insert(0, self.patient_data.get('name', ''))
        self.phone_entry.insert(0, self.patient_data.get('phone_number', '') or '') # Handle None
        self.bp_systolic_entry.insert(0, self.patient_data.get('blood_pressure_systolic', '') or '')
        self.bp_diastolic_entry.insert(0, self.patient_data.get('blood_pressure_diastolic', '') or '')
        self.oxygen_entry.insert(0, self.patient_data.get('oxygen_saturation', '') or '')
        self.heart_rate_entry.insert(0, self.patient_data.get('heart_rate', '') or '')

    def submit(self):
        new_name = self.name_entry.get().strip()
        new_phone_number = self.phone_entry.get().strip() or None # Use None if empty
        patient_id = self.patient_data.get('patient_id')

        # Validate optional numeric fields
        def parse_int(value):
            val_str = str(value).strip() # Ensure it's a string before stripping
            if not val_str:
                return None
            try:
                return int(val_str)
            except ValueError:
                return "invalid" # Indicate parsing error

        bp_systolic = parse_int(self.bp_systolic_entry.get())
        bp_diastolic = parse_int(self.bp_diastolic_entry.get())
        oxygen = parse_int(self.oxygen_entry.get())
        heart_rate = parse_int(self.heart_rate_entry.get())

        # Check for invalid integer inputs
        if any(v == "invalid" for v in [bp_systolic, bp_diastolic, oxygen, heart_rate]):
             messagebox.showerror("Erreur", "Veuillez entrer des nombres valides pour les champs numériques ou laissez-les vides.", parent=self.top)
             return

        # Validate ranges if values are provided
        if bp_systolic is not None and not (50 <= bp_systolic <= 250):
            messagebox.showerror("Erreur", "La pression systolique doit être entre 50 et 250 mmHg.", parent=self.top)
            return
        if bp_diastolic is not None and not (30 <= bp_diastolic <= 150):
            messagebox.showerror("Erreur", "La pression diastolique doit être entre 30 et 150 mmHg.", parent=self.top)
            return
        if oxygen is not None and not (50 <= oxygen <= 100):
            messagebox.showerror("Erreur", "La saturation en oxygène doit être entre 50 et 100%.", parent=self.top)
            return
        if heart_rate is not None and not (30 <= heart_rate <= 220):
            messagebox.showerror("Erreur", "La fréquence cardiaque doit être entre 30 et 220 bpm.", parent=self.top)
            return

        if not new_name:
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.", parent=self.top)
            return

        if not patient_id:
             messagebox.showerror("Erreur Critique", "ID du patient manquant. Impossible de modifier.", parent=self.top)
             return

        try:
            # Attempt to update the patient via the database manager
            # Assuming user_id=None for audit log for now
            # TODO: Pass the actual user_id if available/required
            success = self.db.update_patient(
                patient_id=patient_id,
                name=new_name,
                phone_number=new_phone_number,
                blood_pressure_systolic=bp_systolic,
                blood_pressure_diastolic=bp_diastolic,
                oxygen_saturation=oxygen,
                heart_rate=heart_rate,
                user_id=None # Placeholder for user ID if needed for audit
            )
            if success:
                messagebox.showinfo("Succès", f"Patient '{new_name}' modifié avec succès.", parent=self.top)
                self.on_success() # Call the success callback (e.g., reload patient list)
                self.top.destroy()
            else:
                 # This might happen if the patient was deleted between opening the dialog and saving
                 messagebox.showwarning("Avertissement", "Le patient n'a pas été trouvé pour la modification.", parent=self.top)
                 self.top.destroy() # Close dialog even if not found

        except DatabaseOperationError as e:
            # Catch specific database errors (like name conflicts)
            messagebox.showerror("Erreur de Modification", f"Impossible de modifier le patient:\n{e}", parent=self.top)
        except ValueError as e: # Catch validation errors (e.g., empty name)
             messagebox.showerror("Erreur de Validation", str(e), parent=self.top)
        except Exception as e:
            # Catch any other unexpected errors
            messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue lors de la modification: {e}", parent=self.top)


# Dialog for selecting an existing patient
class PatientSelectionDialog:
    def __init__(self, parent, db, theme):
        self.top = tk.Toplevel(parent)
        self.top.title("Sélectionner Patient Existant")
        self.top.geometry("400x400")
        self.db = db
        self.theme = theme
        self.selected_patient = None # Store the selected patient name

        self.top.transient(parent)
        self.top.grab_set()

        self.create_widgets()
        self.load_patients()

    def create_widgets(self):
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Search Entry
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="Rechercher:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.filter_patients)

        # Patient Listbox
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Use default colors instead of theme.colors to avoid AttributeError
        self.patient_listbox = tk.Listbox(list_frame,
                                         font=('Arial', 12),
                                         selectmode=tk.SINGLE,
                                         bg='white',
                                         fg='black',
                                         borderwidth=1,
                                         relief='solid',
                                         highlightthickness=0,
                                         selectbackground='lightblue')
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_listbox.yview)
        self.patient_listbox.configure(yscrollcommand=scrollbar.set)

        self.patient_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.patient_listbox.bind('<Double-1>', lambda e: self.confirm_selection()) # Double-click to select

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="OK", style='Primary.TButton',
                  command=self.confirm_selection).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", style='Secondary.TButton',
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def load_patients(self):
        """Load all patient names into the listbox."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id, name, phone_number FROM patients ORDER BY name")
                rows = cursor.fetchall()
                logger.debug(f"Loaded {len(rows)} patients from database")
                self.all_patients = [(row['patient_id'], row['name'], row['phone_number']) for row in rows]
                self.filter_patients() # Initial population
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}", parent=self.top)
            self.all_patients = [] # Ensure it's initialized

    def filter_patients(self, event=None):
        """Filter the listbox based on the search entry."""
        # Removed guard clause to avoid AttributeError
        search_term = self.search_entry.get().strip().lower()
        logger.debug(f"Filtering patients with search term: '{search_term}'")
        self.patient_listbox.delete(0, tk.END)
        for patient_id, name, phone in self.all_patients:
            phone_str = str(phone) if phone is not None else ""
            if (search_term in name.lower() or
                search_term in phone_str.lower() or
                search_term in str(patient_id)):
                display_text = f"{name} - {phone_str}" if phone_str else name
                self.patient_listbox.insert(tk.END, display_text)

    def confirm_selection(self):
        """Confirm the selected patient and close the dialog."""
        selection = self.patient_listbox.curselection()
        if not selection:
            messagebox.showwarning("Sélection Requise", "Veuillez sélectionner un patient.", parent=self.top)
            return
        self.selected_patient = self.patient_listbox.get(selection[0])
        self.top.destroy()


import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import DatabaseError, DatabaseOperationError # Import DatabaseError and DatabaseOperationError
import tkinter.font as tkfont

# Dialog for adding a new patient and other dialogs remain unchanged...

class PatientListDialog:
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Liste des Patients")
        self.top.geometry("900x650")
        self.db = db
        
        # Get valid date range from database
        self.get_valid_date_range()

        # Set ttk style for better appearance
        style = ttk.Style(self.top)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))
        style.configure("Treeview", font=('Arial', 11), rowheight=25)
        style.configure("TButton", font=('Arial', 11))
        style.configure("TLabelFrame", font=('Arial', 12, 'bold'))

        self.patient_listbox = None  # Initialize attribute
        self.patient_listbox = None  # Initialize attribute
        self.create_widgets()
        self.load_patients()

    def get_valid_date_range(self):
        """Get the valid date range from the visits table"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MIN(date(checkout_at)) as earliest,
                           MAX(date(checkout_at)) as latest
                    FROM visits
                    WHERE checkout_at IS NOT NULL
                """)
                result = cursor.fetchone()
                if result and result['earliest'] and result['latest']:
                    self.min_date = datetime.strptime(result['earliest'], "%Y-%m-%d")
                    self.max_date = datetime.strptime(result['latest'], "%Y-%m-%d")
                else:
                    # Default to a reasonable range if no data
                    self.min_date = datetime.now() - timedelta(days=30)
                    self.max_date = datetime.now()
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            self.min_date = datetime.now() - timedelta(days=30)
            self.max_date = datetime.now()

    def create_widgets(self):
        # Search section with placeholder text
        search_frame = ttk.LabelFrame(self.top, text="Rechercher un patient", padding="10")
        search_frame.pack(fill=tk.X, padx=15, pady=10)

        # Text search entry
        self.search_entry = ttk.Entry(search_frame, width=30, font=('Arial', 11))
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_entry.insert(0, "Rechercher par nom ou numéro de téléphone...")
        self.search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self.add_search_placeholder)
        self.search_entry.bind('<KeyRelease>', self.on_text_search)

        # Date filter frame
        date_filter_frame = ttk.Frame(search_frame)
        date_filter_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(date_filter_frame, text=f"Période du: ({self.min_date.strftime('%d/%m/%Y')} - {self.max_date.strftime('%d/%m/%Y')})").grid(row=0, column=0, columnspan=2, padx=2, pady=2, sticky='w')
        
        self.from_date_entry = DateEntry(date_filter_frame, width=12, font=('Arial', 11),
                                       date_pattern='dd/mm/yyyy',
                                       mindate=self.min_date,
                                       maxdate=self.max_date)
        self.from_date_entry.grid(row=1, column=0, padx=2, pady=2)
        self.from_date_entry.set_date(self.min_date)

        ttk.Label(date_filter_frame, text="au:").grid(row=0, column=1, padx=2, pady=2, sticky='w')
        self.to_date_entry = DateEntry(date_filter_frame, width=12, font=('Arial', 11),
                                     date_pattern='dd/mm/yyyy',
                                     mindate=self.min_date,
                                     maxdate=self.max_date)
        self.to_date_entry.grid(row=1, column=1, padx=2, pady=2)
        self.to_date_entry.set_date(self.max_date)

        # Add Search button for date filters
        self.search_button = ttk.Button(date_filter_frame, text="Rechercher", style='Primary.TButton', command=self.on_search)
        self.search_button.grid(row=1, column=2, padx=10, pady=2)

        # Status label for search results
        self.status_label = ttk.Label(search_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Patient list
        list_frame = ttk.LabelFrame(self.top, text="Patients", padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        columns = ('name', 'phone', 'visits', 'last_visit', 'total_spent', 'blood_pressure', 'oxygen_saturation', 'heart_rate')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns with sorting capability
        self.tree.heading('name', text='Nom du Patient', command=lambda: self.sort_column('name', False))
        self.tree.heading('phone', text='Numéro de Téléphone', command=lambda: self.sort_column('phone', False))
        self.tree.heading('visits', text='Nombre de Visites', command=lambda: self.sort_column('visits', True))
        self.tree.heading('last_visit', text='Dernière Visite', command=lambda: self.sort_column('last_visit', False))
        self.tree.heading('total_spent', text='Total Payé', command=lambda: self.sort_column('total_spent', True))
        self.tree.heading('blood_pressure', text='Tension Artérielle (mmHg)', command=lambda: self.sort_column('blood_pressure', True))
        self.tree.heading('oxygen_saturation', text='Saturation en Oxygène (%)', command=lambda: self.sort_column('oxygen_saturation', True))
        self.tree.heading('heart_rate', text='Fréquence Cardiaque (bpm)', command=lambda: self.sort_column('heart_rate', True))
        
        self.tree.column('name', width=220)
        self.tree.column('phone', width=160)
        self.tree.column('visits', width=120, anchor='center')
        self.tree.column('last_visit', width=160)
        self.tree.column('total_spent', width=120, anchor='e')
        self.tree.column('blood_pressure', width=160, anchor='center')
        self.tree.column('oxygen_saturation', width=140, anchor='center')
        self.tree.column('heart_rate', width=140, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add action buttons with icons and tooltips
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X, pady=10)

        # Load icons (assuming icons are in assets folder)
        try:
            self.icon_edit = tk.PhotoImage(file="assets/edit_icon.png")
            self.icon_delete = tk.PhotoImage(file="assets/delete_icon.png")
            self.icon_new = tk.PhotoImage(file="assets/new_icon.png")
        except Exception:
            self.icon_edit = None
            self.icon_delete = None
            self.icon_new = None

        btn_edit = ttk.Button(btn_frame, text="Modifier", command=self.edit_patient, image=self.icon_edit, compound=tk.LEFT)
        btn_edit.pack(side=tk.LEFT, padx=8)
        self.create_tooltip(btn_edit, "Modifier le patient sélectionné")

        btn_delete = ttk.Button(btn_frame, text="Supprimer", command=self.delete_patient, image=self.icon_delete, compound=tk.LEFT)
        btn_delete.pack(side=tk.LEFT, padx=8)
        self.create_tooltip(btn_delete, "Supprimer le patient sélectionné")

        btn_new = ttk.Button(btn_frame, text="Nouveau Patient", command=self.open_new_patient_form, image=self.icon_new, compound=tk.LEFT)
        btn_new.pack(side=tk.LEFT, padx=8)
        self.create_tooltip(btn_new, "Ajouter un nouveau patient")

        btn_close = ttk.Button(btn_frame, text="Fermer", command=self.top.destroy)
        btn_close.pack(side=tk.RIGHT, padx=8)

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

    def clear_search_placeholder(self, event):
        if self.search_entry.get() == "Rechercher par nom ou numéro de téléphone...":
            self.search_entry.delete(0, tk.END)

    def add_search_placeholder(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Rechercher par nom ou numéro de téléphone...")

    def load_patients(self, from_date=None, to_date=None):
        """Load all patients with their visit information, optionally filtered by date range"""
        import traceback
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Base query selects all patients with optional date filtering
                query = """
                    SELECT
                        p.patient_id,
                        p.name,
                        p.phone_number,
                        p.blood_pressure_systolic,
                        p.blood_pressure_diastolic,
                        p.oxygen_saturation,
                        p.heart_rate,
                        COUNT(v.visit_id) as visit_count,
                        MAX(v.checkout_at) as last_visit,
                        SUM(v.total_paid) as total_spent
                    FROM patients p
                    LEFT JOIN visits v ON p.patient_id = v.patient_id
                """
                
                params = []
                if from_date or to_date:
                    query += " WHERE 1=1"
                    if from_date:
                        query += " AND DATE(v.checkout_at) >= ?"
                        params.append(from_date)
                    if to_date:
                        query += " AND DATE(v.checkout_at) <= ?"
                        params.append(to_date)

                query += """
                    GROUP BY p.patient_id, p.name, p.phone_number, p.blood_pressure_systolic, p.blood_pressure_diastolic, p.oxygen_saturation, p.heart_rate
                    ORDER BY p.name
                """

                # Debug logging
                logger.debug(f"Executing SQL query: {query}")
                logger.debug(f"With parameters: {params}")

                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.debug(f"Number of rows fetched: {len(rows)}")

                self.tree.delete(*self.tree.get_children())
                self.patient_data_cache = []

                for row in rows:
                    patient_id = row['patient_id']
                    last_visit_raw = row['last_visit']
                    last_visit = last_visit_raw if last_visit_raw else 'Jamais'
                    if last_visit != 'Jamais':
                        last_visit = datetime.strptime(last_visit, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                    total_spent = f"{row['total_spent']} DA" if row['total_spent'] else '0 DA'
                    phone_number = row['phone_number'] if row['phone_number'] else 'N/A'

                    # Only show patients with visits in the date range if dates are specified
                    if (from_date or to_date) and last_visit == 'Jamais':
                        continue

                    blood_pressure = "N/A"
                    if row['blood_pressure_systolic'] is not None and row['blood_pressure_diastolic'] is not None:
                        blood_pressure = f"{row['blood_pressure_systolic']} / {row['blood_pressure_diastolic']}"
                    oxygen_saturation = str(row['oxygen_saturation']) if row['oxygen_saturation'] is not None else "N/A"
                    heart_rate = str(row['heart_rate']) if row['heart_rate'] is not None else "N/A"

                    self.tree.insert('', 'end', iid=patient_id, values=(
            row['name'],
            phone_number,
            row['visit_count'],
            last_visit,
            total_spent,
            blood_pressure,
            oxygen_saturation,
                heart_rate
            ))
                    self.patient_data_cache.append({
                        'patient_id': patient_id,
                        'name': row['name'],
                        'phone_number': phone_number,
                        'visit_count': row['visit_count'],
                        'last_visit': last_visit,
                        'total_spent': total_spent,
                        'blood_pressure': blood_pressure,
                        'oxygen_saturation': oxygen_saturation,
                        'heart_rate': heart_rate
                    })

                # Update status label
                if from_date or to_date:
                    period = f"du {from_date} au {to_date}" if from_date and to_date else \
                             f"depuis le {from_date}" if from_date else \
                             f"jusqu'au {to_date}"
                    self.status_label.config(text=f"{len(self.tree.get_children())} patient(s) trouvé(s) {period}")
                else:
                    self.status_label.config(text=f"{len(self.tree.get_children())} patient(s) au total")

        except Exception as e:
            logger.error("Exception in load_patients:", exc_info=True)
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}")

    def on_text_search(self, event=None):
        """Handle text-only search"""
        search_text = self.search_entry.get().strip().lower()
        if search_text == "rechercher par nom ou numéro de téléphone...":
            search_text = ""
            
        # Show all items if search is empty
        if not search_text:
            self.load_patients()
            return
        
        # Instead of detaching/reattaching, rebuild the treeview with filtered patients
        filtered_patients = []
        for patient in self.patient_data_cache:
            name = patient['name'].lower()
            phone = patient['phone_number'].lower() if patient['phone_number'] else ''
            if search_text in name or search_text in phone:
                filtered_patients.append(patient)
        
        self.tree.delete(*self.tree.get_children())
        for patient in filtered_patients:
            self.tree.insert('', 'end', iid=patient['patient_id'], values=(
                patient['name'],
                patient['phone_number'],
                patient['visit_count'],
                patient['last_visit'],
                patient['total_spent'],
                patient['blood_pressure'],
                patient['oxygen_saturation'],
                patient['heart_rate']
            ))

    def on_search(self, event=None):
        """Handle combined text and date search when search button is clicked"""
        logger.debug("on_search called")
        search_text = self.search_entry.get().strip().lower()
        if search_text == "rechercher par nom ou numéro de téléphone...":
            search_text = ""

        from_date_raw = self.from_date_entry.get_date()
        to_date_raw = self.to_date_entry.get_date()

        # Validate date range
        if from_date_raw > to_date_raw:
            messagebox.showerror("Erreur", "La date de début doit être antérieure à la date de fin")
            return

        # Convert dates to string format for database
        from_date_db = from_date_raw.strftime("%Y-%m-%d")
        to_date_db = to_date_raw.strftime("%Y-%m-%d")

        logger.debug(f"Performing date search with from_date={from_date_db}, to_date={to_date_db}")
        self.load_patients(from_date=from_date_db, to_date=to_date_db)

        # Apply text filter if needed
        if search_text:
            logger.debug(f"Applying text filter: {search_text}")
            filtered_items = []
            for item_id in self.tree.get_children():
                values = self.tree.item(item_id)['values']
                name = str(values[0]).lower()
                phone = str(values[1]).lower()
                if search_text in name or search_text in phone:
                    filtered_items.append(item_id)

            # Hide non-matching items
            all_items = list(self.tree.get_children())
            for item_id in all_items:
                if item_id not in filtered_items:
                    self.tree.detach(item_id)

            # Update status with combined search results
            self.status_label.config(
                text=f"{len(filtered_items)} patient(s) trouvé(s) pour '{search_text}' entre {from_date_raw.strftime('%d/%m/%Y')} et {to_date_raw.strftime('%d/%m/%Y')}"
            )

    def sort_column(self, col, numeric):
        """Sort treeview column when header clicked"""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        if numeric:
            def convert(value):
                try:
                    if col == 'blood_pressure':
                        # Extract systolic value for sorting
                        if value and '/' in value:
                            return int(value.split('/')[0])
                        else:
                            return 0
                    # Remove non-numeric characters for total_spent (e.g., "1234 DA")
                    return float(''.join(filter(str.isdigit, value))) if value else 0
                except:
                    return 0
            data.sort(key=lambda t: convert(t[0]))
        else:
            data.sort(key=lambda t: t[0].lower())

        # Toggle sort order
        if hasattr(self, 'sort_reverse') and self.sort_reverse.get(col, False):
            data.reverse()
            self.sort_reverse[col] = False
        else:
            if not hasattr(self, 'sort_reverse'):
                self.sort_reverse = {}
            self.sort_reverse[col] = True

        # Rearrange items in sorted order
        for index, (val, item) in enumerate(data):
            self.tree.move(item, '', index)

    # Other methods (open_new_patient_form, edit_patient, delete_patient, show_history) remain unchanged...


    def open_new_patient_form(self):
        """Opens the dialog to add a new patient."""
        # Create and display the NewPatientDialog
        # Pass self.load_patients as the callback to refresh the list on success
        dialog = NewPatientDialog(self.top, self.db, self.load_patients)
        # Wait for the dialog to close before continuing
        self.top.wait_window(dialog.top)

    def show_history(self):
        """Show detailed history for selected patient"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient")
            return
            
        patient_name = self.tree.item(selection[0])['values'][0]
        
        # Create history window
        history = tk.Toplevel(self.top)
        history.title(f"Historique - {patient_name}")
        history.geometry("600x400")
        
        # Create history treeview
        columns = ('date', 'services', 'paid')
        tree = ttk.Treeview(history, columns=columns, show='headings')
        
        tree.heading('date', text='Date')
        tree.heading('services', text='Services')
        tree.heading('paid', text='Montant')
        
        tree.column('date', width=100)
        tree.column('services', width=300)
        tree.column('paid', width=100, anchor='e')
        
        scrollbar = ttk.Scrollbar(history, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load patient history
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        v.checkout_at,
                        GROUP_CONCAT(s.name) as services,
                        v.total_paid
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    WHERE p.name = ?
                    GROUP BY v.visit_id
                    ORDER BY v.checkout_at DESC
                """, (patient_name,))
                
                for row in cursor.fetchall():
                    if row['checkout_at']:
                        visit_date = datetime.strptime(
                            row['checkout_at'], 
                            "%Y-%m-%d %H:%M:%S"
                        ).strftime("%d/%m/%Y")
                        services = row['services'] if row['services'] else "Consultation"
                        tree.insert('', 'end', values=(
                            visit_date,
                            services,
                            f"{row['total_paid']} DA"
                        ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de l'historique: {str(e)}")

    def edit_patient(self):
        """Opens the edit dialog for the selected patient."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à modifier.", parent=self.top)
            return
        
        patient_id = selection[0] # The iid is the patient_id
        
        try:
            # Fetch current patient data
            patient_data = self.db.get_patient_by_id(patient_id)
            if not patient_data:
                messagebox.showerror("Erreur", "Impossible de récupérer les informations du patient sélectionné.", parent=self.top)
                self.load_patients() # Refresh list in case patient was deleted
                return

            # Open the EditPatientDialog
            dialog = EditPatientDialog(self.top, self.db, patient_data, self.load_patients)
            self.top.wait_window(dialog.top) # Wait for the edit dialog to close

        except DatabaseOperationError as e:
            messagebox.showerror("Erreur de Base de Données", f"Impossible de récupérer les informations du patient:\n{e}", parent=self.top)
        except Exception as e:
            messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue: {e}", parent=self.top)


    def delete_patient(self):
        """Deletes the selected patient after confirmation."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à supprimer.", parent=self.top)
            return

        patient_id = selection[0] # The iid is the patient_id
        patient_name = self.tree.item(patient_id)['values'][0]

        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirmer la Suppression",
            f"Êtes-vous sûr de vouloir supprimer le patient '{patient_name}' et toutes ses données associées (visites, paiements) ?\n\nCette action est irréversible.",
            parent=self.top
        )

        if confirm:
            try:
                # Assuming user_id=None for audit log for now
                # TODO: Pass the actual user_id if available/required
                if self.db.delete_patient_by_id(patient_id, user_id=None): 
                    messagebox.showinfo("Succès", f"Patient '{patient_name}' supprimé avec succès.", parent=self.top)
                    self.load_patients() # Refresh the list
                else:
                    # This case might happen if the patient was deleted by another process
                    # between selection and confirmation, though delete_patient_by_id raises error now.
                    messagebox.showwarning("Avertissement", f"Le patient '{patient_name}' n'a pas pu être trouvé pour la suppression.", parent=self.top)
                    self.load_patients() # Refresh anyway
            except DatabaseOperationError as e:
                messagebox.showerror("Erreur de Suppression", f"Impossible de supprimer le patient:\n{e}", parent=self.top)
            except Exception as e:
                messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue lors de la suppression: {e}", parent=self.top)
