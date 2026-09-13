import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

# -------------------------------------------------
# MAIN FOLDER
# -------------------------------------------------

base_folder = Path(__file__).parent

household_records = []
quality_records = []

house_folders = sorted(base_folder.glob("House_*"))

print("Houses found:", len(house_folders))
print()


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def is_selected(value):
    return clean_text(value).lower() == "x"


def find_question_row(ws, question_text):
    """
    Searches column A for the requested question.
    Ignores extra spaces and capitalization.
    """

    target = clean_text(question_text).lower()

    for row in range(1, ws.max_row + 1):

        value = clean_text(
            ws.cell(row=row, column=1).value
        ).lower()

        if value == target:
            return row

    return None


def get_selected_options(ws, question_text):
    """
    Finds all options marked with X below a question.
    Stops at the first completely blank row.
    """

    question_row = find_question_row(
        ws,
        question_text
    )

    if question_row is None:
        return []

    selected = []

    for row in range(
        question_row + 1,
        ws.max_row + 1
    ):

        option = ws.cell(
            row=row,
            column=1
        ).value

        if option is None:
            break

        option = clean_text(option)

        for column in range(
            2,
            ws.max_column + 1
        ):

            value = ws.cell(
                row=row,
                column=column
            ).value

            if is_selected(value):
                selected.append(option)
                break

    return selected


def get_occupants(ws):
    """
    Calculates total household occupants
    from the age-category matrix.
    """

    question_row = find_question_row(
        ws,
        "Number of occupants of the house according to their age category"
    )

    if question_row is None:
        return None, False

    headers = {}

    # Headers are 0, 1, 2, 3, 4, 5, >5
    for column in range(
        2,
        ws.max_column + 1
    ):

        header = ws.cell(
            row=question_row,
            column=column
        ).value

        if header is not None:
            headers[column] = header

    total = 0
    approximate = False

    # Children / Teenager / Adult / >65 years old
    for row in range(
        question_row + 1,
        ws.max_row + 1
    ):

        category = ws.cell(
            row=row,
            column=1
        ).value

        if category is None:
            break

        for column, header in headers.items():

            selected_value = ws.cell(
                row=row,
                column=column
            ).value

            if is_selected(selected_value):

                header_text = clean_text(header)

                if ">" in header_text:
                    # >5 means at least 6 occupants
                    total += 6
                    approximate = True

                else:
                    try:
                        total += int(float(header))
                    except (ValueError, TypeError):
                        pass

    if approximate:
        return f">={total}", True

    return total, False


# -------------------------------------------------
# PROCESS EACH HOUSE
# -------------------------------------------------

