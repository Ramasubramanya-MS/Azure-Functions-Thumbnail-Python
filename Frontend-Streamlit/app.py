"""
# This streamlit application interacts with a deployed Azure Function through a POST request.
# The Azure Function handles the image processing, and the URLs for both the
# original image and the thumbnail are returned to the user for further use.
"""

import streamlit as st
import requests
import os
from PIL import Image
import io

# Set the title and description of the Streamlit app
st.title("Image Thumbnail Generator")
st.write("Upload an image to generate a thumbnail")

# File uploader component for image files with accepted formats (jpg, jpeg, png)
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

# Azure Function endpoint URL for generating thumbnails
# Note: Update with the actual endpoint URL after deploying the Azure Function
azure_function_url = "<azure-storage-account-connection-string>"

# Process the uploaded file if any
if uploaded_file is not None:
    # Display the original image
    st.subheader("Original Image")
    image = Image.open(uploaded_file)  # Open image using Pillow (PIL)
    st.image(image, width=300)  # Display the original image with a set width

    # Trigger the thumbnail generation when the button is pressed
    if st.button("Generate Thumbnail"):
        with st.spinner("Generating thumbnail..."):  # Show a spinner while processing
            # Prepare the file data to send in the POST request
            files = {
                "file": (
                    uploaded_file.name,  # Use the original uploaded file name
                    uploaded_file.getvalue(),  # Get the file content as bytes
                    uploaded_file.type,  # Include the MIME type of the file
                )
            }

            try:
                # Send the image to the Azure Function via a POST request
                response = requests.post(azure_function_url, files=files)

                # Check if the response is successful (HTTP status code 200)
                if response.status_code == 200:
                    # Parse the response JSON to extract the URLs
                    data = response.json()
                    original_url = data["original_url"]  # URL of the original image
                    thumbnail_url = data[
                        "thumbnail_url"
                    ]  # URL of the generated thumbnail

                    # Display success message indicating that the thumbnail was generated
                    st.success("Thumbnail generated successfully!")

                    # Create a layout with two columns to display the thumbnail and download options
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Thumbnail")
                        # Fetch and display the generated thumbnail image
                        thumbnail_response = requests.get(
                            thumbnail_url
                        )  # Fetch thumbnail image
                        thumbnail_image = Image.open(
                            io.BytesIO(thumbnail_response.content)
                        )
                        st.image(thumbnail_image)  # Display thumbnail image

                    with col2:
                        st.subheader("Download")
                        # Provide download links for both the original image and thumbnail
                        st.markdown(f"[Download Thumbnail]({thumbnail_url})")
                        st.markdown(f"[Download Original]({original_url})")

                    # Optionally, display the URLs for further reference or debugging
                    with st.expander("Image URLs"):
                        st.text(f"Original image URL: {original_url}")
                        st.text(f"Thumbnail URL: {thumbnail_url}")
                else:
                    # Handle errors from the Azure Function (e.g., incorrect URL or function failure)
                    st.error(f"Error: {response.text}")
            except Exception as e:
                # Handle general exceptions (e.g., network issues or function unavailability)
                st.error(f"Error connecting to Azure Function: {str(e)}")

# Add informational sidebar with app details and usage instructions
st.sidebar.header("About")
st.sidebar.info(
    "This application uses Azure Functions to generate thumbnails "
    "of your uploaded images. The original images and thumbnails "
    "are stored in Azure Blob Storage."
)
