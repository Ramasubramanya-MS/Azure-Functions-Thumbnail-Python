import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from PIL import Image
import io
import json
import uuid

# -----------------------------------------------------------------------------
# Summary:
# This Azure Function receives an image file via an HTTP request, generates a
# thumbnail of the image, and uploads both the original image and the thumbnail
# to Azure Blob Storage. The function then returns the URLs of the uploaded
# images (original and thumbnail) as a JSON response.
#
# The function performs the following steps:
# 1. Receives the image file in the HTTP request.
# 2. Generates a thumbnail of the image (default size: 128x128).
# 3. Uploads both the original image and the generated thumbnail to Azure Blob Storage.
# 4. Returns the URLs for the uploaded images.
#
# Required environment variables:
# - AzureWebJobsStorage: Azure Storage connection string to access Blob Storage.
# -----------------------------------------------------------------------------


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing an image upload to generate a thumbnail.")

    # Step 1: Check if a file is provided in the HTTP request
    try:
        file = req.files.get("file")  # Retrieve the file from the request
        if not file:
            return func.HttpResponse(
                "No file uploaded", status_code=400
            )  # Return error if no file is uploaded
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return func.HttpResponse(
            "Error processing request", status_code=500
        )  # Return error if there is an issue reading the file

    try:
        # Step 2: Read the image file into memory and generate a thumbnail
        image_bytes = file.read()  # Read the image bytes from the uploaded file
        image = Image.open(io.BytesIO(image_bytes))  # Open the image using PIL (Pillow)

        # Generate the thumbnail (default size: 128x128)
        thumbnail_size = (128, 128)
        image.thumbnail(thumbnail_size)

        # Save the thumbnail to a byte buffer
        thumb_buffer = io.BytesIO()  # Create a memory buffer to store the thumbnail
        image.save(thumb_buffer, format="JPEG")  # Save the thumbnail as a JPEG image
        thumb_buffer.seek(0)  # Rewind the buffer to the start

        # Step 3: Generate unique blob names for storing the original image and the thumbnail
        original_blob_name = (
            f"{uuid.uuid4()}_{file.filename}"  # Unique name for the original image
        )
        thumbnail_blob_name = (
            f"thumb_{original_blob_name}"  # Unique name for the thumbnail
        )

        # Step 4: Connect to Azure Blob Storage using the connection string stored in environment variables
        conn_str = os.environ[
            "AzureWebJobsStorage"
        ]  # Get the connection string from environment variables
        blob_service_client = BlobServiceClient.from_connection_string(
            conn_str
        )  # Initialize the BlobServiceClient

        # Step 5: Upload the original image to Blob Storage
        original_container = "originalimages"  # Container for storing original images
        original_blob_client = blob_service_client.get_blob_client(
            container=original_container, blob=original_blob_name
        )
        original_blob_client.upload_blob(
            image_bytes, overwrite=True
        )  # Upload the original image to Blob Storage

        # Step 6: Upload the thumbnail to Blob Storage
        thumbnail_container = "thumbnails"  # Container for storing thumbnails
        thumbnail_blob_client = blob_service_client.get_blob_client(
            container=thumbnail_container, blob=thumbnail_blob_name
        )
        thumbnail_blob_client.upload_blob(
            thumb_buffer.getvalue(), overwrite=True
        )  # Upload the thumbnail to Blob Storage

        # Step 7: Generate the URLs for both the original image and the thumbnail
        original_url = original_blob_client.url  # URL of the uploaded original image
        thumbnail_url = thumbnail_blob_client.url  # URL of the uploaded thumbnail

        # Prepare the response body with the URLs
        response_body = {"original_url": original_url, "thumbnail_url": thumbnail_url}

        # Return a successful response with the URLs in JSON format
        return func.HttpResponse(
            json.dumps(response_body), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        # Log any errors during processing and return a failure response
        logging.error(f"Error processing image: {e}")
        return func.HttpResponse(
            "Error processing image", status_code=500
        )  # Return error if any exception occurs
