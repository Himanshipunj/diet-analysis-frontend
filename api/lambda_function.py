from azure.storage.blob import BlobServiceClient
import pandas as pd
import io
import json
import os

def process_nutritional_data_from_azurite():
    # Connection string for Azurite
    connect_str = (
        "DefaultEndpointsProtocol=http;"
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )

    # Connect to Azurite
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = 'datasets'
    blob_name = 'All_Diets.csv'

    # Access the blob
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    # Download CSV data
    print("Downloading CSV from Azurite...")
    stream = blob_client.download_blob().readall()
    df = pd.read_csv(io.BytesIO(stream))

    # Compute averages
    avg_macros = df.groupby('Diet_type')[['Protein(g)', 'Carbs(g)', 'Fat(g)']].mean().reset_index()

    # Simulated NoSQL storage
    os.makedirs('simulated_nosql', exist_ok=True)
    result_path = 'simulated_nosql/results.json'

    result = avg_macros.to_dict(orient='records')
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"✅ Data processed and stored successfully in {result_path}")
    return result

if __name__ == "__main__":
    results = process_nutritional_data_from_azurite()
    print("Output:", results)
