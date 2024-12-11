import json
import os
from datetime import datetime
import uuid
import logging
from pymongo import MongoClient
from sqlalchemy import create_engine, text
import pandas as pd


# Configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_DIR = "local_storage"


def ensure_storage_dir():
    """
    Ensures the existence of the storage directory. If it doesn't exist,
    it creates it.
    """
    try:
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR)
            logger.info(f"Created storage directory at '{STORAGE_DIR}'.")
    except Exception as e:
        logger.error(f"Failed to ensure storage directory: {e}")
        raise Exception(f"Failed to ensure storage directory: {e}")


def save_to_database(data, filename):
    """
    Saves a document to a local JSON file in the 'local_storage' directory.

    Parameters:
    - data: The content to be stored in the document (must be serializable).
    - filename: The name of the file (used for logging purposes).

    Returns:
    - document_id: The unique identifier generated for the saved document.
    """
    try:
        ensure_storage_dir()
        logger.info(f"Saving document '{filename}' to database.")
        document_id = str(uuid.uuid4())  # Generate a unique document ID
        logger.info(f"doc id is'{document_id}'.")
    except Exception as e:
        logger.error(f"Failed to generate document ID: {e}")
        raise Exception(f"Failed to generate document ID: {e}")

    try:
        # Prepare the document data
        save_data = {
            "id": document_id,
            "filename": filename,
            "date": datetime.now().isoformat(),
            "data": json.dumps(data),  # Store data as-is (assuming it's serializable)
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
    """
    Retrieves all the documents stored in the local 'local_storage' directory.

    Returns:
    - A list of all saved documents (in JSON format).
    """
    try:
        ensure_storage_dir()
        documents = []
        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(STORAGE_DIR, filename)
                try:
                    with open(file_path, "r") as f:
                        documents.append(
                            json.load(f)
                        )  # Load each document as a Python dictionary
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted file detected and skipped: {filename}")
                except Exception as e:
                    logger.error(f"Error reading file '{filename}': {e}")
        return documents
    except Exception as e:
        logger.error(f"Failed to retrieve saved documents: {e}")
        raise Exception(f"Failed to retrieve saved documents: {e}")


def delete_document(document_id):
    """
    Deletes a document from the local storage by its document ID.

    Parameters:
    - document_id: The unique identifier of the document to be deleted.

    Returns:
    - True if deletion was successful, raises an exception otherwise.
    """
    try:
        file_path = os.path.join(STORAGE_DIR, f"{document_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)  # Remove the file
            logger.info(f"Document with ID '{document_id}' deleted successfully.")
            return True
        else:
            logger.warning(
                f"Attempted to delete non-existent document ID '{document_id}'."
            )
            raise Exception("Document not found.")
    except Exception as e:
        logger.error(f"Failed to delete document '{document_id}': {e}")
        raise Exception(f"Failed to delete document: {e}")


def save_to_mongodb(data, filename):
    """
    Saves a document to a MongoDB database.

    Parameters:
    - data: The content to be stored in the document (must be serializable).
    - filename: The name of the file (used for logging purposes).

    Returns:
    - document_id: The unique identifier generated for the saved document.
    """
    try:
        logger.info(f"Saving document '{filename}' to MongoDB database.")
        document_id = str(uuid.uuid4())  # Generate a unique document ID
        logger.info(f"doc id is'{document_id}'.")
    except Exception as e:
        logger.error(f"Failed to generate document ID: {e}")
        raise Exception(f"Failed to generate document ID: {e}")

    try:
        # Prepare MongoDB document
        mongo_data = {
            "id": document_id,
            "filename": filename,
            "date": datetime.now().isoformat(),
            "data": json.dumps(data),  # Store data as a JSON string
        }

        mongo_uri = "mongodb://localhost:27017/"
        db_name = "transformodocs_db"
        collection_name = "transformodocs_collection"

        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        print("Connected to MongoDB")

        # Access the MongoDB collection
        db = client[db_name]
        collection = db[collection_name]

        # Insert document(s) into MongoDB
        if isinstance(mongo_data, list):
            collection.insert_many(mongo_data)
            print(
                f"Inserted {len(mongo_data)} documents into '{db_name}.{collection_name}'"
            )
        else:
            collection.insert_one(mongo_data)
            print(f"Inserted 1 document into '{db_name}.{collection_name}'")

        # Close the MongoDB connection
        client.close()
        print("Connection to MongoDB closed")
        return document_id
    except Exception as e:
        logger.error(f"Failed to save document '{filename}': {e}")
        raise Exception(f"Failed to save document: {e}")


def get_mongo_data():
    """
    Retrieves all documents stored in the MongoDB collection.

    Returns:
    - A list of documents from the MongoDB database.
    """
    try:
        mongo_uri = "mongodb://localhost:27017/"
        db_name = "transformodocs_db"
        collection_name = "transformodocs_collection"
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        documents = list(collection.find())  # Fetch all documents
        client.close()
        print("Connection to MongoDB closed")
        return documents
    except Exception as e:
        logger.error(f"Failed to retrieve data from MongoDB: {e}")
        raise Exception(f"Failed to retrieve data from MongoDB: {e}")


def delete_mongo_data(document_id):
    """
    Deletes a document from MongoDB by its document ID.

    Parameters:
    - document_id: The unique identifier of the document to be deleted.

    Returns:
    - True if deletion was successful, raises an exception otherwise.
    """
    try:
        mongo_uri = "mongodb://localhost:27017/"
        db_name = "transformodocs_db"
        collection_name = "transformodocs_collection"
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        result = collection.delete_one({"id": document_id})  # Delete the document by ID
        client.close()
        print("Connection to MongoDB closed")
        return True
    except Exception as e:
        logger.error(f"Failed to delete document from MongoDB: {e}")
        raise Exception(f"Failed to delete document from MongoDB: {e}")


def save_to_sqldb(data, filename):
    """
    Saves a document to a SQLite database.

    Parameters:
    - data: The content to be stored in the document (must be serializable).
    - filename: The name of the file (used for logging purposes).

    Returns:
    - document_id: The unique identifier generated for the saved document.
    """
    try:
        logger.info(f"Saving document '{filename}' to SQLDB database.")
        document_id = str(uuid.uuid4())  # Generate a unique document ID
        logger.info(f"doc id is'{document_id}'.")
    except Exception as e:
        logger.error(f"Failed to generate document ID: {e}")
        raise Exception(f"Failed to generate document ID: {e}")

    try:
        # Prepare the SQL data
        sql_data = {
            "id": document_id,
            "filename": filename,
            "date": datetime.now().isoformat(),
            "data": json.dumps(data),  # Store data as a JSON string
        }

        # Convert the data to a pandas DataFrame
        df = pd.json_normalize(sql_data)

        # Connect to SQLite database
        engine = create_engine("sqlite:///transformodocs.db")

        # Save DataFrame to SQL table
        table_name = "processed_docs"
        df.to_sql(table_name, con=engine, if_exists="append", index=False)

        print(f"Data saved to SQL table '{table_name}'")
        return document_id
    except Exception as e:
        logger.error(f"Failed to save document '{filename}': {e}")
        raise Exception(f"Failed to save document: {e}")


def get_sql_data():
    """
    Retrieves all documents stored in the SQLite database.

    Returns:
    - A list of documents from the SQLite database.
    """
    try:
        engine = create_engine("sqlite:///transformodocs.db")
        query = text("SELECT * FROM processed_docs")  # SQL query to fetch all records
        with engine.connect() as connection:
            result = connection.execute(query)
        documents = result.fetchall()  # Fetch all rows as a list of tuples
        return documents
    except Exception as e:
        logger.error(f"Failed to retrieve data from SQLite: {e}")
        raise Exception(f"Failed to retrieve data from SQLite: {e}")


def delete_sql_data(document_id):
    """
    Deletes a document from the SQLite database by its document ID.

    Parameters:
    - document_id: The unique identifier of the document to be deleted.

    Returns:
    - True if deletion was successful.
    """
    try:
        engine = create_engine("sqlite:///transformodocs.db")
        query = text(
            "DELETE FROM processed_docs WHERE id = :document_id"
        )  # SQL delete query
        with engine.connect() as connection:
            result = connection.execute(
                query, {"document_id": document_id}
            )  # Execute the query
            connection.commit()  # Commit the changes
        return True
    except Exception as e:
        logger.error(f"Failed to delete document from SQLite: {e}")
        raise Exception(f"Failed to delete document from SQLite: {e}")