for house_folder in house_folders:

    house_id = house_folder.name

    print("===================================")
    print("Processing:", house_id)

    # IMPORTANT:
    # Search recursively inside ALL subfolders
    excel_files = []

    excel_files.extend(
        house_folder.rglob("*.xlsx")
    )

    excel_files.extend(
        house_folder.rglob("*.xlsm")
    )

    excel_files = [
        file
        for file in excel_files
        if not file.name.startswith("~$")
    ]

    # Prefer the household metadata questionnaire
    preferred_files = [
        file
        for file in excel_files
        if (
            "sociodemographic"
            in file.name.lower()
            or
            "building"
            in file.name.lower()
            or
            "metadata"
            in file.name.lower()
        )
    ]

    if preferred_files:
        metadata_file = preferred_files[0]

    elif len(excel_files) == 1:
        metadata_file = excel_files[0]

    else:
        print("Metadata Excel file NOT found.")

        if excel_files:
            print("Excel files found:")
            for file in excel_files:
                print("  ", file)

        quality_records.append(
            {
                "house_id": house_id,
                "metadata_file_found": False,
                "missing_fields": "ALL",
                "occupants_approximate": None
            }
        )

        print()
        continue


    print("Metadata file found:")
    print(metadata_file)


    # -------------------------------------------------
    # OPEN WORKBOOK
    # -------------------------------------------------

    try:

        workbook = load_workbook(
            metadata_file,
            data_only=True
        )

    except Exception as error:

        print("Could not open workbook:")
        print(error)

        quality_records.append(
            {
                "house_id": house_id,
                "metadata_file_found": False,
                "missing_fields": "FILE_OPEN_ERROR",
                "occupants_approximate": None
            }
        )

        print()
        continue


    # Use first sheet
    ws = workbook[
        workbook.sheetnames[0]
    ]

    print("Worksheet:", ws.title)


    # -------------------------------------------------
    # OCCUPANTS
    # -------------------------------------------------

    occupants, occupants_approximate = (
        get_occupants(ws)
    )


    # -------------------------------------------------
    # BUILDING CHARACTERISTICS
    # -------------------------------------------------

    house_type_options = (
        get_selected_options(
            ws,
            "House typology"
        )
    )

    rooms_options = (
        get_selected_options(
            ws,
            "Numbers of rooms"
        )
    )

    construction_options = (
        get_selected_options(
            ws,
            "Year of construction"
        )
    )

    renovation_options = (
        get_selected_options(
            ws,
            "Renovation"
        )
    )

    tenure_options = (
        get_selected_options(
            ws,
            "Houseowner situation"
        )
    )

    heating_options = (
        get_selected_options(
            ws,
            "Types of heating and cooling systems"
        )
    )

    water_heater_options = (
        get_selected_options(
            ws,
            "Type of water heater"
        )
    )

    solar_options = (
        get_selected_options(
            ws,
            "Solar panels"
        )
    )


    # -------------------------------------------------
    # CREATE HOUSEHOLD RECORD
    # -------------------------------------------------

    record = {

        "house_id":
            house_id,

        "occupants":
            occupants,

        "house_type":
            house_type_options[0]
            if house_type_options
            else None,

        "number_of_rooms":
            rooms_options[0]
            if rooms_options
            else None,

        "construction_period":
            construction_options[0]
            if construction_options
            else None,

        "renovation_status":
            renovation_options[0]
            if renovation_options
            else None,

        "tenure":
            tenure_options[0]
            if tenure_options
            else None,

        # Keep ALL selected heating/cooling systems
        "heating_cooling_system":
            " | ".join(
                heating_options
            )
            if heating_options
            else None,

        # Keep ALL selected water-heating systems
        "water_heater_type":
            " | ".join(
                water_heater_options
            )
            if water_heater_options
            else None,

        "solar_panels":
            solar_options[0]
            if solar_options
            else None
    }

    household_records.append(
        record
    )


    # -------------------------------------------------
    # QUALITY CHECK
    # -------------------------------------------------

    missing_fields = [

        field

        for field, value
        in record.items()

        if (
            field != "house_id"
            and (
                value is None
                or value == ""
            )
        )
    ]

    quality_records.append(
        {
            "house_id":
                house_id,

            "metadata_file_found":
                True,

            "missing_fields":
                " | ".join(
                    missing_fields
                ),

            "occupants_approximate":
                occupants_approximate
        }
    )


    # Display result
    print("Occupants:", occupants)
    print(
        "House type:",
        record["house_type"]
    )
    print(
        "Number of rooms:",
        record["number_of_rooms"]
    )
    print(
        "Construction period:",
        record["construction_period"]
    )
    print(
        "Renovation:",
        record["renovation_status"]
    )
    print(
        "Tenure:",
        record["tenure"]
    )
    print(
        "Heating/Cooling:",
        record["heating_cooling_system"]
    )
    print(
        "Water heater:",
        record["water_heater_type"]
    )
    print(
        "Solar panels:",
        record["solar_panels"]
    )
    print(
        "Missing fields:",
        missing_fields
    )

    print()


# -------------------------------------------------
# CREATE DATAFRAMES
# -------------------------------------------------

households = pd.DataFrame(
    household_records
)

quality_summary = pd.DataFrame(
    quality_records
)


# -------------------------------------------------
# CREATE OUTPUT FOLDER
# -------------------------------------------------

output_folder = (
    base_folder / "Processed_Data"
)

output_folder.mkdir(
    exist_ok=True
)


# -------------------------------------------------
# SAVE QUALITY SUMMARY
# -------------------------------------------------

quality_output = (
    output_folder
    / "households_quality_summary.csv"
)

quality_summary.to_csv(
    quality_output,
    index=False
)


# -------------------------------------------------
# SAFETY CHECK
# -------------------------------------------------

if households.empty:

    print("===================================")
    print("PROCESS STOPPED")
    print("===================================")

    print(
        "No household records were extracted."
    )

    print(
        "Check the metadata file paths shown above."
    )

    print()
    print(
        "Quality summary created:"
    )

    print(
        quality_output
    )

else:

    # Sort houses
    households = households.sort_values(
        "house_id"
    ).reset_index(drop=True)

    # Save final household dataset
    households_output = (
        output_folder
        / "households.csv"
    )

    households.to_csv(
        households_output,
        index=False
    )


    # -------------------------------------------------
    # FINAL RESULTS
    # -------------------------------------------------

    print("===================================")
    print("PROCESS COMPLETED")
    print("===================================")

    print(
        "Household records:",
        len(households)
    )

    print(
        "Duplicate house IDs:",
        households[
            "house_id"
        ]
        .duplicated()
        .sum()
    )

    print()
    print(
        "Households dataset created:"
    )

    print(
        households_output
    )

    print()
    print(
        "Quality summary created:"
    )

    print(
        quality_output
    )

    print()
    print(
        "Final households table:"
    )

    print(
        households.to_string(
            index=False
        )
    )