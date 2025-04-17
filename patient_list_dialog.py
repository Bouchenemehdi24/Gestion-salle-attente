import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import DatabaseError, DatabaseOperationError # Import DatabaseError and DatabaseOperationError

# Dialog for adding a new patient
class NewPatientDialog:
    def __init__(self, parent, db, on_success):
        self.top = tk.Toplevel(parent)
        self.top.title("Nouveau Patient")
        self.top.geometry("400x200")
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

        # Bind Enter key for navigation/submission
        self.name_entry.bind('<Return>', lambda e: self.phone_entry.focus())
        self.phone_entry.bind('<Return>', lambda e: self.submit())

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Ajouter",
                  command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def submit(self):
        name = self.name_entry.get().strip()
        phone_number = self.phone_entry.get().strip() or None # Use None if empty

        if not name:
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.", parent=self.top)
            return

        try:
            # Attempt to add the patient via the database manager
            patient_id = self.db.add_patient(name, phone_number=phone_number)
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
        self.top.geometry("400x200")
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

        # Bind Enter key for navigation/submission
        self.name_entry.bind('<Return>', lambda e: self.phone_entry.focus())
        self.phone_entry.bind('<Return>', lambda e: self.submit())

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Enregistrer",
                  command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def populate_fields(self):
        """Populate the entry fields with the existing patient data."""
        self.name_entry.insert(0, self.patient_data.get('name', ''))
        self.phone_entry.insert(0, self.patient_data.get('phone_number', '') or '') # Handle None

    def submit(self):
        new_name = self.name_entry.get().strip()
        new_phone_number = self.phone_entry.get().strip() or None # Use None if empty
        patient_id = self.patient_data.get('patient_id')

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
            success = self.db.update_patient(patient_id, new_name, new_phone_number, user_id=None)
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
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Sélectionner Patient Existant")
        self.top.geometry("400x400")
        self.db = db
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

        self.patient_listbox = tk.Listbox(list_frame, font=('Arial', 12), selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_listbox.yview)
        self.patient_listbox.configure(yscrollcommand=scrollbar.set)

        self.patient_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.patient_listbox.bind('<Double-1>', lambda e: self.confirm_selection()) # Double-click to select

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="OK",
                  command=self.confirm_selection).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def load_patients(self):
        """Load all patient names into the listbox."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM patients ORDER BY name")
                self.all_patients = [row['name'] for row in cursor.fetchall()]
                self.filter_patients() # Initial population
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}", parent=self.top)
            self.all_patients = [] # Ensure it's initialized

    def filter_patients(self, event=None):
        """Filter the listbox based on the search entry."""
        search_term = self.search_entry.get().strip().lower()
        self.patient_listbox.delete(0, tk.END)
        for patient in self.all_patients:
            if search_term in patient.lower():
                self.patient_listbox.insert(tk.END, patient)

    def confirm_selection(self):
        """Confirm the selected patient and close the dialog."""
        selection = self.patient_listbox.curselection()
        if not selection:
            messagebox.showwarning("Sélection Requise", "Veuillez sélectionner un patient.", parent=self.top)
            return
        self.selected_patient = self.patient_listbox.get(selection[0])
        self.top.destroy()


class PatientListDialog:
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Liste des Patients")
        self.top.geometry("800x600")
        self.db = db
        self.create_widgets()
        self.load_patients()
        
    def create_widgets(self):
        # Search section
        search_frame = ttk.LabelFrame(self.top, text="Rechercher un patient", padding="5")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Patient list
        list_frame = ttk.LabelFrame(self.top, text="Patients", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('name', 'phone', 'visits', 'last_visit', 'total_spent') # Added 'phone'
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        self.tree.heading('name', text='Nom du Patient')
        self.tree.heading('phone', text='Numéro de Téléphone') # Added phone heading
        self.tree.heading('visits', text='Nombre de Visites')
        self.tree.heading('last_visit', text='Dernière Visite')
        self.tree.heading('total_spent', text='Total Payé')
        
        self.tree.column('name', width=200)
        self.tree.column('phone', width=150) # Added phone column config
        self.tree.column('visits', width=100, anchor='center')
        self.tree.column('last_visit', width=150)
        self.tree.column('total_spent', width=100, anchor='e')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add action buttons
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Modifier",
                  command=self.edit_patient).pack(side=tk.LEFT, padx=5) # Edit button
        ttk.Button(btn_frame, text="Supprimer",
                  command=self.delete_patient).pack(side=tk.LEFT, padx=5) # Delete button
        ttk.Button(btn_frame, text="Nouveau Patient",
                  command=self.open_new_patient_form).pack(side=tk.LEFT, padx=5) # Added New Patient button

        ttk.Button(btn_frame, text="Fermer",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def open_new_patient_form(self):
        """Opens the dialog to add a new patient."""
        # Create and display the NewPatientDialog
        # Pass self.load_patients as the callback to refresh the list on success
        dialog = NewPatientDialog(self.top, self.db, self.load_patients)
        # Wait for the dialog to close before continuing
        self.top.wait_window(dialog.top)

    def load_patients(self):
        """Load all patients with their visit information"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Select patient_id as well
                cursor.execute("""
                    SELECT
                        p.patient_id,
                        p.name,
                        p.phone_number, -- Added phone_number
                        COUNT(v.visit_id) as visit_count,
                        MAX(v.checkout_at) as last_visit,
                        SUM(v.total_paid) as total_spent
                    FROM patients p
                    LEFT JOIN visits v ON p.patient_id = v.patient_id
                    GROUP BY p.patient_id, p.name, p.phone_number -- Added phone_number to GROUP BY
                    ORDER BY p.name
                """)

                self.tree.delete(*self.tree.get_children()) # Clear existing items
                for row in cursor.fetchall():
                    patient_id = row['patient_id'] # Get the patient ID
                    last_visit = row['last_visit'] if row['last_visit'] else 'Jamais'
                    if last_visit != 'Jamais':
                        last_visit = datetime.strptime(last_visit,
                            "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                    total_spent = f"{row['total_spent']} DA" if row['total_spent'] else '0 DA'
                    phone_number = row['phone_number'] if row['phone_number'] else 'N/A' # Get phone number

                    # Use patient_id as the item ID (iid)
                    self.tree.insert('', 'end', iid=patient_id, values=(
                        row['name'],
                        phone_number, # Added phone number to values
                        row['visit_count'],
                        last_visit,
                        total_spent
                    ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}")

    def on_search(self, event=None):
        """Filter patient list based on search text"""
        search_text = self.search_entry.get().strip().lower()
        
        # Show all items if search is empty
        if not search_text:
            self.load_patients()
            return
            
        # Hide non-matching items
        for item in self.tree.get_children():
            patient_name = self.tree.item(item)['values'][0].lower()
            if search_text in patient_name:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

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
