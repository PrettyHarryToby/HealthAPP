"""
Database models for the Health Database Application
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from enum import Enum

Base = declarative_base()


class Patient(Base):
    """Patient information model"""
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    blood_parameters = relationship("BloodParameters", back_populates="patient", cascade="all, delete-orphan")
    reproductive_health = relationship("ReproductiveHealth", back_populates="patient", cascade="all, delete-orphan")
    vitamin_levels = relationship("VitaminLevels", back_populates="patient", cascade="all, delete-orphan")
    micronutrient_levels = relationship("MicronutrientLevels", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    genetic_data = relationship("GeneticData", back_populates="patient", cascade="all, delete-orphan")
    patient_needs = relationship("PatientNeeds", back_populates="patient", cascade="all, delete-orphan")
    gynecological_risk_indicators = relationship("GynecologicalRiskIndicators", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id}, name={self.first_name} {self.last_name})>"


class BloodParameters(Base):
    """Blood test parameters"""
    __tablename__ = 'blood_parameters'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Complete Blood Count (CBC)
    hemoglobin = Column(Float)  # g/dL
    hematocrit = Column(Float)  # %
    white_blood_cells = Column(Float)  # cells/μL
    red_blood_cells = Column(Float)  # cells/μL
    platelets = Column(Float)  # cells/μL
    
    # Metabolic Panel
    glucose = Column(Float)  # mg/dL
    creatinine = Column(Float)  # mg/dL
    bun = Column(Float)  # Blood Urea Nitrogen, mg/dL
    alt = Column(Float)  # Alanine Aminotransferase, U/L
    ast = Column(Float)  # Aspartate Aminotransferase, U/L
    
    # Lipid Panel
    total_cholesterol = Column(Float)  # mg/dL
    hdl_cholesterol = Column(Float)  # mg/dL
    ldl_cholesterol = Column(Float)  # mg/dL
    triglycerides = Column(Float)  # mg/dL
    
    # Thyroid Function
    tsh = Column(Float)  # Thyroid Stimulating Hormone, mIU/L
    t3 = Column(Float)  # Triiodothyronine, ng/dL
    t4 = Column(Float)  # Thyroxine, μg/dL
    
    # Other
    ferritin = Column(Float)  # ng/mL
    iron = Column(Float)  # μg/dL
    transferrin = Column(Float)  # mg/dL
    
    # Protein Levels
    total_protein = Column(Float)  # g/dL
    albumin = Column(Float)  # g/dL
    globulin = Column(Float)  # g/dL
    a_g_ratio = Column(Float)  # Albumin/Globulin ratio
    c_reactive_protein = Column(Float)  # mg/L (CRP - inflammation marker)
    hemoglobin_a1c = Column(Float)  # % (HbA1c - diabetes marker)
    
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="blood_parameters")
    
    def __repr__(self):
        return f"<BloodParameters(patient_id={self.patient_id}, date={self.test_date})>"


class ReproductiveHealth(Base):
    """Reproductive health information"""
    __tablename__ = 'reproductive_health'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    record_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Menstrual Cycle
    last_menstrual_period = Column(Date)
    cycle_length = Column(Integer)  # days
    period_duration = Column(Integer)  # days
    menstrual_regularity = Column(String(20))  # Regular, Irregular, Amenorrhea
    
    # Hormone Levels
    fsh = Column(Float)  # Follicle Stimulating Hormone, mIU/mL
    lh = Column(Float)  # Luteinizing Hormone, mIU/mL
    estradiol = Column(Float)  # pg/mL
    progesterone = Column(Float)  # ng/mL
    testosterone = Column(Float)  # ng/dL
    prolactin = Column(Float)  # ng/mL
    
    # Pregnancy Related
    pregnancy_status = Column(String(20))  # Not Pregnant, Pregnant, Postpartum
    weeks_pregnant = Column(Integer)
    due_date = Column(Date)
    
    # Contraception
    contraception_method = Column(String(50))
    
    # Other
    pcos_diagnosis = Column(Boolean, default=False)
    endometriosis = Column(Boolean, default=False)
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="reproductive_health")
    
    def __repr__(self):
        return f"<ReproductiveHealth(patient_id={self.patient_id}, date={self.record_date})>"


class GynecologicalRiskIndicators(Base):
    """Indicators for patients prone to gynecological conditions"""
    __tablename__ = 'gynecological_risk_indicators'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    record_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Family History
    family_history_ovarian_cancer = Column(Boolean, default=False)
    family_history_breast_cancer = Column(Boolean, default=False)
    family_history_cervical_cancer = Column(Boolean, default=False)
    family_history_endometrial_cancer = Column(Boolean, default=False)
    family_history_details = Column(Text)  # Details about affected relatives
    
    # Personal History
    personal_history_breast_cancer = Column(Boolean, default=False)
    personal_history_ovarian_cancer = Column(Boolean, default=False)
    personal_history_cervical_cancer = Column(Boolean, default=False)
    personal_history_endometrial_cancer = Column(Boolean, default=False)
    
    # Reproductive Risk Factors
    age_at_menarche = Column(Integer)  # Age at first period
    age_at_menopause = Column(Integer)  # Age at menopause (if applicable)
    nulliparity = Column(Boolean, default=False)  # Never given birth
    number_of_pregnancies = Column(Integer)
    first_pregnancy_age = Column(Integer)
    breastfeeding_history = Column(Boolean, default=False)
    breastfeeding_duration_months = Column(Integer)
    
    # Hormonal Factors
    hormone_replacement_therapy = Column(Boolean, default=False)
    hrt_duration_years = Column(Float)
    oral_contraceptive_use = Column(Boolean, default=False)
    oc_duration_years = Column(Float)
    
    # Lifestyle Risk Factors
    smoking_history = Column(Boolean, default=False)
    smoking_pack_years = Column(Float)
    alcohol_consumption_weekly = Column(Float)  # drinks per week
    physical_activity_level = Column(String(50))  # Sedentary, Light, Moderate, Active
    bmi = Column(Float)  # Body Mass Index
    
    # Medical Conditions
    diabetes = Column(Boolean, default=False)
    hypertension = Column(Boolean, default=False)
    autoimmune_diseases = Column(String(200))  # List of autoimmune conditions
    
    # Previous Gynecological Procedures
    previous_gynecological_surgery = Column(Boolean, default=False)
    gynecological_surgery_type = Column(String(200))  # Type of surgery
    abnormal_pap_smear_history = Column(Boolean, default=False)
    cervical_dysplasia_history = Column(Boolean, default=False)
    
    # Biomarkers and Screening Results
    ca125_level = Column(Float)  # Cancer antigen 125 (ovarian cancer marker)
    ca125_test_date = Column(Date)
    he4_level = Column(Float)  # Human epididymis protein 4
    he4_test_date = Column(Date)
    roma_index = Column(Float)  # Risk of Ovarian Malignancy Algorithm
    roma_test_date = Column(Date)
    
    # Screening Dates
    last_mammogram_date = Column(Date)
    mammogram_results = Column(String(100))  # Normal, Abnormal, Suspicious
    last_pap_smear_date = Column(Date)
    pap_smear_results = Column(String(100))  # Normal, ASCUS, LSIL, HSIL, etc.
    last_pelvic_ultrasound_date = Column(Date)
    pelvic_ultrasound_results = Column(Text)
    next_screening_due_date = Column(Date)
    
    # Risk Assessment
    overall_risk_level = Column(String(50))  # Low, Moderate, High, Very High
    risk_factors_summary = Column(Text)  # Summary of identified risk factors
    recommended_screening_schedule = Column(Text)  # Recommended screening frequency
    
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="gynecological_risk_indicators")
    
    def __repr__(self):
        return f"<GynecologicalRiskIndicators(patient_id={self.patient_id}, date={self.record_date})>"


class VitaminLevels(Base):
    """Vitamin levels tracking over time"""
    __tablename__ = 'vitamin_levels'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Fat-Soluble Vitamins
    vitamin_a = Column(Float)  # μg/dL
    vitamin_d = Column(Float)  # ng/mL
    vitamin_e = Column(Float)  # mg/dL
    vitamin_k = Column(Float)  # ng/mL
    
    # Water-Soluble Vitamins
    vitamin_b1 = Column(Float)  # Thiamine, ng/mL
    vitamin_b2 = Column(Float)  # Riboflavin, ng/mL
    vitamin_b3 = Column(Float)  # Niacin, ng/mL
    vitamin_b5 = Column(Float)  # Pantothenic Acid, μg/mL
    vitamin_b6 = Column(Float)  # Pyridoxine, ng/mL
    vitamin_b7 = Column(Float)  # Biotin, ng/mL
    vitamin_b9 = Column(Float)  # Folate/Folic Acid, ng/mL
    vitamin_b12 = Column(Float)  # Cobalamin, pg/mL
    vitamin_c = Column(Float)  # Ascorbic Acid, mg/dL
    
    # Status tracking (calculated fields)
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="vitamin_levels")
    
    def __repr__(self):
        return f"<VitaminLevels(patient_id={self.patient_id}, date={self.test_date})>"


class MicronutrientLevels(Base):
    """Micronutrient levels tracking"""
    __tablename__ = 'micronutrient_levels'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Minerals
    calcium = Column(Float)  # mg/dL
    magnesium = Column(Float)  # mg/dL
    phosphorus = Column(Float)  # mg/dL
    potassium = Column(Float)  # mEq/L
    sodium = Column(Float)  # mEq/L
    zinc = Column(Float)  # μg/dL
    selenium = Column(Float)  # μg/L
    copper = Column(Float)  # μg/dL
    manganese = Column(Float)  # μg/L
    chromium = Column(Float)  # μg/L
    molybdenum = Column(Float)  # μg/L
    
    # Other Micronutrients
    omega_3 = Column(Float)  # mg/dL
    omega_6 = Column(Float)  # mg/dL
    coenzyme_q10 = Column(Float)  # μg/mL
    
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="micronutrient_levels")
    
    def __repr__(self):
        return f"<MicronutrientLevels(patient_id={self.patient_id}, date={self.test_date})>"


class Medication(Base):
    """Medication requirements and prescriptions"""
    __tablename__ = 'medications'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))  # e.g., "Once daily", "Twice daily"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # None if ongoing
    prescribing_physician = Column(String(200))
    reason = Column(Text)  # Indication for medication
    is_active = Column(Boolean, default=True)
    discontinuation_reason = Column(Text)  # Reason for discontinuation
    discontinuation_date = Column(Date)  # Date medication was discontinued
    status = Column(String(50), default='Active')  # Active, Discontinued, Inactive, On Hold
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="medications")
    
    def __repr__(self):
        return f"<Medication(patient_id={self.patient_id}, name={self.medication_name})>"


class GeneticData(Base):
    """Genetic information and test results"""
    __tablename__ = 'genetic_data'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow)
    test_type = Column(String(100))  # e.g., "BRCA1/2", "MTHFR", "Pharmacogenomics"
    test_provider = Column(String(200))
    
    # Common genetic variants
    mthfr_c677t = Column(String(20))  # CC, CT, TT
    mthfr_a1298c = Column(String(20))  # AA, AC, CC
    brca1_mutation = Column(Boolean)
    brca2_mutation = Column(Boolean)
    
    # Raw genetic data (JSON-like storage)
    raw_data = Column(Text)  # Store JSON or other format
    
    # Interpretation
    interpretation = Column(Text)
    clinical_significance = Column(Text)
    recommendations = Column(Text)
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="genetic_data")
    
    def __repr__(self):
        return f"<GeneticData(patient_id={self.patient_id}, type={self.test_type})>"


class PatientNeeds(Base):
    """Individual patient needs and requirements"""
    __tablename__ = 'patient_needs'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    record_date = Column(Date, nullable=False, default=datetime.utcnow)
    
    # Dietary Needs
    dietary_restrictions = Column(Text)  # Allergies, intolerances, preferences
    special_diet = Column(String(100))  # e.g., "Vegetarian", "Keto", "Low-sodium"
    
    # Activity Level
    activity_level = Column(String(50))  # Sedentary, Light, Moderate, Active, Very Active
    
    # Health Goals
    health_goals = Column(Text)
    
    # Special Requirements
    special_requirements = Column(Text)  # Any other specific needs
    
    # Lifestyle Factors
    smoking_status = Column(String(20))  # Never, Former, Current
    alcohol_consumption = Column(String(50))
    sleep_hours = Column(Float)
    
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="patient_needs")
    
    def __repr__(self):
        return f"<PatientNeeds(patient_id={self.patient_id}, date={self.record_date})>"

