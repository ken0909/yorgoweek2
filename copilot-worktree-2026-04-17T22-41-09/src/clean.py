"""
clean.py

This script handles data cleaning for the ML pipeline.
"""
import os
import pandas as pd

def clean_data(input_path: str, output_path: str):
    """Read raw data, clean it, and save the cleaned data."""
    # Example: Read CSV
    df = pd.read_csv(input_path)
    # Drop duplicates
    df = df.drop_duplicates()
    # Fill missing values (example: fill with mean)
    df = df.fillna(df.mean(numeric_only=True))
    # Save cleaned data
    df.to_csv(output_path, index=False)
    print(f"Cleaned data saved to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean raw data.")
    parser.add_argument('--input', required=True, help='Path to raw data CSV')
    parser.add_argument('--output', required=True, help='Path to save cleaned data CSV')
    args = parser.parse_args()
    clean_data(args.input, args.output)

