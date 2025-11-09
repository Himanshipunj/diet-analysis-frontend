import json
import logging
import azure.functions as func

from .azure_diet_processor import AzureDietDataProcessor


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger for diet data processing operations.

    This function delegates to AzureDietDataProcessor for all data operations.
    Route parameter `operation` is used to select the operation. See README or
    the processor for available operations.
    """

    logging.info("Diet data processor HTTP trigger function processed a request.")

    try:
        # Get operation from route
        operation = (req.route_params.get("operation") or "").lower()

        # Handle health check first
        if operation == "health":
            return func.HttpResponse(
                json.dumps({"status": "healthy", "message": "Function is running"}),
                status_code=200,
                mimetype="application/json",
            )

        # Initialize the processor
        processor = AzureDietDataProcessor()

        # Load data from Azure Blob Storage
        if not processor.load_data_from_blob():
            return func.HttpResponse(
                json.dumps({"error": "Failed to load data from blob storage"}),
                status_code=500,
                mimetype="application/json",
            )

        # Route to appropriate function based on operation
        if operation == "summary":
            result = processor.get_diet_summary()

        elif operation == "macronutrients":
            result = processor.get_macronutrient_averages()

        elif operation == "comparison":
            result = processor.get_diet_comparison_data()

        elif operation == "top-recipes":
            nutrient = req.params.get("nutrient", "Protein")
            # Safe parse for n, clamp to sensible maximum
            try:
                n = int(req.params.get("n", 10))
            except (TypeError, ValueError):
                n = 10
            n = max(1, min(n, 100))
            result = processor.get_top_recipes_by_nutrient(nutrient, n)

        elif operation == "cuisine-distribution":
            result = processor.get_cuisine_distribution()

        elif operation == "nutrient-ranges":
            result = processor.get_nutrient_ranges()

        elif operation.startswith("recipes/"):
            diet_type = operation.replace("recipes/", "")
            result = processor.get_recipes_by_diet_type(diet_type)

        elif operation == "search":
            search_term = req.params.get("term", "")
            search_field = req.params.get("field", "Recipe_name")
            if not search_term:
                return func.HttpResponse(
                    json.dumps({"error": "Search term is required"}),
                    status_code=400,
                    mimetype="application/json",
                )
            result = processor.search_recipes(search_term, search_field)

        else:
            # Default: return available operations
            result = {
                "message": "Welcome to Diet Data Processor API",
                "status": "running",
                "available_operations": [
                    "/diet-processor/health",
                    "/diet-processor/summary",
                    "/diet-processor/macronutrients",
                    "/diet-processor/comparison",
                    "/diet-processor/top-recipes?nutrient=Protein&n=10",
                    "/diet-processor/cuisine-distribution",
                    "/diet-processor/nutrient-ranges",
                    "/diet-processor/recipes/{diet_type}",
                    "/diet-processor/search?term={search_term}&field=Recipe_name",
                ],
            }

        return func.HttpResponse(
            json.dumps(result, indent=2), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )
