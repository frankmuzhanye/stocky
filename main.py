import os
import time
import requests
import shutil
import logging

# Define constants
LOCAL_FOLDER = r"C:\receipts"
TEMP_FOLDER = r"C:\receipts\temp"
PDF_URL = "https://bms.beautybychichi.org/reports/receipts/POS_Receipt.pdf"
DELETE_URL = "https://bms.beautybychichi.org/reports/receipts/delete_file.php?file=POS_Receipt.pdf"
CHECK_INTERVAL = 10  # Check every 10 seconds
MIN_FILE_SIZE_KB = 1  # Minimum file size in kilobytes

# Ensure TEMP_FOLDER exists
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler for logging to a file
file_handler = logging.FileHandler(os.path.join(TEMP_FOLDER, 'script.log'))
file_handler.setLevel(logging.INFO)

# Console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define the logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def download_pdf(url, dest_folder):
    try:
        logger.info(f"Attempting to download receipt")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_name = url.split("/")[-1]  # Extract file name from URL
            file_path = os.path.join(dest_folder, file_name)
            with open(file_path, 'wb') as file:
                shutil.copyfileobj(response.raw, file)
            logger.info(f"File downloaded successfully")
            return file_path
        else:
            logger.error(f"Failed to download file: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Exception in download_pdf: {str(e)}")
        return None

def is_file_size_valid(file_path, min_size_kb):
    try:
        file_size = os.path.getsize(file_path)  # Get file size in bytes
        valid = file_size >= (min_size_kb * 1024)  # Convert KB to bytes
        logger.info(f"Waiting for new receipt")
        return valid
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False

def delete_remote_file(url):
    try:
        logger.info(f"Processing receipt")
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("Receipt processed successfully.")
        else:
            logger.error(f"Failed to delete remote file: {response.status_code}")
    except Exception as e:
        logger.error(f"Exception in delete_remote_file: {str(e)}")

def main():
    logger.info("Script started.")
    while True:
        try:
            logger.info("Checking new receipt.")
            downloaded_file_path = download_pdf(PDF_URL, TEMP_FOLDER)
            if downloaded_file_path:
                if is_file_size_valid(downloaded_file_path, MIN_FILE_SIZE_KB):
                    downloaded_file_name = os.path.basename(downloaded_file_path)
                    local_file_path = os.path.join(LOCAL_FOLDER, downloaded_file_name)

                    if not os.path.exists(local_file_path) or downloaded_file_name != os.path.basename(local_file_path):
                        shutil.copy(downloaded_file_path, local_file_path)  # Copy instead of move to keep temp file
                        logger.info(f"Local file updated")
                    else:
                        logger.info("Files are identical. No update needed.")

                    # Wait for 1 second before deleting the remote file
                    time.sleep(1)
                    delete_remote_file(DELETE_URL)

                else:
                    logger.warning(f"No new receipt available")
                    os.remove(downloaded_file_path)  # Remove the small file
            else:
                logger.warning("Download failed. Skipping this check.")

            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Exception in main loop: {str(e)}")
            # Continue the loop even if an exception occurs

if __name__ == "__main__":
    main()
