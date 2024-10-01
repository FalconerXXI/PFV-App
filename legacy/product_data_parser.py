import pandas as pd
import json

class ProductDataParser:
    def __init__(self, file_path):
        """
        Initializes the parser with the file path of the JSON file.

        :param file_path: The path to the JSON file containing product data.
        """
        self.file_path = file_path
        self.data = None
        self.df = None

    def load_data(self):
        """
        Loads the JSON data from the provided file path.
        """
        try:
            with open(self.file_path, 'r') as file:
                self.data = json.load(file)
            print(f"Data loaded successfully from {self.file_path}.")
        except Exception as e:
            print(f"Failed to load data: {e}")

    def extract_product_info(self):
        """
        Extracts product information and flattens the nested JSON structure into a DataFrame.
        """
        if self.data is None:
            print("No data found. Please load the data first.")
            return None

        # Extract the 'document' field from each product and flatten the data
        product_list = [item['document'] for item in self.data if 'document' in item]
        self.df = pd.json_normalize(product_list)
        print("Product information extracted and flattened into a DataFrame.")

    def handle_inconsistencies(self):
        """
        Handles inconsistencies in the DataFrame, particularly for missing or non-uniform fields.
        """
        if self.df is None:
            print("No DataFrame found. Please extract product info first.")
            return

        # Handle inconsistencies in '_Processor_Model'
        if '_Processor_Model' in self.df.columns:
            self.df['_Processor_Model'] = self.df['_Processor_Model'].apply(
                lambda x: x[0] if isinstance(x, list) and x else None
            )
        else:
            print("No '_Processor_Model' column found in DataFrame.")

        # Handle other common inconsistencies
        self.df.fillna("", inplace=True)  # Replace NaNs with empty strings
        self.df.replace(to_replace=[None], value="", inplace=True)  # Replace None with empty strings

        print("Handled inconsistencies in the DataFrame.")

    def filter_columns(self, columns=None):
        """
        Filters the DataFrame to include only specified columns.

        :param columns: List of columns to include in the final DataFrame. If None, include all columns.
        """
        if self.df is None:
            print("No DataFrame found. Please extract product info first.")
            return None

        # Get the list of existing columns in the DataFrame
        existing_columns = self.df.columns.tolist()

        # Check if any of the specified columns are missing and log a warning
        missing_columns = [col for col in columns if col not in existing_columns]
        if missing_columns:
            print(f"Warning: The following columns are missing and will be skipped: {missing_columns}")

        # Filter to include only the columns that exist in the DataFrame
        columns_to_include = [col for col in columns if col in existing_columns]
        if columns_to_include:
            self.df = self.df[columns_to_include]
            print(f"Data filtered to include columns: {columns_to_include}")
        else:
            print("No specified columns found in the DataFrame. Returning all columns.")

    def save_to_csv(self, output_file):
        """
        Saves the DataFrame to a CSV file.

        :param output_file: The path to save the CSV file.
        """
        if self.df is None:
            print("No DataFrame found. Please extract product info first.")
            return

        try:
            self.df.to_csv(output_file, index=False)
            print(f"Data successfully saved to {output_file}.")
        except Exception as e:
            print(f"Failed to save DataFrame to CSV: {e}")

    def get_dataframe(self):
        """
        Returns the current DataFrame.

        :return: The current DataFrame.
        """
        return self.df