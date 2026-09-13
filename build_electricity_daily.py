import pandas as pd
from pathlib import Path

# -------------------------------------------------
# PATHS
# -------------------------------------------------

base_folder = Path(__file__).parent
processed_folder = base_folder / "Processed_Data"

input_file = (
    processed_folder
    / "electricity_15min_all_houses.csv"
)

output_file = (
    processed_folder
    / "electricity_daily_all_houses.csv"
)

quality_file = (
    processed_folder
    / "electricity_daily_quality_summary.csv"
)


# -------------------------------------------------
# READ 15-MINUTE DATA
# -------------------------------------------------

print("Reading:")
print(input_file)
print()

df = pd.read_csv(input_file)

df["timestamp_15min"] = pd.to_datetime(
    df["timestamp_15min"]
)

# Create calendar date
df["date"] = (
    df["timestamp_15min"]
    .dt.date
)


# -------------------------------------------------
# PREPARE WEIGHTED POWER CALCULATION
# -------------------------------------------------

# Used so incomplete 15-minute intervals
# do not receive the same weight as complete ones
df["weighted_power"] = (
    df["avg_total_power_w"]
    * df["sample_count"]
)


# -------------------------------------------------
# AGGREGATE TO HOUSE + DAY
# -------------------------------------------------

daily = (
    df.groupby(
        ["house_id", "date"],
        as_index=False
    )
    .agg(
        total_energy_kwh=(
            "energy_kwh",
            "sum"
        ),

        weighted_power_sum=(
            "weighted_power",
            "sum"
        ),

        max_power_w=(
            "max_total_power_w",
            "max"
        ),

        issue_count=(
            "issue_count",
            "sum"
        ),

        sample_count=(
            "sample_count",
            "sum"
        ),

        interval_count=(
            "timestamp_15min",
            "count"
        )
    )
)


# -------------------------------------------------
# CALCULATE DAILY KPIs
# -------------------------------------------------

# Weighted average power
daily["avg_power_w"] = (
    daily["weighted_power_sum"]
    / daily["sample_count"]
)

# Daily issue rate
daily["issue_rate"] = (
    daily["issue_count"]
    / daily["sample_count"]
)

# A complete day should contain 96 x 15-minute intervals
daily["data_coverage_pct"] = (
    daily["interval_count"]
    / 96
    * 100
)

# Prevent values above 100% in case
# an unexpected duplicate ever appears
daily["data_coverage_pct"] = (
    daily["data_coverage_pct"]
    .clip(upper=100)
)

# Remove helper column
daily = daily.drop(
    columns=["weighted_power_sum"]
)


# -------------------------------------------------
# ROUND DISPLAY VALUES
# -------------------------------------------------

daily["total_energy_kwh"] = (
    daily["total_energy_kwh"]
    .round(4)
)

daily["avg_power_w"] = (
    daily["avg_power_w"]
    .round(3)
)

daily["max_power_w"] = (
    daily["max_power_w"]
    .round(3)
)

daily["issue_rate"] = (
    daily["issue_rate"]
    .round(6)
)

daily["data_coverage_pct"] = (
    daily["data_coverage_pct"]
    .round(2)
)


# -------------------------------------------------
# COLUMN ORDER
# -------------------------------------------------

daily = daily[
    [
        "house_id",
        "date",
        "total_energy_kwh",
        "avg_power_w",
        "max_power_w",
        "issue_count",
        "sample_count",
        "issue_rate",
        "interval_count",
        "data_coverage_pct"
    ]
]


# -------------------------------------------------
# SORT
# -------------------------------------------------

daily = daily.sort_values(
    ["house_id", "date"]
).reset_index(drop=True)


# -------------------------------------------------
# QUALITY CHECKS
# -------------------------------------------------

duplicate_count = (
    daily[
        ["house_id", "date"]
    ]
    .duplicated()
    .sum()
)

incomplete_days = (
    daily["interval_count"] < 96
).sum()

full_days = (
    daily["interval_count"] == 96
).sum()

quality_summary = pd.DataFrame(
    [
        {
            "total_houses":
                daily["house_id"].nunique(),

            "total_daily_rows":
                len(daily),

            "start_date":
                daily["date"].min(),

            "end_date":
                daily["date"].max(),

            "duplicate_house_date":
                duplicate_count,

            "full_days":
                full_days,

            "incomplete_days":
                incomplete_days,

            "min_data_coverage_pct":
                daily[
                    "data_coverage_pct"
                ].min()
        }
    ]
)


# -------------------------------------------------
# SAVE FILES
# -------------------------------------------------

daily.to_csv(
    output_file,
    index=False
)

quality_summary.to_csv(
    quality_file,
    index=False
)


# -------------------------------------------------
# RESULTS
# -------------------------------------------------

print("===================================")
print("PROCESS COMPLETED")
print("===================================")

print(
    "Total houses:",
    daily["house_id"].nunique()
)

print(
    "Total daily rows:",
    len(daily)
)

print(
    "Duplicate house/date:",
    duplicate_count
)

print(
    "Full days:",
    full_days
)

print(
    "Incomplete days:",
    incomplete_days
)

print()
print("Daily dataset created:")
print(output_file)

print()
print("Quality summary created:")
print(quality_file)