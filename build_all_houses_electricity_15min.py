import pandas as pd
from pathlib import Path

# Main folder containing House_01 ... House_13
base_folder = Path(__file__).parent

all_houses = []
quality_summary = []

# Find all house folders
house_folders = sorted(base_folder.glob("House_*"))

print("Houses found:", len(house_folders))
print()


for house_folder in house_folders:

    house_id = house_folder.name
    electric_folder = house_folder / "Electric_data"

    print("===================================")
    print("Processing:", house_id)

    # Find monthly electricity files only
    monthly_files = sorted(
        electric_folder.glob("20??-??.csv")
    )

    print("Monthly files:", len(monthly_files))

    # Skip house if no monthly files exist
    if len(monthly_files) == 0:
        print("No monthly electricity files found.")
        print()
        continue

    house_months = []

    months_without_voltage = 0
    months_without_current = 0


    for input_file in monthly_files:

        print("  Processing:", input_file.name)

        # Read the whole monthly CSV because
        # not every house contains the same columns
        df = pd.read_csv(input_file)

        # Required columns for this analysis
        required_columns = [
            "timestamp",
            "P_agg",
            "issues"
        ]

        missing_required = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_required:
            raise ValueError(
                f"{house_id} - {input_file.name}: "
                f"Missing required columns: {missing_required}"
            )

        # Check optional Voltage and Current columns
        has_voltage = "V" in df.columns
        has_current = "A" in df.columns

        if not has_voltage:
            months_without_voltage += 1
            print("    Note: V column not available")

        if not has_current:
            months_without_current += 1
            print("    Note: A column not available")

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        # Assign each 10-second measurement
        # to a 15-minute interval
        df["timestamp_15min"] = (
            df["timestamp"].dt.floor("15min")
        )

        # Basic aggregations available for every house
        aggregation_rules = {
            "avg_total_power_w": (
                "P_agg",
                "mean"
            ),
            "max_total_power_w": (
                "P_agg",
                "max"
            ),
            "issue_count": (
                "issues",
                "sum"
            ),
            "sample_count": (
                "timestamp",
                "count"
            )
        }

        # Add Voltage only when available
        if has_voltage:
            aggregation_rules[
                "avg_voltage_v"
            ] = ("V", "mean")

        # Add Current only when available
        if has_current:
            aggregation_rules[
                "avg_current_a"
            ] = ("A", "mean")

        # Aggregate to 15-minute level
        month_15min = (
            df.groupby("timestamp_15min")
            .agg(**aggregation_rules)
            .reset_index()
        )

        # If Voltage or Current were unavailable,
        # create the columns with missing values
        if not has_voltage:
            month_15min[
                "avg_voltage_v"
            ] = float("nan")

        if not has_current:
            month_15min[
                "avg_current_a"
            ] = float("nan")

        # Add house identifier
        month_15min.insert(
            0,
            "house_id",
            house_id
        )

        # Calculate energy consumption in kWh
        # based on the actual number of 10-second samples
        month_15min["energy_kwh"] = (
            month_15min["avg_total_power_w"]
            * month_15min["sample_count"]
            * 10
            / 3_600_000
        )

        # Calculate proportion of flagged samples
        month_15min["issue_rate"] = (
            month_15min["issue_count"]
            / month_15min["sample_count"]
        )

        # Keep the same column order for every house
        month_15min = month_15min[
            [
                "house_id",
                "timestamp_15min",
                "avg_voltage_v",
                "avg_current_a",
                "avg_total_power_w",
                "max_total_power_w",
                "energy_kwh",
                "issue_count",
                "sample_count",
                "issue_rate"
            ]
        ]

        house_months.append(month_15min)


    # Combine all months for this house
    house_data = pd.concat(
        house_months,
        ignore_index=True
    )

    # Sort chronologically
    house_data = house_data.sort_values(
        "timestamp_15min"
    ).reset_index(drop=True)


    # -----------------------------
    # QUALITY CHECKS
    # -----------------------------

    duplicate_count = (
        house_data["timestamp_15min"]
        .duplicated()
        .sum()
    )

    incomplete_intervals = (
        house_data["sample_count"] != 90
    ).sum()

    intervals_with_issues = (
        house_data["issue_count"] > 0
    ).sum()

    max_issue_rate = (
        house_data["issue_rate"].max()
    )

    # Build expected complete 15-minute timeline
    expected_timestamps = pd.date_range(
        start=house_data[
            "timestamp_15min"
        ].min(),
        end=house_data[
            "timestamp_15min"
        ].max(),
        freq="15min"
    )

    actual_timestamps = pd.DatetimeIndex(
        house_data["timestamp_15min"]
    )

    missing_timestamps = (
        expected_timestamps.difference(
            actual_timestamps
        )
    )

    missing_intervals = len(
        missing_timestamps
    )


    # Store quality summary
    quality_summary.append(
        {
            "house_id": house_id,
            "rows_15min": len(house_data),
            "start_date": house_data[
                "timestamp_15min"
            ].min(),
            "end_date": house_data[
                "timestamp_15min"
            ].max(),
            "duplicate_timestamps":
                duplicate_count,
            "missing_intervals":
                missing_intervals,
            "incomplete_intervals":
                incomplete_intervals,
            "intervals_with_issues":
                intervals_with_issues,
            "max_issue_rate":
                max_issue_rate,
            "months_without_voltage":
                months_without_voltage,
            "months_without_current":
                months_without_current
        }
    )

    all_houses.append(house_data)


    # Display house-level checks
    print("15-minute rows:", len(house_data))
    print(
        "Missing intervals:",
        missing_intervals
    )
    print(
        "Incomplete intervals:",
        incomplete_intervals
    )
    print(
        "Duplicates:",
        duplicate_count
    )
    print(
        "Months without Voltage:",
        months_without_voltage
    )
    print(
        "Months without Current:",
        months_without_current
    )

    if missing_intervals > 0:
        print(
            "First missing timestamps:",
            list(missing_timestamps[:5])
        )

    print()


# -----------------------------
# COMBINE ALL HOUSES
# -----------------------------

electricity_all_houses = pd.concat(
    all_houses,
    ignore_index=True
)

electricity_all_houses = (
    electricity_all_houses
    .sort_values(
        [
            "house_id",
            "timestamp_15min"
        ]
    )
    .reset_index(drop=True)
)


# -----------------------------
# CREATE OUTPUT FOLDER
# -----------------------------

output_folder = (
    base_folder / "Processed_Data"
)

output_folder.mkdir(
    exist_ok=True
)


# -----------------------------
# SAVE ELECTRICITY DATASET
# -----------------------------

electricity_output = (
    output_folder
    / "electricity_15min_all_houses.csv"
)

electricity_all_houses.to_csv(
    electricity_output,
    index=False
)


# -----------------------------
# SAVE QUALITY SUMMARY
# -----------------------------

quality_df = pd.DataFrame(
    quality_summary
)

quality_output = (
    output_folder
    / "electricity_quality_summary.csv"
)

quality_df.to_csv(
    quality_output,
    index=False
)


# -----------------------------
# FINAL RESULTS
# -----------------------------

print("===================================")
print("PROCESS COMPLETED")
print("===================================")

print(
    "Total houses:",
    electricity_all_houses[
        "house_id"
    ].nunique()
)

print(
    "Total 15-minute rows:",
    len(electricity_all_houses)
)

print()
print("Electricity dataset created:")
print(electricity_output)

print()
print("Quality summary created:")
print(quality_output)