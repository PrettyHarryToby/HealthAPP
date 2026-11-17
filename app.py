"""
Main GUI application for Avenara
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, date
from database import init_database, get_session, close_session
from models import (
    Patient, BloodParameters, ReproductiveHealth, VitaminLevels,
    MicronutrientLevels, Medication, GeneticData, PatientNeeds
)
from analysis import generate_health_insights, analyze_vitamin_trends, analyze_micronutrient_trends
import re


class HealthDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Avenara - Women's Health Workspace")
        self.root.geometry("1200x800")
        
        # Initialize database
        init_database()
        
        # Create main container
        self.create_main_interface()
        
    def create_main_interface(self):
        """Create the main interface with notebook tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_patient_tab()
        self.create_blood_parameters_tab()
        self.create_reproductive_health_tab()
        self.create_vitamin_tab()
        self.create_micronutrient_tab()
        self.create_medication_tab()
        self.create_genetic_tab()
        self.create_patient_needs_tab()
        self.create_insights_tab()
        
    def create_patient_tab(self):
        """Create patient management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Patients")
        
        # Left panel - Patient list
        left_panel = ttk.Frame(frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_panel, text="Patient List", font=("Arial", 12, "bold")).pack()
        
        # Patient listbox with scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.patient_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.patient_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.patient_listbox.yview)
        self.patient_listbox.bind('<<ListboxSelect>>', self.on_patient_select)
        
        # Buttons
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_patient_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_patient).pack(side=tk.LEFT, padx=2)
        
        # Right panel - Patient form
        right_panel = ttk.LabelFrame(frame, text="Patient Information")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Form fields
        self.patient_fields = {}
        fields = [
            ("Patient ID", "patient_id"),
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("Date of Birth (YYYY-MM-DD)", "date_of_birth"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Address", "address")
        ]
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(right_panel, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            if field == "address":
                entry = scrolledtext.ScrolledText(right_panel, height=3, width=30)
            else:
                entry = ttk.Entry(right_panel, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.patient_fields[field] = entry
        
        # Buttons
        btn_frame2 = ttk.Frame(right_panel)
        btn_frame2.grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame2, text="Add New", command=self.add_patient).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Update", command=self.update_patient).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Clear", command=self.clear_patient_form).pack(side=tk.LEFT, padx=5)
        
        self.current_patient_id = None
        self.refresh_patient_list()
    
    def refresh_patient_list(self):
        """Refresh the patient list"""
        self.patient_listbox.delete(0, tk.END)
        session = get_session()
        try:
            patients = session.query(Patient).order_by(Patient.last_name).all()
            for patient in patients:
                self.patient_listbox.insert(tk.END, f"{patient.patient_id} - {patient.first_name} {patient.last_name}")
        finally:
            close_session(session)
    
    def on_patient_select(self, event):
        """Handle patient selection"""
        selection = self.patient_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.patient_listbox.get(selection[0])
        patient_id = selected_text.split(" - ")[0]
        
        session = get_session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            if patient:
                self.current_patient_id = patient.id
                self.patient_fields["patient_id"].delete(0, tk.END)
                self.patient_fields["patient_id"].insert(0, patient.patient_id)
                self.patient_fields["first_name"].delete(0, tk.END)
                self.patient_fields["first_name"].insert(0, patient.first_name or "")
                self.patient_fields["last_name"].delete(0, tk.END)
                self.patient_fields["last_name"].insert(0, patient.last_name or "")
                self.patient_fields["date_of_birth"].delete(0, tk.END)
                self.patient_fields["date_of_birth"].insert(0, str(patient.date_of_birth) if patient.date_of_birth else "")
                self.patient_fields["email"].delete(0, tk.END)
                self.patient_fields["email"].insert(0, patient.email or "")
                self.patient_fields["phone"].delete(0, tk.END)
                self.patient_fields["phone"].insert(0, patient.phone or "")
                self.patient_fields["address"].delete("1.0", tk.END)
                self.patient_fields["address"].insert("1.0", patient.address or "")
        finally:
            close_session(session)
    
    def add_patient(self):
        """Add a new patient"""
        try:
            session = get_session()
            patient_id = self.patient_fields["patient_id"].get().strip()
            if not patient_id:
                messagebox.showerror("Error", "Patient ID is required")
                return
            
            # Check if patient ID already exists
            existing = session.query(Patient).filter_by(patient_id=patient_id).first()
            if existing:
                messagebox.showerror("Error", "Patient ID already exists")
                return
            
            dob_str = self.patient_fields["date_of_birth"].get().strip()
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
            
            patient = Patient(
                patient_id=patient_id,
                first_name=self.patient_fields["first_name"].get().strip(),
                last_name=self.patient_fields["last_name"].get().strip(),
                date_of_birth=dob,
                email=self.patient_fields["email"].get().strip() or None,
                phone=self.patient_fields["phone"].get().strip() or None,
                address=self.patient_fields["address"].get("1.0", tk.END).strip() or None
            )
            
            session.add(patient)
            session.commit()
            messagebox.showinfo("Success", "Patient added successfully")
            self.clear_patient_form()
            self.refresh_patient_list()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add patient: {str(e)}")
        finally:
            close_session(session)
    
    def update_patient(self):
        """Update existing patient"""
        if not self.current_patient_id:
            messagebox.showerror("Error", "Please select a patient to update")
            return
        
        try:
            session = get_session()
            patient = session.query(Patient).filter_by(id=self.current_patient_id).first()
            if not patient:
                messagebox.showerror("Error", "Patient not found")
                return
            
            dob_str = self.patient_fields["date_of_birth"].get().strip()
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
            
            patient.first_name = self.patient_fields["first_name"].get().strip()
            patient.last_name = self.patient_fields["last_name"].get().strip()
            patient.date_of_birth = dob
            patient.email = self.patient_fields["email"].get().strip() or None
            patient.phone = self.patient_fields["phone"].get().strip() or None
            patient.address = self.patient_fields["address"].get("1.0", tk.END).strip() or None
            patient.updated_at = datetime.utcnow()
            
            session.commit()
            messagebox.showinfo("Success", "Patient updated successfully")
            self.refresh_patient_list()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update patient: {str(e)}")
        finally:
            close_session(session)
    
    def delete_patient(self):
        """Delete selected patient"""
        selection = self.patient_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a patient to delete")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this patient and all associated data?"):
            return
        
        selected_text = self.patient_listbox.get(selection[0])
        patient_id = selected_text.split(" - ")[0]
        
        session = get_session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            if patient:
                session.delete(patient)
                session.commit()
                messagebox.showinfo("Success", "Patient deleted successfully")
                self.clear_patient_form()
                self.refresh_patient_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete patient: {str(e)}")
        finally:
            close_session(session)
    
    def clear_patient_form(self):
        """Clear patient form"""
        self.current_patient_id = None
        for field in self.patient_fields.values():
            if isinstance(field, scrolledtext.ScrolledText):
                field.delete("1.0", tk.END)
            else:
                field.delete(0, tk.END)
    
    def get_selected_patient_id(self):
        """Get the selected patient's database ID"""
        selection = self.patient_listbox.curselection()
        if not selection:
            return None
        
        selected_text = self.patient_listbox.get(selection[0])
        patient_id = selected_text.split(" - ")[0]
        
        session = get_session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            return patient.id if patient else None
        finally:
            close_session(session)
    
    def create_blood_parameters_tab(self):
        """Create blood parameters tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Blood Parameters")
        
        # Patient selection
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.blood_patient_var = tk.StringVar()
        self.blood_patient_combo = ttk.Combobox(patient_frame, textvariable=self.blood_patient_var, state="readonly", width=30)
        self.blood_patient_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(patient_frame, text="Refresh Patients", command=self.refresh_patient_combos).pack(side=tk.LEFT, padx=5)
        
        # Form
        form_frame = ttk.LabelFrame(frame, text="Blood Test Results")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Date field
        ttk.Label(scrollable_frame, text="Test Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.blood_date_entry = ttk.Entry(scrollable_frame, width=20)
        self.blood_date_entry.insert(0, str(date.today()))
        self.blood_date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # Blood parameter fields
        self.blood_fields = {}
        blood_params = [
            ("Hemoglobin (g/dL)", "hemoglobin"),
            ("Hematocrit (%)", "hematocrit"),
            ("White Blood Cells (cells/μL)", "white_blood_cells"),
            ("Red Blood Cells (cells/μL)", "red_blood_cells"),
            ("Platelets (cells/μL)", "platelets"),
            ("Glucose (mg/dL)", "glucose"),
            ("Creatinine (mg/dL)", "creatinine"),
            ("BUN (mg/dL)", "bun"),
            ("ALT (U/L)", "alt"),
            ("AST (U/L)", "ast"),
            ("Total Cholesterol (mg/dL)", "total_cholesterol"),
            ("HDL Cholesterol (mg/dL)", "hdl_cholesterol"),
            ("LDL Cholesterol (mg/dL)", "ldl_cholesterol"),
            ("Triglycerides (mg/dL)", "triglycerides"),
            ("TSH (mIU/L)", "tsh"),
            ("T3 (ng/dL)", "t3"),
            ("T4 (μg/dL)", "t4"),
            ("Ferritin (ng/mL)", "ferritin"),
            ("Iron (μg/dL)", "iron"),
            ("Transferrin (mg/dL)", "transferrin"),
        ]
        
        row = 1
        for label, field in blood_params:
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=20)
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.blood_fields[field] = entry
            row += 1
        
        # Notes
        ttk.Label(scrollable_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.blood_notes = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.blood_notes.grid(row=row, column=1, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Blood Parameters", command=self.save_blood_parameters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_blood_form).pack(side=tk.LEFT, padx=5)
        
        self.refresh_patient_combos()
    
    def save_blood_parameters(self):
        """Save blood parameters"""
        patient_id = self.get_patient_id_from_combo(self.blood_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            test_date_str = self.blood_date_entry.get().strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            blood_params = BloodParameters(
                patient_id=patient_id,
                test_date=test_date
            )
            
            for field, entry in self.blood_fields.items():
                value = entry.get().strip()
                if value:
                    try:
                        setattr(blood_params, field, float(value))
                    except ValueError:
                        pass
            
            notes = self.blood_notes.get("1.0", tk.END).strip()
            if notes:
                blood_params.notes = notes
            
            session.add(blood_params)
            session.commit()
            messagebox.showinfo("Success", "Blood parameters saved successfully")
            self.clear_blood_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_blood_form(self):
        """Clear blood parameters form"""
        self.blood_date_entry.delete(0, tk.END)
        self.blood_date_entry.insert(0, str(date.today()))
        for entry in self.blood_fields.values():
            entry.delete(0, tk.END)
        self.blood_notes.delete("1.0", tk.END)
    
    def create_reproductive_health_tab(self):
        """Create reproductive health tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Reproductive Health")
        
        # Similar structure to blood parameters tab
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.repro_patient_var = tk.StringVar()
        self.repro_patient_combo = ttk.Combobox(patient_frame, textvariable=self.repro_patient_var, state="readonly", width=30)
        self.repro_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Reproductive Health Information")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ttk.Label(scrollable_frame, text="Record Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.repro_date_entry = ttk.Entry(scrollable_frame, width=20)
        self.repro_date_entry.insert(0, str(date.today()))
        self.repro_date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.repro_fields = {}
        repro_params = [
            ("Last Menstrual Period (YYYY-MM-DD)", "last_menstrual_period"),
            ("Cycle Length (days)", "cycle_length"),
            ("Period Duration (days)", "period_duration"),
            ("Menstrual Regularity", "menstrual_regularity"),
            ("FSH (mIU/mL)", "fsh"),
            ("LH (mIU/mL)", "lh"),
            ("Estradiol (pg/mL)", "estradiol"),
            ("Progesterone (ng/mL)", "progesterone"),
            ("Testosterone (ng/dL)", "testosterone"),
            ("Prolactin (ng/mL)", "prolactin"),
            ("Pregnancy Status", "pregnancy_status"),
            ("Weeks Pregnant", "weeks_pregnant"),
            ("Due Date (YYYY-MM-DD)", "due_date"),
            ("Contraception Method", "contraception_method"),
        ]
        
        row = 1
        for label, field in repro_params:
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=20)
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.repro_fields[field] = entry
            row += 1
        
        # Checkboxes
        self.repro_pcos = tk.BooleanVar()
        self.repro_endometriosis = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text="PCOS Diagnosis", variable=self.repro_pcos).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        ttk.Checkbutton(scrollable_frame, text="Endometriosis", variable=self.repro_endometriosis).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.repro_notes = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.repro_notes.grid(row=row, column=1, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Reproductive Health", command=self.save_reproductive_health).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_repro_form).pack(side=tk.LEFT, padx=5)
    
    def save_reproductive_health(self):
        """Save reproductive health data"""
        patient_id = self.get_patient_id_from_combo(self.repro_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            record_date_str = self.repro_date_entry.get().strip()
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date() if record_date_str else date.today()
            
            repro_health = ReproductiveHealth(
                patient_id=patient_id,
                record_date=record_date,
                pcos_diagnosis=self.repro_pcos.get(),
                endometriosis=self.repro_endometriosis.get()
            )
            
            date_fields = ['last_menstrual_period', 'due_date']
            int_fields = ['cycle_length', 'period_duration', 'weeks_pregnant']
            
            for field, entry in self.repro_fields.items():
                value = entry.get().strip()
                if value:
                    if field in date_fields:
                        try:
                            setattr(repro_health, field, datetime.strptime(value, "%Y-%m-%d").date())
                        except ValueError:
                            pass
                    elif field in int_fields:
                        try:
                            setattr(repro_health, field, int(value))
                        except ValueError:
                            pass
                    else:
                        try:
                            setattr(repro_health, field, float(value))
                        except ValueError:
                            setattr(repro_health, field, value)
            
            notes = self.repro_notes.get("1.0", tk.END).strip()
            if notes:
                repro_health.notes = notes
            
            session.add(repro_health)
            session.commit()
            messagebox.showinfo("Success", "Reproductive health data saved successfully")
            self.clear_repro_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_repro_form(self):
        """Clear reproductive health form"""
        self.repro_date_entry.delete(0, tk.END)
        self.repro_date_entry.insert(0, str(date.today()))
        for entry in self.repro_fields.values():
            entry.delete(0, tk.END)
        self.repro_pcos.set(False)
        self.repro_endometriosis.set(False)
        self.repro_notes.delete("1.0", tk.END)
    
    def create_vitamin_tab(self):
        """Create vitamin levels tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Vitamin Levels")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.vitamin_patient_var = tk.StringVar()
        self.vitamin_patient_combo = ttk.Combobox(patient_frame, textvariable=self.vitamin_patient_var, state="readonly", width=30)
        self.vitamin_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Vitamin Level Test Results")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ttk.Label(scrollable_frame, text="Test Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.vitamin_date_entry = ttk.Entry(scrollable_frame, width=20)
        self.vitamin_date_entry.insert(0, str(date.today()))
        self.vitamin_date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.vitamin_fields = {}
        vitamins = [
            ("Vitamin A (μg/dL)", "vitamin_a"),
            ("Vitamin D (ng/mL)", "vitamin_d"),
            ("Vitamin E (mg/dL)", "vitamin_e"),
            ("Vitamin K (ng/mL)", "vitamin_k"),
            ("Vitamin B1 - Thiamine (ng/mL)", "vitamin_b1"),
            ("Vitamin B2 - Riboflavin (ng/mL)", "vitamin_b2"),
            ("Vitamin B3 - Niacin (ng/mL)", "vitamin_b3"),
            ("Vitamin B5 - Pantothenic Acid (μg/mL)", "vitamin_b5"),
            ("Vitamin B6 - Pyridoxine (ng/mL)", "vitamin_b6"),
            ("Vitamin B7 - Biotin (ng/mL)", "vitamin_b7"),
            ("Vitamin B9 - Folate (ng/mL)", "vitamin_b9"),
            ("Vitamin B12 - Cobalamin (pg/mL)", "vitamin_b12"),
            ("Vitamin C - Ascorbic Acid (mg/dL)", "vitamin_c"),
        ]
        
        row = 1
        for label, field in vitamins:
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=20)
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.vitamin_fields[field] = entry
            row += 1
        
        ttk.Label(scrollable_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.vitamin_notes = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.vitamin_notes.grid(row=row, column=1, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Vitamin Levels", command=self.save_vitamin_levels).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_vitamin_form).pack(side=tk.LEFT, padx=5)
    
    def save_vitamin_levels(self):
        """Save vitamin levels"""
        patient_id = self.get_patient_id_from_combo(self.vitamin_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            test_date_str = self.vitamin_date_entry.get().strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            vitamin_levels = VitaminLevels(
                patient_id=patient_id,
                test_date=test_date
            )
            
            for field, entry in self.vitamin_fields.items():
                value = entry.get().strip()
                if value:
                    try:
                        setattr(vitamin_levels, field, float(value))
                    except ValueError:
                        pass
            
            notes = self.vitamin_notes.get("1.0", tk.END).strip()
            if notes:
                vitamin_levels.notes = notes
            
            session.add(vitamin_levels)
            session.commit()
            messagebox.showinfo("Success", "Vitamin levels saved successfully")
            self.clear_vitamin_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_vitamin_form(self):
        """Clear vitamin form"""
        self.vitamin_date_entry.delete(0, tk.END)
        self.vitamin_date_entry.insert(0, str(date.today()))
        for entry in self.vitamin_fields.values():
            entry.delete(0, tk.END)
        self.vitamin_notes.delete("1.0", tk.END)
    
    def create_micronutrient_tab(self):
        """Create micronutrient levels tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Micronutrients")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.micronutrient_patient_var = tk.StringVar()
        self.micronutrient_patient_combo = ttk.Combobox(patient_frame, textvariable=self.micronutrient_patient_var, state="readonly", width=30)
        self.micronutrient_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Micronutrient Level Test Results")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ttk.Label(scrollable_frame, text="Test Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.micronutrient_date_entry = ttk.Entry(scrollable_frame, width=20)
        self.micronutrient_date_entry.insert(0, str(date.today()))
        self.micronutrient_date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.micronutrient_fields = {}
        micronutrients = [
            ("Calcium (mg/dL)", "calcium"),
            ("Magnesium (mg/dL)", "magnesium"),
            ("Phosphorus (mg/dL)", "phosphorus"),
            ("Potassium (mEq/L)", "potassium"),
            ("Sodium (mEq/L)", "sodium"),
            ("Zinc (μg/dL)", "zinc"),
            ("Selenium (μg/L)", "selenium"),
            ("Copper (μg/dL)", "copper"),
            ("Manganese (μg/L)", "manganese"),
            ("Chromium (μg/L)", "chromium"),
            ("Molybdenum (μg/L)", "molybdenum"),
            ("Omega-3 (mg/dL)", "omega_3"),
            ("Omega-6 (mg/dL)", "omega_6"),
            ("Coenzyme Q10 (μg/mL)", "coenzyme_q10"),
        ]
        
        row = 1
        for label, field in micronutrients:
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=20)
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.micronutrient_fields[field] = entry
            row += 1
        
        ttk.Label(scrollable_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.micronutrient_notes = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.micronutrient_notes.grid(row=row, column=1, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Micronutrient Levels", command=self.save_micronutrient_levels).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_micronutrient_form).pack(side=tk.LEFT, padx=5)
    
    def save_micronutrient_levels(self):
        """Save micronutrient levels"""
        patient_id = self.get_patient_id_from_combo(self.micronutrient_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            test_date_str = self.micronutrient_date_entry.get().strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            micronutrient_levels = MicronutrientLevels(
                patient_id=patient_id,
                test_date=test_date
            )
            
            for field, entry in self.micronutrient_fields.items():
                value = entry.get().strip()
                if value:
                    try:
                        setattr(micronutrient_levels, field, float(value))
                    except ValueError:
                        pass
            
            notes = self.micronutrient_notes.get("1.0", tk.END).strip()
            if notes:
                micronutrient_levels.notes = notes
            
            session.add(micronutrient_levels)
            session.commit()
            messagebox.showinfo("Success", "Micronutrient levels saved successfully")
            self.clear_micronutrient_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_micronutrient_form(self):
        """Clear micronutrient form"""
        self.micronutrient_date_entry.delete(0, tk.END)
        self.micronutrient_date_entry.insert(0, str(date.today()))
        for entry in self.micronutrient_fields.values():
            entry.delete(0, tk.END)
        self.micronutrient_notes.delete("1.0", tk.END)
    
    def create_medication_tab(self):
        """Create medication tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Medications")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.medication_patient_var = tk.StringVar()
        self.medication_patient_combo = ttk.Combobox(patient_frame, textvariable=self.medication_patient_var, state="readonly", width=30)
        self.medication_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Medication Information")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.medication_fields = {}
        med_fields = [
            ("Medication Name", "medication_name"),
            ("Dosage", "dosage"),
            ("Frequency", "frequency"),
            ("Start Date (YYYY-MM-DD)", "start_date"),
            ("End Date (YYYY-MM-DD)", "end_date"),
            ("Prescribing Physician", "prescribing_physician"),
            ("Reason/Indication", "reason"),
        ]
        
        for i, (label, field) in enumerate(med_fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            if field == "reason":
                entry = scrolledtext.ScrolledText(form_frame, height=3, width=40)
            else:
                entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.medication_fields[field] = entry
        
        self.medication_active = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Active Medication", variable=self.medication_active).grid(row=len(med_fields), column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Notes:").grid(row=len(med_fields)+1, column=0, sticky=tk.W, padx=5, pady=5)
        self.medication_notes = scrolledtext.ScrolledText(form_frame, height=3, width=40)
        self.medication_notes.grid(row=len(med_fields)+1, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Medication", command=self.save_medication).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_medication_form).pack(side=tk.LEFT, padx=5)
    
    def save_medication(self):
        """Save medication"""
        patient_id = self.get_patient_id_from_combo(self.medication_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            medication_name = self.medication_fields["medication_name"].get().strip()
            if not medication_name:
                messagebox.showerror("Error", "Medication name is required")
                return
            
            start_date_str = self.medication_fields["start_date"].get().strip()
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
            
            end_date_str = self.medication_fields["end_date"].get().strip()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            
            medication = Medication(
                patient_id=patient_id,
                medication_name=medication_name,
                dosage=self.medication_fields["dosage"].get().strip() or None,
                frequency=self.medication_fields["frequency"].get().strip() or None,
                start_date=start_date,
                end_date=end_date,
                prescribing_physician=self.medication_fields["prescribing_physician"].get().strip() or None,
                reason=self.medication_fields["reason"].get("1.0", tk.END).strip() or None,
                is_active=self.medication_active.get()
            )
            
            notes = self.medication_notes.get("1.0", tk.END).strip()
            if notes:
                medication.notes = notes
            
            session.add(medication)
            session.commit()
            messagebox.showinfo("Success", "Medication saved successfully")
            self.clear_medication_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_medication_form(self):
        """Clear medication form"""
        for field, entry in self.medication_fields.items():
            if isinstance(entry, scrolledtext.ScrolledText):
                entry.delete("1.0", tk.END)
            else:
                entry.delete(0, tk.END)
        self.medication_active.set(True)
        self.medication_notes.delete("1.0", tk.END)
    
    def create_genetic_tab(self):
        """Create genetic data tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Genetic Data")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.genetic_patient_var = tk.StringVar()
        self.genetic_patient_combo = ttk.Combobox(patient_frame, textvariable=self.genetic_patient_var, state="readonly", width=30)
        self.genetic_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Genetic Test Information")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.genetic_fields = {}
        genetic_fields = [
            ("Test Date (YYYY-MM-DD)", "test_date"),
            ("Test Type", "test_type"),
            ("Test Provider", "test_provider"),
            ("MTHFR C677T", "mthfr_c677t"),
            ("MTHFR A1298C", "mthfr_a1298c"),
        ]
        
        row = 0
        for label, field in genetic_fields:
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=30)
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.genetic_fields[field] = entry
            row += 1
        
        self.genetic_brca1 = tk.BooleanVar()
        self.genetic_brca2 = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text="BRCA1 Mutation", variable=self.genetic_brca1).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        ttk.Checkbutton(scrollable_frame, text="BRCA2 Mutation", variable=self.genetic_brca2).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Raw Data:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.genetic_raw_data = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.genetic_raw_data.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Interpretation:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.genetic_interpretation = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.genetic_interpretation.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Clinical Significance:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.genetic_clinical = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.genetic_clinical.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Recommendations:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.genetic_recommendations = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.genetic_recommendations.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        ttk.Label(scrollable_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.genetic_notes = scrolledtext.ScrolledText(scrollable_frame, height=3, width=40)
        self.genetic_notes.grid(row=row, column=1, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Genetic Data", command=self.save_genetic_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_genetic_form).pack(side=tk.LEFT, padx=5)
    
    def save_genetic_data(self):
        """Save genetic data"""
        patient_id = self.get_patient_id_from_combo(self.genetic_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            test_date_str = self.genetic_fields["test_date"].get().strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            genetic_data = GeneticData(
                patient_id=patient_id,
                test_date=test_date,
                test_type=self.genetic_fields["test_type"].get().strip() or None,
                test_provider=self.genetic_fields["test_provider"].get().strip() or None,
                mthfr_c677t=self.genetic_fields["mthfr_c677t"].get().strip() or None,
                mthfr_a1298c=self.genetic_fields["mthfr_a1298c"].get().strip() or None,
                brca1_mutation=self.genetic_brca1.get(),
                brca2_mutation=self.genetic_brca2.get(),
                raw_data=self.genetic_raw_data.get("1.0", tk.END).strip() or None,
                interpretation=self.genetic_interpretation.get("1.0", tk.END).strip() or None,
                clinical_significance=self.genetic_clinical.get("1.0", tk.END).strip() or None,
                recommendations=self.genetic_recommendations.get("1.0", tk.END).strip() or None,
                notes=self.genetic_notes.get("1.0", tk.END).strip() or None
            )
            
            session.add(genetic_data)
            session.commit()
            messagebox.showinfo("Success", "Genetic data saved successfully")
            self.clear_genetic_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_genetic_form(self):
        """Clear genetic form"""
        for entry in self.genetic_fields.values():
            entry.delete(0, tk.END)
        self.genetic_brca1.set(False)
        self.genetic_brca2.set(False)
        self.genetic_raw_data.delete("1.0", tk.END)
        self.genetic_interpretation.delete("1.0", tk.END)
        self.genetic_clinical.delete("1.0", tk.END)
        self.genetic_recommendations.delete("1.0", tk.END)
        self.genetic_notes.delete("1.0", tk.END)
    
    def create_patient_needs_tab(self):
        """Create patient needs tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Patient Needs")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.needs_patient_var = tk.StringVar()
        self.needs_patient_combo = ttk.Combobox(patient_frame, textvariable=self.needs_patient_var, state="readonly", width=30)
        self.needs_patient_combo.pack(side=tk.LEFT, padx=5)
        
        form_frame = ttk.LabelFrame(frame, text="Individual Patient Needs")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.needs_fields = {}
        needs_fields = [
            ("Record Date (YYYY-MM-DD)", "record_date"),
            ("Dietary Restrictions", "dietary_restrictions"),
            ("Special Diet", "special_diet"),
            ("Activity Level", "activity_level"),
            ("Smoking Status", "smoking_status"),
            ("Alcohol Consumption", "alcohol_consumption"),
            ("Sleep Hours", "sleep_hours"),
        ]
        
        for i, (label, field) in enumerate(needs_fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            if field == "dietary_restrictions":
                entry = scrolledtext.ScrolledText(form_frame, height=3, width=40)
            else:
                entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.needs_fields[field] = entry
        
        ttk.Label(form_frame, text="Health Goals:").grid(row=len(needs_fields), column=0, sticky=tk.W, padx=5, pady=5)
        self.needs_health_goals = scrolledtext.ScrolledText(form_frame, height=3, width=40)
        self.needs_health_goals.grid(row=len(needs_fields), column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Special Requirements:").grid(row=len(needs_fields)+1, column=0, sticky=tk.W, padx=5, pady=5)
        self.needs_special = scrolledtext.ScrolledText(form_frame, height=3, width=40)
        self.needs_special.grid(row=len(needs_fields)+1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Notes:").grid(row=len(needs_fields)+2, column=0, sticky=tk.W, padx=5, pady=5)
        self.needs_notes = scrolledtext.ScrolledText(form_frame, height=3, width=40)
        self.needs_notes.grid(row=len(needs_fields)+2, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Save Patient Needs", command=self.save_patient_needs).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_needs_form).pack(side=tk.LEFT, padx=5)
    
    def save_patient_needs(self):
        """Save patient needs"""
        patient_id = self.get_patient_id_from_combo(self.needs_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        try:
            session = get_session()
            record_date_str = self.needs_fields["record_date"].get().strip()
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date() if record_date_str else date.today()
            
            sleep_hours_str = self.needs_fields["sleep_hours"].get().strip()
            sleep_hours = float(sleep_hours_str) if sleep_hours_str else None
            
            patient_needs = PatientNeeds(
                patient_id=patient_id,
                record_date=record_date,
                dietary_restrictions=self.needs_fields["dietary_restrictions"].get("1.0", tk.END).strip() or None,
                special_diet=self.needs_fields["special_diet"].get().strip() or None,
                activity_level=self.needs_fields["activity_level"].get().strip() or None,
                smoking_status=self.needs_fields["smoking_status"].get().strip() or None,
                alcohol_consumption=self.needs_fields["alcohol_consumption"].get().strip() or None,
                sleep_hours=sleep_hours,
                health_goals=self.needs_health_goals.get("1.0", tk.END).strip() or None,
                special_requirements=self.needs_special.get("1.0", tk.END).strip() or None,
                notes=self.needs_notes.get("1.0", tk.END).strip() or None
            )
            
            session.add(patient_needs)
            session.commit()
            messagebox.showinfo("Success", "Patient needs saved successfully")
            self.clear_needs_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid date or number format")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
        finally:
            close_session(session)
    
    def clear_needs_form(self):
        """Clear patient needs form"""
        for field, entry in self.needs_fields.items():
            if isinstance(entry, scrolledtext.ScrolledText):
                entry.delete("1.0", tk.END)
            else:
                entry.delete(0, tk.END)
        self.needs_health_goals.delete("1.0", tk.END)
        self.needs_special.delete("1.0", tk.END)
        self.needs_notes.delete("1.0", tk.END)
    
    def create_insights_tab(self):
        """Create insights and analysis tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Insights & Analysis")
        
        patient_frame = ttk.Frame(frame)
        patient_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(patient_frame, text="Select Patient:").pack(side=tk.LEFT, padx=5)
        self.insights_patient_var = tk.StringVar()
        self.insights_patient_combo = ttk.Combobox(patient_frame, textvariable=self.insights_patient_var, state="readonly", width=30)
        self.insights_patient_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(patient_frame, text="Generate Insights", command=self.generate_insights).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(frame, text="Health Insights & Recommendations")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.insights_text = scrolledtext.ScrolledText(results_frame, height=30, width=100, wrap=tk.WORD)
        self.insights_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def generate_insights(self):
        """Generate and display health insights"""
        patient_id = self.get_patient_id_from_combo(self.insights_patient_var.get())
        if not patient_id:
            messagebox.showerror("Error", "Please select a patient")
            return
        
        session = get_session()
        try:
            insights = generate_health_insights(session, patient_id)
            
            self.insights_text.delete("1.0", tk.END)
            
            output = "=" * 80 + "\n"
            output += "HEALTH INSIGHTS & RECOMMENDATIONS\n"
            output += "=" * 80 + "\n\n"
            
            # Vitamin Analysis
            if insights['vitamin_analysis'] and insights['vitamin_analysis'].get('has_data'):
                va = insights['vitamin_analysis']
                output += "VITAMIN LEVEL ANALYSIS\n"
                output += "-" * 80 + "\n"
                output += f"Total Records Analyzed: {va.get('total_records', 0)}\n\n"
                
                if va.get('deficiencies'):
                    output += "DEFICIENCIES DETECTED:\n"
                    for def_item in va['deficiencies']:
                        output += f"  • {def_item['vitamin']}: {def_item['value']} {def_item['unit']} "
                        output += f"(Reference: {def_item['reference_low']}+ {def_item['unit']}) "
                        output += f"[{def_item['deficiency_percent']}% below normal]\n"
                        output += f"    Date: {def_item['date']}\n"
                    output += "\n"
                
                if va.get('excesses'):
                    output += "ELEVATED LEVELS DETECTED:\n"
                    for exc_item in va['excesses']:
                        output += f"  • {exc_item['vitamin']}: {exc_item['value']} {exc_item['unit']} "
                        output += f"(Reference: <{exc_item['reference_high']} {exc_item['unit']}) "
                        output += f"[{exc_item['excess_percent']}% above normal]\n"
                        output += f"    Date: {exc_item['date']}\n"
                    output += "\n"
                
                if va.get('trends'):
                    output += "VITAMIN TRENDS:\n"
                    for vitamin, trend_data in va['trends'].items():
                        output += f"  • {vitamin.replace('_', ' ').title()}: "
                        output += f"{trend_data['status']} ({trend_data['trend']}) "
                        output += f"- Latest: {trend_data['latest_value']} {trend_data.get('unit', '')} "
                        output += f"on {trend_data['latest_date']}\n"
                    output += "\n"
            else:
                output += "VITAMIN LEVEL ANALYSIS: No data available\n\n"
            
            # Micronutrient Analysis
            if insights['micronutrient_analysis'] and insights['micronutrient_analysis'].get('has_data'):
                ma = insights['micronutrient_analysis']
                output += "MICRONUTRIENT LEVEL ANALYSIS\n"
                output += "-" * 80 + "\n"
                output += f"Total Records Analyzed: {ma.get('total_records', 0)}\n\n"
                
                if ma.get('deficiencies'):
                    output += "DEFICIENCIES DETECTED:\n"
                    for def_item in ma['deficiencies']:
                        output += f"  • {def_item['micronutrient']}: {def_item['value']} {def_item['unit']} "
                        output += f"(Reference: {def_item['reference_low']}+ {def_item['unit']})\n"
                        output += f"    Date: {def_item['date']}\n"
                    output += "\n"
                
                if ma.get('excesses'):
                    output += "ELEVATED LEVELS DETECTED:\n"
                    for exc_item in ma['excesses']:
                        output += f"  • {exc_item['micronutrient']}: {exc_item['value']} {exc_item['unit']} "
                        output += f"(Reference: <{exc_item['reference_high']} {exc_item['unit']})\n"
                        output += f"    Date: {exc_item['date']}\n"
                    output += "\n"
            else:
                output += "MICRONUTRIENT LEVEL ANALYSIS: No data available\n\n"
            
            # Genetic Insights
            if insights['genetic_insights']:
                output += "GENETIC INSIGHTS\n"
                output += "-" * 80 + "\n"
                for genetic_insight in insights['genetic_insights']:
                    output += f"  • {genetic_insight['type']}: {genetic_insight.get('variant', '')}\n"
                    output += f"    Implication: {genetic_insight['implication']}\n"
                    output += f"    Priority: {genetic_insight['priority'].upper()}\n\n"
            else:
                output += "GENETIC INSIGHTS: No significant findings\n\n"
            
            # Medication Recommendations
            if insights['medication_recommendations']:
                output += "MEDICATION/SUPPLEMENT RECOMMENDATIONS\n"
                output += "-" * 80 + "\n"
                for med_rec in insights['medication_recommendations']:
                    output += f"  • {med_rec['type'].upper()}: {med_rec.get('vitamin', 'N/A')}\n"
                    output += f"    Reason: {med_rec['reason']}\n"
                    output += f"    Priority: {med_rec['priority'].upper()}\n\n"
            else:
                output += "MEDICATION RECOMMENDATIONS: None at this time\n\n"
            
            # Overall Recommendations
            if insights['overall_recommendations']:
                output += "OVERALL RECOMMENDATIONS\n"
                output += "-" * 80 + "\n"
                for rec in insights['overall_recommendations']:
                    output += f"  [{rec['priority'].upper()}] {rec['category']}: {rec['recommendation']}\n"
                output += "\n"
            
            output += "=" * 80 + "\n"
            output += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            self.insights_text.insert("1.0", output)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate insights: {str(e)}")
        finally:
            close_session(session)
    
    def refresh_patient_combos(self):
        """Refresh all patient combo boxes"""
        session = get_session()
        try:
            patients = session.query(Patient).order_by(Patient.last_name).all()
            patient_list = [f"{p.patient_id} - {p.first_name} {p.last_name}" for p in patients]
            
            combos = [
                self.blood_patient_combo,
                self.repro_patient_combo,
                self.vitamin_patient_combo,
                self.micronutrient_patient_combo,
                self.medication_patient_combo,
                self.genetic_patient_combo,
                self.needs_patient_combo,
                self.insights_patient_combo
            ]
            
            for combo in combos:
                combo['values'] = patient_list
        finally:
            close_session(session)
    
    def get_patient_id_from_combo(self, combo_value: str) -> int:
        """Get patient database ID from combo box value"""
        if not combo_value:
            return None
        
        patient_id = combo_value.split(" - ")[0]
        session = get_session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            return patient.id if patient else None
        finally:
            close_session(session)


def main():
    root = tk.Tk()
    app = HealthDatabaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

