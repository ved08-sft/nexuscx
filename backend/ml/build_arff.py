#!/usr/bin/env python3
"""
Convert CSV data to ARFF format for WEKA.
"""

import argparse
import csv
import sys
from typing import List, Dict, Any


def csv_to_arff(csv_file: str, arff_file: str, relation_name: str = "nexuscx_risk_v1") -> None:
    """
    Convert CSV file to ARFF format.
    """
    # Read CSV data
    rows = []
    headers = []

    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # First row is header
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    if not rows:
        print("Error: No data found in CSV file")
        sys.exit(1)

    # Determine column types
    col_types: List[str] = []
    nominal_values: Dict[int, List[str]] = {}

    # Initialize nominal value tracking for columns that might be nominal
    for i, header in enumerate(headers):
        nominal_values[i] = set()

    # Scan all rows to determine types and collect nominal values
    for row in rows:
        if len(row) != len(headers):
            print(f"Warning: Row has {len(row)} columns, expected {len(headers)}")
            continue

        for i, cell in enumerate(row):
            # Try to parse as float
            try:
                float(cell)
                # If it parses as float, it's numeric
                if col_types and col_types[i] == "nominal":
                    print(f"Warning: Column {i} ('{headers[i]}') has mixed types")
                col_types[i] = "numeric"
            except ValueError:
                # Not a float, treat as nominal/string
                nominal_values[i].add(cell)
                if col_types and col_types[i] == "numeric":
                    print(f"Warning: Column {i} ('{headers[i]}') has mixed types")
                col_types[i] = "nominal"

    # Convert nominal sets to sorted lists
    for i in nominal_values:
        nominal_values[i] = sorted(list(nominal_values[i]))

    # Write ARFF file
    try:
        with open(arff_file, 'w') as f:
            # Write relation
            f.write(f"@relation {relation_name}\n\n")

            # Write attributes
            for i, header in enumerate(headers):
                if col_types[i] == "numeric":
                    f.write(f"@attribute {header} numeric\n")
                else:  # nominal
                    values_str = ",".join([f'"{val}"' for val in nominal_values[i]])
                    f.write(f"@attribute {header} {{{values_str}}}\n")

            f.write("\n@data\n")

            # Write data rows
            for row in rows:
                if len(row) != len(headers):
                    continue
                formatted_row = []
                for i, cell in enumerate(row):
                    if col_types[i] == "numeric":
                        formatted_row.append(cell)
                    else:  # nominal
                        formatted_row.append(f'"{cell}"')
                f.write(",".join(formatted_row) + "\n")

        print(f"Successfully converted {csv_file} to {arff_file}")
        print(f"Relation: {relation_name}")
        print(f"Instances: {len(rows)}")
        print(f"Attributes: {len(headers)}")

    except Exception as e:
        print(f"Error writing ARFF file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert CSV to ARFF for WEKA")
    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("output", help="Output ARFF file")
    parser.add_argument("--relation", default="nexuscx_risk_v1",
                       help="Relation name for ARFF file (default: nexuscx_risk_v1)")

    args = parser.parse_args()

    csv_to_arff(args.input, args.output, args.relation)


if __name__ == "__main__":
    main()