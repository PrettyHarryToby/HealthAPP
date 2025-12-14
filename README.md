# Health Database Application for Female Patients

A comprehensive Python-based health database application designed specifically for tracking and managing clinical data for female patients. The system stores and analyzes blood parameters, reproductive health information, vitamin and micronutrient levels, medications, genetic data, and individual patient needs.

## 📚 Documentation

- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Complete setup and developer guide ⭐ **START HERE FOR DEVELOPERS**
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Detailed development documentation and code patterns
- **[SETUP.md](SETUP.md)** - Quick setup guide (5 minutes)
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app_web.py

# 3. Open browser to http://localhost:5000
```

## Features

### Core Functionality

- **Patient Management**: Complete patient information system with unique patient IDs
- **Blood Parameters Tracking**: Store and track comprehensive blood test results including:
  - Complete Blood Count (CBC)
  - Metabolic Panel
  - Lipid Panel
  - Thyroid Function Tests
  - Iron Studies
  - **Protein Levels** (Total Protein, Albumin, Globulin, A/G Ratio, CRP, HbA1c)

- **Reproductive Health**: Track menstrual cycles, hormone levels, pregnancy status, and reproductive health conditions

- **Vitamin Level Tracking**: Continuous monitoring of all vitamins (A, D, E, K, B-complex, C) with:
  - Automatic deficiency/excess detection
  - Trend analysis over time
  - Reference range comparisons

- **Micronutrient Monitoring**: Track essential minerals and nutrients including:
  - Calcium, Magnesium, Phosphorus
  - Potassium, Sodium
  - Zinc, Selenium, Copper, Manganese, Chromium, Molybdenum
  - Omega-3, Omega-6, Coenzyme Q10

- **Medication Management**: Track prescriptions, dosages, frequencies, and medication history
  - **Active Medications**
  - **Inactive/Discontinued Medications** with discontinuation reasons

- **Genetic Data Storage**: Store genetic test results including:
  - MTHFR variants (C677T, A1298C)
  - BRCA1/BRCA2 mutations
  - Custom genetic test data
  - Clinical interpretations and recommendations

- **Gynecological Risk Indicators**: Comprehensive risk assessment including:
  - Family and personal cancer history
  - Reproductive risk factors
  - Biomarkers (CA-125, HE4, ROMA)
  - Screening dates and results
  - Risk level assessment

- **Patient Needs**: Document individual patient requirements including:
  - Dietary restrictions and preferences
  - Activity levels
  - Health goals
  - Lifestyle factors

### Analysis & Insights

- **Automated Deficiency Detection**: Identifies vitamins and micronutrients below reference ranges
- **Excess Level Alerts**: Flags elevated levels that may require attention
- **Trend Analysis**: Tracks changes in vitamin/micronutrient levels over time
- **Genetic-Based Recommendations**: Provides insights based on genetic variants (e.g., MTHFR mutations affecting folate metabolism)
- **Medication Recommendations**: Suggests supplements based on detected deficiencies
- **Comprehensive Health Reports**: Generates detailed insights combining all available data

### Advanced Dashboard

- **Real-time Statistics**: Patient counts, medication tracking, test activity
- **Health Profiling**: 
  - Patients with protein level issues
  - Patients with inactive/discontinued medications
  - Patients with gynecological risk indicators
- **Quick Access**: Direct links to patient records and insights

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone or download the application files**

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   **Option 1: Web Application (Recommended)**
   ```bash
   python app_web.py
   ```
   Then open your browser and navigate to: **http://localhost:5000**
   
   **Option 2: Desktop GUI Application**
   ```bash
   python app.py
   ```

The application will automatically create a SQLite database file (`health_database.db`) on first run.

## Usage Guide

### Getting Started

1. **Add a Patient**: 
   - Go to the "Patients" tab
   - Fill in patient information (Patient ID is required and must be unique)
   - Click "Add New"

2. **Enter Clinical Data**:
   - Select a patient from the dropdown in any data entry tab
   - Fill in the relevant information
   - Click "Save" to store the data

3. **View Insights**:
   - Go to the "Insights & Analysis" tab
   - Select a patient
   - Click "Generate Insights" to see comprehensive health analysis

### Data Entry Tips

- **Dates**: Use YYYY-MM-DD format (e.g., 2024-01-15)
- **Numeric Values**: Enter only numbers for test results (decimals allowed)
- **Optional Fields**: Leave fields blank if data is not available
- **Patient Selection**: Always select a patient before entering data in other tabs

### Understanding Insights

The Insights tab provides:

- **Deficiencies**: Vitamins/micronutrients below normal ranges with percentage below normal
- **Excesses**: Elevated levels above normal ranges
- **Trends**: Whether levels are increasing, decreasing, or stable over time
- **Genetic Insights**: Implications of genetic variants on health and supplementation
- **Recommendations**: Actionable suggestions based on all available data

## Database Structure

The application uses SQLite database with the following main tables:

- `patients`: Patient demographic information
- `blood_parameters`: Blood test results (including protein levels)
- `reproductive_health`: Reproductive health records
- `vitamin_levels`: Vitamin test results with timestamps
- `micronutrient_levels`: Micronutrient test results
- `medications`: Medication prescriptions and history (with status tracking)
- `genetic_data`: Genetic test results
- `patient_needs`: Individual patient requirements
- `gynecological_risk_indicators`: Risk assessment data

## Reference Ranges

The application uses standard medical reference ranges for vitamins and micronutrients. These can be customized in `analysis.py` if needed.

### Example Reference Ranges:
- **Vitamin D**: 30-100 ng/mL (optimal range)
- **Vitamin B12**: 200-900 pg/mL
- **Folate (B9)**: 4-20 ng/mL
- **Calcium**: 8.5-10.5 mg/dL
- **Magnesium**: 1.7-2.2 mg/dL

### Protein Reference Ranges:
- **Total Protein**: 6.0-8.3 g/dL
- **Albumin**: 3.5-5.0 g/dL
- **C-Reactive Protein**: <3.0 mg/L (normal)
- **Hemoglobin A1c**: <5.7% (normal)

## Important Notes

- **Data Privacy**: This application stores sensitive health information. Ensure proper security measures are in place
- **Backup**: Regularly backup the `health_database.db` file
- **Medical Disclaimer**: This application is a data management tool and does not provide medical advice. Always consult healthcare professionals for medical decisions
- **Patient ID**: Patient IDs must be unique and are used as the primary identifier

## Troubleshooting

### Database Errors
- If you encounter database errors, ensure you have write permissions in the application directory
- Run `python migrate_database.py` to update database schema
- Delete `health_database.db` to reset the database (WARNING: This will delete all data)

### Date Format Errors
- Always use YYYY-MM-DD format for dates
- Example: 2024-01-15 (not 01/15/2024 or 15-01-2024)

### Patient Selection Issues
- Click "Refresh Patients" if patient list doesn't update
- Ensure patient is added in the Patients tab before entering other data

### Port Already in Use
- Change port in `app_web.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`

## For Developers

See **[HOW_TO_RUN.md](HOW_TO_RUN.md)** for complete developer documentation including:
- Project structure
- Code organization
- Adding new features
- Database management
- Performance optimization
- Testing guidelines

## Future Enhancements

Potential features for future versions:
- Export reports to PDF
- Data visualization charts and graphs
- Multi-user support with authentication
- Cloud database integration
- Mobile app companion
- Integration with lab systems
- Automated reminder system for follow-up tests

## License

This application is provided as-is for health data management purposes.

## Support

For issues or questions:
1. Check `HOW_TO_RUN.md` for setup issues
2. Review `DEVELOPER_GUIDE.md` for development questions
3. Check error messages in terminal/console
4. Verify database schema with `python verify_database.py`
