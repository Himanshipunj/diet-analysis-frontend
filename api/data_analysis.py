import pandas as pd
import numpy as np
from datetime import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, List
import warnings

warnings.filterwarnings("ignore")


class DietAnalyzer:
    def __init__(self):
        self.data = None

    def load_data(self, data_source):
        """Load diet data from various sources"""
        if isinstance(data_source, str):
            # Load from file
            if data_source.endswith(".csv"):
                self.data = pd.read_csv(data_source)
        elif isinstance(data_source, dict):
            # Load from dictionary/API response
            self.data = pd.DataFrame(data_source)

        # Clean data after loading
        if self.data is not None:
            self.clean_data()

        return self.data

    def clean_data(self):
        """Handle missing values and clean the dataset"""
        if self.data is None:
            return

        print("Cleaning data...")
        print(f"Original shape: {self.data.shape}")

        # Identify numeric columns for macronutrients
        numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]

        # Fill missing values with mean for numeric columns
        for col in numeric_cols:
            if col in self.data.columns:
                mean_val = self.data[col].mean()
                self.data[col] = self.data[col].fillna(mean_val)
                print(
                    f"Filled {self.data[col].isna().sum()} missing values in {col} with mean: {mean_val:.2f}"
                )

        # Fill missing categorical values with mode or 'Unknown'
        categorical_cols = ["Diet_type", "Cuisine_type"]
        for col in categorical_cols:
            if col in self.data.columns:
                mode_value = self.data[col].mode()
                fill_value = mode_value[0] if len(mode_value) > 0 else "Unknown"
                missing_count = self.data[col].isna().sum()
                self.data[col] = self.data[col].fillna(fill_value)
                print(
                    f"Filled {missing_count} missing values in {col} with: {fill_value}"
                )

        print(f"Cleaned shape: {self.data.shape}")

    def calculate_average_macronutrients(self) -> pd.DataFrame:
        """Calculate average macronutrient content for each diet type"""
        if self.data is None:
            return pd.DataFrame()

        macro_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
        available_cols = [col for col in macro_cols if col in self.data.columns]

        if "Diet_type" not in self.data.columns or not available_cols:
            return pd.DataFrame()

        avg_macros = self.data.groupby("Diet_type")[available_cols].mean()
        return avg_macros

    def get_top_protein_recipes(self, n: int = 5) -> pd.DataFrame:
        """Find top N protein-rich recipes for each diet type"""
        if self.data is None or "Protein(g)" not in self.data.columns:
            return pd.DataFrame()

        return (
            self.data.sort_values("Protein(g)", ascending=False)
            .groupby("Diet_type")
            .head(n)
        )

    def get_highest_protein_diet_type(self) -> str:
        """Find diet type with highest average protein content"""
        avg_macros = self.calculate_average_macronutrients()
        if avg_macros.empty or "Protein(g)" not in avg_macros.columns:
            return "No data available"

        return avg_macros["Protein(g)"].idxmax()

    def get_common_cuisines_by_diet(self) -> Dict:
        """Identify most common cuisines for each diet type"""
        if (
            self.data is None
            or "Diet_type" not in self.data.columns
            or "Cuisine_type" not in self.data.columns
        ):
            return {}

        result = {}
        for diet_type in self.data["Diet_type"].unique():
            diet_data = self.data[self.data["Diet_type"] == diet_type]
            cuisine_counts = diet_data["Cuisine_type"].value_counts()
            result[diet_type] = cuisine_counts.head(5).to_dict()

        return result

    def calculate_ratios(self):
        """Calculate protein-to-carbs and carbs-to-fat ratios"""
        if self.data is None:
            return

        # Calculate ratios, handling division by zero
        if "Protein(g)" in self.data.columns and "Carbs(g)" in self.data.columns:
            self.data["Protein_to_Carbs_ratio"] = np.where(
                self.data["Carbs(g)"] != 0,
                self.data["Protein(g)"] / self.data["Carbs(g)"],
                np.inf,
            )

        if "Carbs(g)" in self.data.columns and "Fat(g)" in self.data.columns:
            self.data["Carbs_to_Fat_ratio"] = np.where(
                self.data["Fat(g)"] != 0,
                self.data["Carbs(g)"] / self.data["Fat(g)"],
                np.inf,
            )

    def visualize_average_macronutrients(self, save: bool = True, output_dir: str = "./output/plt/"):
        """Create bar charts for average macronutrient content by diet type and optionally save them"""
        avg_macros = self.calculate_average_macronutrients()
        if avg_macros.empty:
            print("No data available for visualization")
            return

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # Protein bar chart
        if "Protein(g)" in avg_macros.columns:
            sns.barplot(
                x=avg_macros.index,
                y=avg_macros["Protein(g)"],
                ax=axes[0],
                palette="viridis",
            )
            axes[0].set_title(
                "Average Protein by Diet Type", fontsize=14, fontweight="bold"
            )
            axes[0].set_ylabel("Average Protein (g)", fontsize=12)
            axes[0].tick_params(axis="x", rotation=45)

        # Carbs bar chart
        if "Carbs(g)" in avg_macros.columns:
            sns.barplot(
                x=avg_macros.index,
                y=avg_macros["Carbs(g)"],
                ax=axes[1],
                palette="plasma",
            )
            axes[1].set_title(
                "Average Carbs by Diet Type", fontsize=14, fontweight="bold"
            )
            axes[1].set_ylabel("Average Carbs (g)", fontsize=12)
            axes[1].tick_params(axis="x", rotation=45)

        # Fat bar chart
        if "Fat(g)" in avg_macros.columns:
            sns.barplot(
                x=avg_macros.index, y=avg_macros["Fat(g)"], ax=axes[2], palette="magma"
            )
            axes[2].set_title(
                "Average Fat by Diet Type", fontsize=14, fontweight="bold"
            )
            axes[2].set_ylabel("Average Fat (g)", fontsize=12)
            axes[2].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        if save:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "average_macronutrients.png"))
            print(f"Saved average macronutrient bar charts to {output_dir}")
        plt.show()

    def visualize_macronutrient_heatmap(self, save: bool = True, output_dir: str = "./output/plt/"):
        """Create heatmap showing relationship between macronutrients and diet types and optionally save it"""
        avg_macros = self.calculate_average_macronutrients()
        if avg_macros.empty:
            print("No data available for heatmap")
            return

        plt.figure(figsize=(12, 8))
        sns.heatmap(
            avg_macros.T,
            annot=True,
            cmap="YlOrRd",
            fmt=".2f",
            cbar_kws={"label": "Grams"},
        )
        plt.title(
            "Macronutrient Content by Diet Type (Heatmap)",
            fontsize=16,
            fontweight="bold",
        )
        plt.ylabel("Macronutrients", fontsize=12)
        plt.xlabel("Diet Type", fontsize=12)
        plt.tight_layout()
        if save:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "macronutrient_heatmap.png"))
            print(f"Saved macronutrient heatmap to {output_dir}")
        plt.show()

    def visualize_top_protein_scatter(self, save: bool = True, output_dir: str = "./output/plt/"):
        """Create scatter plot for top protein-rich recipes across cuisines and optionally save it"""
        top_protein = self.get_top_protein_recipes()
        if top_protein.empty or "Cuisine_type" not in top_protein.columns:
            print("No data available for scatter plot")
            return

        plt.figure(figsize=(14, 10))

        # Create scatter plot with different colors for each diet type
        diet_types = top_protein["Diet_type"].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(diet_types)))

        for i, diet_type in enumerate(diet_types):
            diet_data = top_protein[top_protein["Diet_type"] == diet_type]
            plt.scatter(
                range(len(diet_data)),
                diet_data["Protein(g)"],
                c=[colors[i]],
                label=diet_type,
                s=120,
                alpha=0.8,
                edgecolors="black",
            )

        plt.xlabel("Recipe Index", fontsize=12)
        plt.ylabel("Protein Content (g)", fontsize=12)
        plt.title(
            "Top 5 Protein-Rich Recipes by Diet Type", fontsize=16, fontweight="bold"
        )
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        if save:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "top_protein_scatter.png"))
            print(f"Saved top protein scatter plot to {output_dir}")
        plt.show()

    def visualize_cuisine_distribution(self, save: bool = True, output_dir: str = "./output/plt/"):
        """Visualize cuisine distribution for each diet type and optionally save it"""
        if (
            self.data is None
            or "Diet_type" not in self.data.columns
            or "Cuisine_type" not in self.data.columns
        ):
            print("No data available for cuisine distribution")
            return

        plt.figure(figsize=(14, 10))

        # Create a cross-tabulation
        cuisine_diet_crosstab = pd.crosstab(
            self.data["Cuisine_type"], self.data["Diet_type"]
        )

        sns.heatmap(
            cuisine_diet_crosstab,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar_kws={"label": "Count"},
        )
        plt.title("Cuisine Distribution by Diet Type", fontsize=16, fontweight="bold")
        plt.ylabel("Cuisine Type", fontsize=12)
        plt.xlabel("Diet Type", fontsize=12)
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        if save:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "cuisine_distribution.png"))
            print(f"Saved cuisine distribution heatmap to {output_dir}")
        plt.show()

    def generate_comprehensive_report(self):
        """Generate a comprehensive analysis report with visualizations"""
        if self.data is None:
            print("No data loaded. Please load data first.")
            return

        print("=" * 60)
        print("COMPREHENSIVE DIET ANALYSIS REPORT")
        print("=" * 60)

        # Calculate ratios if not already done
        self.calculate_ratios()

        # 1. Dataset Overview
        print("\n1. DATASET OVERVIEW:")
        print(f"   Total recipes: {len(self.data)}")
        print(f"   Diet types: {self.data['Diet_type'].nunique()}")
        print(f"   Cuisine types: {self.data['Cuisine_type'].nunique()}")
        print(f"   Diet types available: {', '.join(self.data['Diet_type'].unique())}")

        # 2. Average macronutrients
        print("\n2. AVERAGE MACRONUTRIENT CONTENT BY DIET TYPE:")
        avg_macros = self.calculate_average_macronutrients()
        print(avg_macros.round(2))

        # 3. Highest protein diet type
        highest_protein_diet = self.get_highest_protein_diet_type()
        print(f"\n3. DIET TYPE WITH HIGHEST PROTEIN CONTENT: {highest_protein_diet}")
        highest_protein_value = avg_macros.loc[highest_protein_diet, "Protein(g)"]
        print(f"   Average protein content: {highest_protein_value:.2f}g")

        # 4. Top protein recipes per diet
        print("\n4. TOP 5 PROTEIN-RICH RECIPES BY DIET TYPE:")
        top_protein = self.get_top_protein_recipes()
        for diet_type in top_protein["Diet_type"].unique():
            diet_recipes = top_protein[top_protein["Diet_type"] == diet_type]
            print(f"\n   {diet_type.upper()}:")
            for idx, recipe in diet_recipes.iterrows():
                print(
                    f"   - {recipe['Recipe_name']}: {recipe['Protein(g)']:.2f}g protein"
                )

        # 5. Common cuisines
        print("\n5. MOST COMMON CUISINES BY DIET TYPE:")
        common_cuisines = self.get_common_cuisines_by_diet()
        for diet_type, cuisines in common_cuisines.items():
            top_3_cuisines = list(cuisines.keys())[:3]
            print(f"   {diet_type}: {', '.join(top_3_cuisines)}")

        # 6. Ratio statistics
        print("\n6. NEW METRICS (RATIOS):")
        if "Protein_to_Carbs_ratio" in self.data.columns:
            # Filter out infinite values for meaningful statistics
            valid_ratios = self.data[self.data["Protein_to_Carbs_ratio"] != np.inf]
            avg_p_to_c = valid_ratios["Protein_to_Carbs_ratio"].mean()
            print(f"   Average Protein-to-Carbs ratio: {avg_p_to_c:.3f}")

        if "Carbs_to_Fat_ratio" in self.data.columns:
            valid_ratios = self.data[self.data["Carbs_to_Fat_ratio"] != np.inf]
            avg_c_to_f = valid_ratios["Carbs_to_Fat_ratio"].mean()
            print(f"   Average Carbs-to-Fat ratio: {avg_c_to_f:.3f}")

        print("\n" + "=" * 60)
        print("GENERATING VISUALIZATIONS...")
        print("=" * 60)

        # Generate visualizations
        self.visualize_average_macronutrients()
        self.visualize_macronutrient_heatmap()
        self.visualize_top_protein_scatter()
        self.visualize_cuisine_distribution()

        print("\nAnalysis complete!")


