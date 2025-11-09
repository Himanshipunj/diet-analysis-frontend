import pandas as pd
import numpy as np
import os
import io
import logging
from typing import Dict, List, Optional, Union
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError


class AzureDietDataProcessor:
    """
    Azure-compatible version of DietDataProcessor that reads data from Azure Blob Storage
    """

    def __init__(
        self, connection_string: Optional[str] = None, container_name: str = "diet-data"
    ):
        """
        Initialize the Azure Diet Data Processor

        Args:
            connection_string: Azure Storage connection string (if None, uses environment variable)
            container_name: Name of the blob container containing the data
        """
        self.data = None
        self.container_name = container_name
        self.blob_name = "All_Diets.csv"

        # Get connection string from parameter or environment variable
        self.connection_string = connection_string or os.getenv("AzureWebJobsStorage")

        if not self.connection_string:
            raise ValueError(
                "Azure Storage connection string must be provided either as parameter or AzureWebJobsStorage environment variable"
            )

        # Initialize blob service client
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        except Exception as e:
            logging.error(f"Failed to initialize blob service client: {e}")
            raise

    def load_data_from_blob(self, blob_name: Optional[str] = None) -> bool:
        """
        Load diet data from Azure Blob Storage

        Args:
            blob_name: Name of the blob file (defaults to All_Diets.csv)

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            blob_name = blob_name or self.blob_name

            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            # Download blob content
            logging.info(
                f"Downloading blob: {blob_name} from container: {self.container_name}"
            )
            blob_data = blob_client.download_blob().readall()

            # Load into pandas DataFrame
            self.data = pd.read_csv(io.BytesIO(blob_data))
            logging.info(
                f"Successfully loaded {len(self.data)} records from blob storage"
            )

            # Clean the data
            self._clean_data()
            return True

        except ResourceNotFoundError:
            logging.error(
                f"Blob {blob_name} not found in container {self.container_name}"
            )
            return False
        except Exception as e:
            logging.error(f"Error loading data from blob storage: {e}")
            return False

    def load_data_from_content(self, content: bytes) -> bool:
        """
        Load diet data from blob content (useful for blob triggers)

        Args:
            content: Raw blob content as bytes

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            self.data = pd.read_csv(io.BytesIO(content))
            logging.info(
                f"Successfully loaded {len(self.data)} records from blob content"
            )

            # Clean the data
            self._clean_data()
            return True

        except Exception as e:
            logging.error(f"Error loading data from blob content: {e}")
            return False

    def upload_results_to_blob(
        self, data: Union[Dict, List], blob_name: str, format_type: str = "json"
    ) -> bool:
        """
        Upload processed results back to blob storage

        Args:
            data: Data to upload
            blob_name: Name for the result blob
            format_type: Format to save data in ('json' or 'csv')

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            if format_type.lower() == "json":
                import json

                content = json.dumps(data, indent=2)
                content_type = "application/json"
            elif format_type.lower() == "csv" and isinstance(data, list):
                df = pd.DataFrame(data)
                content = df.to_csv(index=False)
                content_type = "text/csv"
            else:
                raise ValueError("Unsupported format type or data structure")

            blob_client.upload_blob(content, overwrite=True, content_type=content_type)
            logging.info(f"Successfully uploaded results to blob: {blob_name}")
            return True

        except Exception as e:
            logging.error(f"Error uploading results to blob storage: {e}")
            return False

    def _clean_data(self):
        """Clean and prepare the dataset"""
        if self.data is None:
            return

        logging.info("Cleaning data...")

        # Fill missing numeric values with mean
        numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
        for col in numeric_cols:
            if col in self.data.columns:
                mean_val = self.data[col].mean()
                self.data[col] = self.data[col].fillna(mean_val)

        # Fill missing categorical values
        categorical_cols = ["Diet_type", "Cuisine_type"]
        for col in categorical_cols:
            if col in self.data.columns:
                mode_value = self.data[col].mode()
                fill_value = mode_value[0] if len(mode_value) > 0 else "Unknown"
                self.data[col] = self.data[col].fillna(fill_value)

        logging.info("Data cleaning completed")

    def get_macronutrient_averages(self) -> Dict[str, Dict[str, float]]:
        """Get average macronutrient content by diet type"""
        if self.data is None:
            logging.warning("No data loaded")
            return {}

        macro_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
        available_cols = [col for col in macro_cols if col in self.data.columns]

        if "Diet_type" not in self.data.columns or not available_cols:
            logging.warning("Required columns not found in data")
            return {}

        result = {}
        for diet_type in self.data["Diet_type"].unique():
            diet_data = self.data[self.data["Diet_type"] == diet_type]
            averages = {}
            for col in available_cols:
                averages[col.replace("(g)", "")] = round(diet_data[col].mean(), 2)
            result[diet_type] = averages

        return result

    def get_diet_comparison_data(self) -> List[Dict]:
        """Get comparison data between different diet types"""
        averages = self.get_macronutrient_averages()
        comparison_data = []

        for diet_type, macros in averages.items():
            diet_info = {
                "diet_type": diet_type,
                "protein": macros.get("Protein", 0),
                "carbs": macros.get("Carbs", 0),
                "fat": macros.get("Fat", 0),
                "total_recipes": len(self.data[self.data["Diet_type"] == diet_type]),
            }
            comparison_data.append(diet_info)

        return comparison_data

    def get_top_recipes_by_nutrient(
        self, nutrient: str = "Protein", n: int = 10
    ) -> List[Dict]:
        """Get top N recipes by specified nutrient content"""
        if self.data is None:
            return []

        nutrient_col = f"{nutrient}(g)"
        if nutrient_col not in self.data.columns:
            logging.warning(f"Nutrient column {nutrient_col} not found")
            return []

        top_recipes = self.data.nlargest(n, nutrient_col)

        result = []
        for _, recipe in top_recipes.iterrows():
            recipe_info = {
                "recipe_name": recipe.get("Recipe_name", "Unknown"),
                "diet_type": recipe.get("Diet_type", "Unknown"),
                "cuisine_type": recipe.get("Cuisine_type", "Unknown"),
                "nutrient_value": round(recipe[nutrient_col], 2),
                "nutrient_type": nutrient,
            }
            result.append(recipe_info)

        return result

    def get_cuisine_distribution(self) -> Dict[str, Dict[str, int]]:
        """Get cuisine distribution by diet type"""
        if (
            self.data is None
            or "Diet_type" not in self.data.columns
            or "Cuisine_type" not in self.data.columns
        ):
            return {}

        result = {}
        for diet_type in self.data["Diet_type"].unique():
            diet_data = self.data[self.data["Diet_type"] == diet_type]
            cuisine_counts = diet_data["Cuisine_type"].value_counts().to_dict()
            result[diet_type] = cuisine_counts

        return result

    def get_nutrient_ranges(self) -> Dict[str, Dict[str, float]]:
        """Get min, max, and average values for each nutrient"""
        if self.data is None:
            return {}

        nutrient_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
        result = {}

        for col in nutrient_cols:
            if col in self.data.columns:
                nutrient_name = col.replace("(g)", "")
                result[nutrient_name] = {
                    "min": round(self.data[col].min(), 2),
                    "max": round(self.data[col].max(), 2),
                    "average": round(self.data[col].mean(), 2),
                    "median": round(self.data[col].median(), 2),
                }

        return result

    def get_diet_summary(self) -> Dict:
        """Get overall summary statistics"""
        if self.data is None:
            return {}

        return {
            "total_recipes": len(self.data),
            "total_diet_types": (
                self.data["Diet_type"].nunique()
                if "Diet_type" in self.data.columns
                else 0
            ),
            "total_cuisine_types": (
                self.data["Cuisine_type"].nunique()
                if "Cuisine_type" in self.data.columns
                else 0
            ),
            "diet_types": (
                self.data["Diet_type"].unique().tolist()
                if "Diet_type" in self.data.columns
                else []
            ),
            "most_common_diet": (
                self.data["Diet_type"].mode()[0]
                if "Diet_type" in self.data.columns
                and len(self.data["Diet_type"].mode()) > 0
                else "Unknown"
            ),
            "most_common_cuisine": (
                self.data["Cuisine_type"].mode()[0]
                if "Cuisine_type" in self.data.columns
                and len(self.data["Cuisine_type"].mode()) > 0
                else "Unknown"
            ),
        }

    def get_recipes_by_diet_type(self, diet_type: str) -> List[Dict]:
        """Get all recipes for a specific diet type"""
        if self.data is None or "Diet_type" not in self.data.columns:
            return []

        diet_recipes = self.data[self.data["Diet_type"] == diet_type]

        result = []
        for _, recipe in diet_recipes.iterrows():
            recipe_info = {
                "recipe_name": recipe.get("Recipe_name", "Unknown"),
                "cuisine_type": recipe.get("Cuisine_type", "Unknown"),
                "protein": round(recipe.get("Protein(g)", 0), 2),
                "carbs": round(recipe.get("Carbs(g)", 0), 2),
                "fat": round(recipe.get("Fat(g)", 0), 2),
            }
            result.append(recipe_info)

        return result

    def search_recipes(
        self, search_term: str, search_field: str = "Recipe_name"
    ) -> List[Dict]:
        """Search for recipes by name or other fields"""
        if self.data is None or search_field not in self.data.columns:
            return []

        # Case-insensitive search
        matching_recipes = self.data[
            self.data[search_field].str.contains(search_term, case=False, na=False)
        ]

        result = []
        for _, recipe in matching_recipes.iterrows():
            recipe_info = {
                "recipe_name": recipe.get("Recipe_name", "Unknown"),
                "diet_type": recipe.get("Diet_type", "Unknown"),
                "cuisine_type": recipe.get("Cuisine_type", "Unknown"),
                "protein": round(recipe.get("Protein(g)", 0), 2),
                "carbs": round(recipe.get("Carbs(g)", 0), 2),
                "fat": round(recipe.get("Fat(g)", 0), 2),
            }
            result.append(recipe_info)

        return result


# Example usage for local testing
def main():
    """Test the AzureDietDataProcessor functionality locally"""
    # For local development, you can use Azurite (Azure Storage Emulator)
    connection_string = (
        "DefaultEndpointsProtocol=http;"
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )

    try:
        processor = AzureDietDataProcessor(connection_string=connection_string)

        # Load data from blob storage
        if processor.load_data_from_blob():
            print("Data loaded successfully from Azure Blob Storage!")

            # Test all functions
            print("\n1. Diet Summary:")
            summary = processor.get_diet_summary()
            print(summary)

            print("\n2. Macronutrient Averages:")
            averages = processor.get_macronutrient_averages()
            for diet, macros in averages.items():
                print(f"  {diet}: {macros}")

            # Upload results back to blob storage
            processor.upload_results_to_blob(summary, "diet_summary.json")
            processor.upload_results_to_blob(averages, "macronutrient_averages.json")

        else:
            print("Failed to load data from blob storage")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
