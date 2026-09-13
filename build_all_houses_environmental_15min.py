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
    environmental_folder = house_folder / "Environmental_data"

    print("===================================")
    print("Processing:", house_id)

    # Find monthly environmental CSV files
    monthly_files = sorted(
        environmental_folder.glob("20??-??.csv")
    )

    print("Monthly files:", len(monthly_files))

    if len(monthly_files) == 0:
        print("No environmental files found.")
        print()
        continue

    house_months = []


    for input_file in monthly_files:

        print("  Processing:", input_file.name)

        df = pd.read_csv(input_file)

        # Remove accidental spaces from column names
        df.columns = df.columns.str.strip()

        # Correct typo used in the original Plegma files
        if "external_temparature" in df.columns:
            df = df.rename(
                columns={
                    "external_temparature":
                    "external_temperature"
                }
            )

        # Required columns
        required_columns = [
            "timestamp",
            "internal_temperature",
            "internal_humidity",
            "external_temperature",
            "external_humidity"
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

        # Keep only fields needed for analysis
        df = df[required_columns].copy()

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        # Add house identifier
        df.insert(
            0,
            "house_id",
            house_id
        )

        # Rename columns for SQL-ready dataset
        df = df.rename(
            columns={
                "internal_temperature":
                    "internal_temperature_c",
                "internal_humidity":
                    "internal_humidity_pct",
                "external_temperature":
                    "external_temperature_c",
                "external_humidity":
                    "external_humidity_pct"
            }
        )

        house_months.append(df)


    # Combine all months for this house
    house_data = pd.concat(
        house_months,
        ignore_index=True
    )

    house_data = house_data.sort_values(
        "timestamp"
    ).reset_index(drop=True)


    # -----------------------------
    # QUALITY CHECKS
    # -----------------------------

    duplicate_count = (
        house_data["timestamp"]
        .duplicated()
        .sum()
    )

    null_internal_temp = (
        house_data["internal_temperature_c"]
        .isna()
        .sum()
    )

    null_internal_humidity = (
        house_data["internal_humidity_pct"]
        .isna()
        .sum()
    )

    null_external_temp = (
        house_data["external_temperature_c"]
        .isna()
        .sum()
    )

    null_external_humidity = (
        house_data["external_humidity_pct"]
        .isna()
        .sum()
    )

    # Expected complete 15-minute timeline
    expected_timestamps = pd.date_range(
        start=house_data["timestamp"].min(),
        end=house_data["timestamp"].max(),
        freq="15min"
    )

    actual_timestamps = pd.DatetimeIndex(
        house_data["timestamp"]
    )

    missing_timestamps = (
        expected_timestamps.difference(
            actual_timestamps
        )
    )

    missing_intervals = len(
        missing_timestamps
    )


    quality_summary.append(
        {
            "house_id": house_id,
            "rows_15min": len(house_data),
            "start_date":
                house_data["timestamp"].min(),
            "end_date":
                house_data["timestamp"].max(),
            "duplicate_timestamps":
                duplicate_count,
            "missing_intervals":
                missing_intervals,
            "null_internal_temperature":
                null_internal_temp,
            "null_internal_humidity":
                null_internal_humidity,
            "null_external_temperature":
                null_external_temp,
            "null_external_humidity":
                null_external_humidity
        }
    )

    all_houses.append(house_data)

    print("15-minute rows:", len(house_data))
    print("Missing intervals:", missing_intervals)
    print("Duplicates:", duplicate_count)

    print(
        "Total null environmental values:",
        null_internal_temp
        + null_internal_humidity
        + null_external_temp
        + null_external_humidity
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

environmental_all_houses = pd.concat(
    all_houses,
    ignore_index=True
)

environmental_all_houses = (
    environmental_all_houses
    .sort_values(
        ["house_id", "timestamp"]
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
# SAVE ENVIRONMENTAL DATASET
# -----------------------------

environmental_output = (
    output_folder
    / "environmental_15min_all_houses.csv"
)

environmental_all_houses.to_csv(
    environmental_output,
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
    / "environmental_quality_summary.csv"
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
    environmental_all_houses[
        "house_id"
    ].nunique()
)

print(
    "Total environmental rows:",
    len(environmental_all_houses)
)

print()
print("Environmental dataset created:")
print(environmental_output)

print()
print("Quality summary created:")
print(quality_output)