def main():
    """Main function to test all DietAnalyzer features"""

    print("=" * 80)
    print("DIET ANALYSIS PROJECT - COMPREHENSIVE TESTING")
    print("=" * 80)

    # Initialize the analyzer
    analyzer = DietAnalyzer()

    # Define the path to the CSV file
    csv_path = "resources/All_Diets.csv"

    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please ensure the file exists in the correct location.")
        return

    try:
        # Load and clean the data
        print(f"Loading data from: {csv_path}")
        data = analyzer.load_data(csv_path)

        if data is None:
            print("Error: Failed to load data")
            return

        print(f"Successfully loaded {len(data)} recipes!")
        print(f"Columns: {list(data.columns)}")

        # Display basic info about the dataset
        print(f"\nDataset Info:")
        print(f"- Shape: {data.shape}")
        print(f"- Diet types: {data['Diet_type'].value_counts().to_dict()}")
        print(
            f"- Top 5 cuisines: {data['Cuisine_type'].value_counts().head().to_dict()}"
        )

        # Test individual features
        print("\n" + "=" * 50)
        print("TESTING INDIVIDUAL FEATURES")
        print("=" * 50)

        # 1. Test average macronutrients calculation
        print("\n1. Testing average macronutrients calculation...")
        avg_macros = analyzer.calculate_average_macronutrients()
        print("Average macronutrients by diet type:")
        print(avg_macros.round(2))

        # 2. Test top protein recipes
        print("\n2. Testing top protein recipes identification...")
        top_protein = analyzer.get_top_protein_recipes(3)  # Top 3 for testing
        print(f"Found {len(top_protein)} top protein recipes")
        for diet in top_protein["Diet_type"].unique():
            diet_recipes = top_protein[top_protein["Diet_type"] == diet]
            print(f"\nTop protein recipes for {diet}:")
            for _, recipe in diet_recipes.iterrows():
                print(f"  - {recipe['Recipe_name']}: {recipe['Protein(g)']:.1f}g")

        # 3. Test highest protein diet type
        print("\n3. Testing highest protein diet type identification...")
        highest_protein_diet = analyzer.get_highest_protein_diet_type()
        print(f"Diet type with highest protein: {highest_protein_diet}")

        # 4. Test common cuisines by diet
        print("\n4. Testing common cuisines analysis...")
        common_cuisines = analyzer.get_common_cuisines_by_diet()
        for diet_type, cuisines in common_cuisines.items():
            top_cuisines = list(cuisines.keys())[:3]
            print(f"{diet_type}: {', '.join(top_cuisines)}")

        # 5. Test ratio calculations
        print("\n5. Testing ratio calculations...")
        analyzer.calculate_ratios()
        print("Ratios calculated successfully!")

        # Show some sample ratios
        sample_data = analyzer.data[
            ["Recipe_name", "Diet_type", "Protein_to_Carbs_ratio", "Carbs_to_Fat_ratio"]
        ].head()
        print("Sample ratios:")
        print(sample_data)

        # 6. Generate comprehensive report with all visualizations
        print("\n" + "=" * 50)
        print("GENERATING COMPREHENSIVE REPORT")
        print("=" * 50)

        analyzer.generate_comprehensive_report()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"Error occurred during analysis: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
