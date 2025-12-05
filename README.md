# BMI706_project
# Global Tuberculosis Analytics Dashboard  
Visualizing TB Burden, Treatment Coverage, Drug Resistance, and HIV Co-infection Using WHO Data (2017–2025)

This Streamlit dashboard provides interactive analyses of key global tuberculosis indicators using data from the World Health Organization (WHO). The application incorporates epidemiological metrics such as incidence, mortality, treatment coverage, rifampicin-resistant tuberculosis (RR-TB), and TB/HIV co-infection. It supports comparisons across countries, WHO regions, and development status groups.

---

## Analytical Tasks and Visualizations

### Task 1: Global and Regional TB Incidence and Mortality (2017–2023)  
This task examines trends in TB incidence and mortality per 100,000 population. The application compares the global average to individual WHO regions and includes optional 95% confidence interval bands. Users can switch regions, toggle indicators (incidence and/or mortality), and choose whether to display uncertainty intervals.

### Task 2: Cross-Country Reduction in TB Incidence (2017–2023)  
This task presents a choropleth world map illustrating the percentage reduction in TB incidence over six years. Darker shades indicate greater decreases. A region filter allows users to focus on specific WHO regions. Hover tooltips provide detailed statistics, including incidence values for 2017 and 2023 and the calculated reduction percentage.

### Task 3: Global TB Treatment Coverage Trends and Comparisons  
This task analyzes TB treatment coverage (%) over time, across countries, and by development status. Panel A displays line trends with confidence intervals for up to eight user-selected countries. Panel B ranks the top five countries for any selected year. A dual heatmap compares treatment coverage between developed countries and the lowest-performing developing countries. Tooltips enable precise value inspection, and a download option provides access to the underlying dataset.

### Task 4: Relationship Between TB Burden and Rifampicin-Resistance (RR-TB) (2015–2023)  
This task compares TB incidence trends with RR-TB prevalence among new and previously treated cases. The visualization overlays these indicators to explore whether drug resistance declines in parallel with overall disease burden. A confidence interval band highlights uncertainty in incidence estimates. A region selector enables multi-region comparisons.

### Task 5: TB/HIV Co-Infection Surveillance  
This task visualizes co-infection prevalence using three coordinated components: a choropleth map, a regional boxplot, and an expandable summary table. Users can switch among survey-based, sentinel-based, and combined datasets. Clicking a country highlights the corresponding WHO region in both visualizations, enabling linked spatial and statistical inference.

---

## Data Source and Preprocessing

### Data Source
All datasets originate from the World Health Organization’s Global TB Programme. Data include annual TB burden estimates, country-level treatment coverage, rifampicin-resistant TB metrics, and non-routine HIV surveillance indicators.

### Preprocessing Overview
Data were standardized to consistent column names and time ranges (2015–2025 depending on dataset). Numeric fields were converted, invalid entries removed, WHO regions mapped, and countries classified as developed or developing where applicable. For Task 4, incidence and RR-TB datasets were merged by year. For Task 5, survey and sentinel datasets were cleaned, deduplicated by most recent measurement, and merged into a unified long format.

---

## Installation and Running the Application

To set up and run the application locally:

```bash
# Clone the repository
git clone https://github.com/YOUR_REPO_NAME/tb-dashboard.git
cd tb-dashboard

# Install required dependencies
pip install -r requirements.txt

# Run the Streamlit application locally
streamlit run app.py
