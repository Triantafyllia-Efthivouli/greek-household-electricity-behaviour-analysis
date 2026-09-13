# Greek Household Electricity Consumption & Behaviour Analysis

## Project Overview

This project analyses household electricity consumption and behaviour using the Plegma smart-meter dataset.

The analysis combines Python, SQL and Power BI to examine electricity consumption patterns, appliance behaviour, seasonality, daily demand profiles and the relationship between outdoor temperature and household energy use.

The final Power BI report includes both Greek and English dashboard pages.

## Project Objectives

The main objectives of the project were to:

- Analyse household electricity consumption patterns.
- Compare average daily electricity consumption across households.
- Examine seasonal differences in electricity demand.
- Identify the daily electricity demand profile.
- Analyse electricity consumption by appliance.
- Compare appliance operating times.
- Explore the relationship between outdoor temperature and electricity consumption.
- Build an interactive Power BI dashboard suitable for portfolio presentation.

## Dataset

The project uses the Plegma household smart-meter dataset.

The analysed sample contains:

- 13 households
- Electricity consumption measurements
- Appliance-level measurements
- Environmental measurements
- Household characteristics

The source data was transformed into analytical datasets at 15-minute and daily granularity.

## Data Workflow

The project followed the workflow:

**Raw smart-meter data → Python preprocessing → 15-minute analytical layer → Daily SQL layer → Oracle SQL analysis → Power BI dashboard**

### Python

Python was used for:

- Combining data from multiple households
- Data cleaning and preprocessing
- Timestamp transformation
- Aggregation into 15-minute intervals
- Data-quality checks
- Preparation of analytical CSV files

### SQL

Oracle SQL was used to create a structured daily analytical layer and perform exploratory analysis.

Two analytical views were created:

- `VW_PLEGMA_DAILY_ANALYTICS`
- `VW_PLEGMA_APPLIANCE_ANALYTICS`

These views combine household characteristics with electricity, environmental and appliance data.

### Power BI

Power BI was used for:

- Data modelling
- Relationships between household, date and fact tables
- DAX measures
- Interactive filtering
- Household comparisons
- Seasonality analysis
- Hourly demand analysis
- Appliance behaviour analysis
- Temperature-impact analysis

## Dashboard

The Power BI report contains four pages:

### Greek Version

1. **Κύρια Επισκόπηση Κατανάλωσης**
2. **Συσκευές & Περιβαλλοντικοί Παράγοντες**

### English Version

3. **Consumption Overview**
4. **Appliances & Environmental Factors**

The dashboards include interactive filters for households, months, seasons and appliances.

## Key Findings

- Electricity consumption increases at temperature extremes. Average daily consumption reaches approximately **13.92 kWh below 10°C** and **13.82 kWh above 30°C**.
- **House_11** records the highest average daily electricity consumption at approximately **17.46 kWh/day**.
- Boiler usage is an important contributor to appliance electricity consumption, particularly during colder conditions.
- Air-conditioner consumption increases strongly at high outdoor temperatures.
- Refrigerators have some of the longest daily operating times, demonstrating that longer operating time does not necessarily correspond to the highest energy consumption.
- The daily electricity demand profile increases during the day and reaches its highest levels during the late afternoon and early evening.

## Data Quality

Data-quality checks were included throughout the analysis.

Incomplete measurements were not automatically deleted or artificially imputed.

Coverage indicators were retained and used when calculating analytical metrics so that incomplete observation periods could be identified and handled appropriately.

## Limitations

The dataset contains measurements from only **13 households**.

Therefore, the findings describe patterns observed within this specific sample and should not be interpreted as representative of all Greek households.

Observation periods and monitored appliance availability also vary between households.

## Tools & Technologies

- Python
- Pandas
- Oracle SQL
- Oracle APEX
- Power BI
- Power Query
- DAX
- GitHub

## Skills Demonstrated

- Data preprocessing
- Data-quality analysis
- SQL data modelling
- Exploratory data analysis
- Power BI data modelling
- DAX measures
- Dashboard development
- Energy consumption analysis
- Behavioural energy analysis
- Data storytelling

## Dashboard Preview

Dashboard screenshots will be added here.

## Author

**Triantafillia Efthivouli**

Energy & Data Analytics Portfolio Project
