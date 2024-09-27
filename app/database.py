# database.py

import json
import os
from datetime import datetime
import uuid
import logging

# Configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_DIR = "local_storage"

def ensure_storage_dir():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        logger.info(f"Created storage directory at '{STORAGE_DIR}'.")

def save_to_database(data, filename):
    ensure_storage_dir()
    logger.info(f"Saving document '{filename}' to database.")
    try:
        document_id = str(uuid.uuid4())
        logger.info(f"doc id is'{document_id}'.")
    except Exception as e:
        logger.error(f"Failed to generate document ID: {e}")
        raise Exception(f"Failed to generate document ID: {e}")
    try:
        save_data = {
            "id": document_id,
            "filename": filename,
            "date": datetime.now().isoformat(),
            "data": json.dumps(data)  # Store data as-is (assuming it's serializable)
        }
        file_path = os.path.join(STORAGE_DIR, f"{document_id}.json")
        with open(file_path, "w") as f:
            json.dump(save_data, f, indent=4)
        logger.info(f"Document '{filename}' saved with ID '{document_id}'.")
        return document_id
    except Exception as e:
        logger.error(f"Failed to save document '{filename}': {e}")
        raise Exception(f"Failed to save document: {e}")

def get_saved_documents():
    ensure_storage_dir()
    documents = []
    for filename in os.listdir(STORAGE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(STORAGE_DIR, filename)
            try:
                with open(file_path, "r") as f:
                    documents.append(json.load(f))
            except json.JSONDecodeError:
                logger.warning(f"Corrupted file detected and skipped: {filename}")
            except Exception as e:
                logger.error(f"Error reading file '{filename}': {e}")
    return documents

def delete_document(document_id):
    file_path = os.path.join(STORAGE_DIR, f"{document_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Document with ID '{document_id}' deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}': {e}")
            raise Exception(f"Failed to delete document: {e}")
    else:
        logger.warning(f"Attempted to delete non-existent document ID '{document_id}'.")
        raise Exception("Document not found.")
