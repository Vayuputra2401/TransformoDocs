import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from extractor import validate_document, extract_text
from processor import process_document, ask_question_to_document
from database import (
    save_to_database,
    get_saved_documents,
    delete_document,
    save_to_mongodb,
    get_mongo_data,
    delete_mongo_data,
    save_to_sqldb,
    get_sql_data,
    delete_sql_data,
)
from datetime import datetime
import json
from PIL import Image
import io
import requests
import os
import jwt
import datetime
import pyperclip


# Function to calculate file sizes
def calculate_file_sizes(uploaded_file, result):
    original_size_mb = uploaded_file.size / (1024 * 1024)
    extracted_size_mb = len(json.dumps(result["json_output"])) / (1024 * 1024)
    return original_size_mb, extracted_size_mb


# Function to load and display the logo
def load_logo():
    # First, try to load the logo from the local assets folder
    local_logo_path = os.path.join("assets", "logo.png")
    if os.path.exists(local_logo_path):
        return Image.open(local_logo_path)

    # If local logo is not found, try to fetch from GitHub
    github_logo_url = "https://raw.githubusercontent.com/vayuputra2401/transformodocs/main/app/assets/logo-white.png"
    try:
        response = requests.get(github_logo_url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        st.warning(f"Failed to fetch logo from GitHub: {str(e)}")

    # If both local and GitHub logo fetch fail, return None
    return None


# Main page setup function
def setup_page():
    st.set_page_config(page_title="Transformo-Docs", layout="wide")

    # Load and display logo
    logo = load_logo()
    if logo:
        st.sidebar.image(logo, width=250)
    st.sidebar.title("📄 Transformo Docs")
    pages = {
        "Home": home_page,
        "Upload Document and Processing": document_processing_page,
        "Saved Documents Storage": saved_documents_page,
        "Chat Interface": chat_interface_page,
        "API Token and Upload": api_token_page,
    }
    page = st.sidebar.radio("Navigate", list(pages.keys()))
    pages[page]()


# Home page function
def home_page():
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("🏠 Welcome to Transformo Docs")
        st.markdown(
            """
        <style>
        .big-font {
            font-size:20px !important;
            color: #1E88E5;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p class="big-font">🚀 Empowering Document Management</p>',
            unsafe_allow_html=True,
        )

        st.write(
            """
        Transformo Docs is a powerful solution designed to tackle the challenge of non-machine-readable documents like PDFs and Word files. 
        
        🌐 This app automates the conversion of such documents into machine-readable formats, making them:
        - 🔍 Searchable
        - 📄 Accessible
        - 🤖 Ready for AI integration
        
        Whether you're working with scanned documents or files generated through software, Transformo Docs ensures your data is always organized and easily accessible.
        """
        )

        st.markdown(
            """
        ---
        ### 🎯 Key Features
        - 📊 Advanced Analytics
        - 🔄 Automated Conversion
        - 🔐 Compliance Ready
        - 📈 Productivity Boost
        """
        )

    st.info(
        "Use the sidebar to navigate through different features of the application."
    )

    # Custom button styling
    st.markdown(
        """
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# Document processing page function
def document_processing_page():
    st.title("🔄 Document Processing")

    # Add a toggle for scanned document processing
    processing_mode = st.radio(
        "Select Document Type", ["Regular Document", "Scanned Document (OCR)"]
    )

    # Determine upload type based on processing mode
    is_scanned = processing_mode == "Scanned Document (OCR)"
    uploaded_file = upload_document(allow_scanned=is_scanned)

    template = st.selectbox(
        "Choose a template for extraction",
        ["Default", "Data Only", "Analytics Only", "Specific Entities"],
        help="Select a predefined template for structuring the output.",
    )
    custom_fields = st.multiselect(
        "Select specific information to extract:",
        [
            "Persons",
            "Organizations",
            "Locations",
            "Dates",
            "Money",
            "Percent",
            "Time",
            "Quantity",
            "Ordinal",
            "Cardinal",
        ],
        help="Choose specific entity types you want to extract from the document.",
    )

    result = None
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            try:
                # Validate and extract text from the document
                file_type = validate_document(uploaded_file, is_scanned)
                extracted_text = extract_text(uploaded_file, file_type, is_scanned)

                # Process the document with selected template and custom fields
                template = (
                    template.lower().replace(" ", "_")
                    if template != "Default"
                    else None
                )
                custom_fields = (
                    [field.lower() for field in custom_fields]
                    if custom_fields
                    else None
                )
                result = process_document(extracted_text, template, custom_fields)

                if result["warnings"]:
                    st.warning("Processing completed with warnings:")
                    for warning in result["warnings"]:
                        st.write(warning)
                else:
                    st.success("Document processed successfully!")

                # Save result in session state
                st.session_state.result = result
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if "result" in st.session_state:
        display_export_options(st.session_state.result, uploaded_file)
        display_analytics(st.session_state.result)
        display_graphs(st.session_state.result, uploaded_file)
        display_database_options(st.session_state.result, uploaded_file.name)


# Function to handle document upload
def upload_document(allow_scanned=False):
    st.subheader("📤 Upload Document")
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    # Different file uploaders based on scanned option
    if not allow_scanned:
        uploaded_file = st.file_uploader(
            "Choose a file", type=["pdf", "docx", "txt", "xlsx"]
        )
        is_scanned = False
    else:
        uploaded_file = st.file_uploader("Choose a scanned document", type=["pdf"])
        is_scanned = True

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.is_scanned = is_scanned
        st.info(f"File '{uploaded_file.name}' uploaded successfully.")

    return st.session_state.uploaded_file


# Function to display export options
def display_export_options(result, uploaded_file):
    st.subheader("💾 Export Options")
    export_format = st.selectbox("Choose export format", ["JSON", "XML"])

    if export_format == "JSON":
        download_content = result["json_output"]
        file_extension = "json"
    else:
        download_content = result["xml_output"]
        file_extension = "xml"

    download_filename = f"{uploaded_file.name}_processed.{file_extension}"
    st.download_button(
        label=f"Download {export_format} File",
        data=download_content,
        file_name=download_filename,
        mime=f"application/{file_extension}",
    )

    with st.expander("View Processed Output"):
        st.code(download_content, language=file_extension.lower())


# Function to display analytics
def display_analytics(result):
    st.subheader("📊 Document Analytics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📏 Basic Metrics")
        st.write(f"**Word Count:** {result['analytics']['word_count']}")
        st.write(f"**Sentence Count:** {result['analytics']['sentence_count']}")
        st.write(
            f"**Average Sentence Length:** {result['analytics']['average_sentence_length']:.2f} words"
        )

        st.markdown("### 🏷️ Named Entities")
        st.write(f"**Entity Count:** {result['analytics']['entity_count']}")
        st.write("**Most Common Entities:**")
        for entity, count in result["analytics"]["most_common_entities"]:
            st.write(f"- {entity}: {count}")

    with col2:
        st.markdown("### 🔑 Keywords")
        st.write(f"**Keyword Count:** {result['analytics']['keyword_count']}")

        st.markdown("### 📊 Word Frequency")
        st.write("**Most Common Words:**")
        for word, count in result["analytics"]["most_common_words"]:
            st.write(f"- {word}: {count}")

    with st.expander("📝 Document Preview"):
        preview_text = (
            result["extracted_text"][:500] + "..."
            if len(result["extracted_text"]) > 500
            else result["extracted_text"]
        )
        st.text_area("First 500 characters", preview_text, height=200)


# Function to display graphs
def display_graphs(result, uploaded_file):
    st.subheader("📈 Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Word Frequency Graph
        word_freq = result["analytics"]["most_common_words"][:10]  # Top 10 words
        fig = px.bar(
            x=[word for word, _ in word_freq],
            y=[count for _, count in word_freq],
            labels={"x": "Word", "y": "Frequency"},
            title="Top 10 Most Frequent Words",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Named Entities Graph
        entity_freq = result["analytics"]["most_common_entities"][
            :10
        ]  # Top 10 entities
        fig = px.bar(
            x=[entity for entity, _ in entity_freq],
            y=[count for _, count in entity_freq],
            labels={"x": "Entity", "y": "Frequency"},
            title="Top 10 Most Common Named Entities",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Basic Metrics Graph
    metrics = {
        "Word Count": result["analytics"]["word_count"],
        "Sentence Count": result["analytics"]["sentence_count"],
        "Avg Sentence Length": round(result["analytics"]["average_sentence_length"], 2),
    }
    fig = go.Figure(
        data=[
            go.Bar(name=metric, x=[metric], y=[value])
            for metric, value in metrics.items()
        ]
    )
    fig.update_layout(title_text="Basic Document Metrics", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    # File Size Comparison Graph
    original_size, extracted_size = calculate_file_sizes(uploaded_file, result)
    size_diff = original_size - extracted_size
    size_diff_percentage = (size_diff / original_size) * 100

    fig = go.Figure(
        data=[
            go.Bar(name="Original Size", x=["Document Size"], y=[original_size]),
            go.Bar(name="Extracted Size", x=["Document Size"], y=[extracted_size]),
        ]
    )
    fig.update_layout(title_text="Document Size Comparison (MB)", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"Size reduction: {size_diff:.2f} MB ({size_diff_percentage:.2f}%)")

    # Keyword Information
    st.subheader("🔑 Keyword Information")
    st.write(f"**Total Keywords:** {result['analytics']['keyword_count']}")
    st.write("**Top Keywords:**")
    keyword_data = pd.DataFrame(
        result["analytics"]["most_common_words"], columns=["Keyword", "Count"]
    )
    st.dataframe(keyword_data)


# Function to display database options
def display_database_options(result, filename):
    st.subheader("💽 Database Options")
    st.info(
        "Choose a database to save the processed document. Currently, only local storage is available."
    )
    database_options = ["Secure Storage", "MongoDB Storage", "MySQL Storage"]
    selected_db = st.selectbox("Select Database", database_options)

    if selected_db == "Secure Storage":
        if st.button("Save to Secure Storage"):
            save_to_database(result, filename)
            st.success("Document saved to Secure storage successfully!")
    elif selected_db == "MongoDB Storage":
        if st.button("Save to MongoDB Storage"):
            save_to_mongodb(result, filename)
            st.success("Document saved to MongoDB storage successfully!")
    elif selected_db == "MySQL Storage":
        if st.button("Save to MySQL Storage"):
            save_to_sqldb(result, filename)
            st.success("Document saved to MySQL storage successfully!")

    else:
        st.warning("Selected database option is currently disabled.")


# Function for saved documents page
def saved_documents_page():
    st.title("💾 Saved Documents")
    st.info("This page displays all documents saved in the selected storage.")

    database_options = ["Secure Storage", "MongoDB Storage", "MySQL Storage"]
    selected_db = st.selectbox("Select Database", database_options)
    if selected_db == "Secure Storage":
        documents = get_saved_documents()
    elif selected_db == "MongoDB Storage":
        documents = get_mongo_data()
    elif selected_db == "MySQL Storage":
        documents = get_sql_data()
    else:
        st.warning("Selected database option is currently disabled.")
    if not documents:
        st.warning("No saved documents found.")
        return

    df = pd.DataFrame(documents)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(
                f"**{row['filename']}** - {row['date'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
        with col2:
            if st.button("Preview", key=f"preview_{row['id']}"):
                st.json(row["data"])
        with col3:
            if st.button("Download", key=f"download_{row['id']}"):
                json_object = json.loads(row["data"])
                st.download_button(
                    label="Download JSON",
                    data=json_object["json_output"],
                    file_name=f"{row['filename']}_processed.json",
                    mime="application/json",
                )
                st.download_button(
                    label="Download XML",
                    data=json_object["xml_output"],
                    file_name=f"{row['filename']}_processed.xml",
                    mime="application/xml",
                )
        with col4:
            if st.button("Delete", key=f"delete_{row['id']}"):
                if selected_db == "Secure Storage":
                    delete_document(row["id"])
                elif selected_db == "MongoDB Storage":
                    delete_mongo_data(row["id"])
                elif selected_db == "MySQL Storage":
                    delete_sql_data(row["id"])
                else:
                    st.warning("Selected database option is currently disabled.")
                st.rerun()


# Function for chat interface page
def chat_interface_page():
    st.title("💬 Chat with Your Document")
    st.info("This feature allows you to ask questions about your processed documents.")

    documents = get_saved_documents()
    if not documents:
        st.warning("No saved documents found. Process and save a document first.")
        return

    selected_doc = st.selectbox(
        "Select a document to chat with", [doc["filename"] for doc in documents]
    )
    selected_data = next(doc for doc in documents if doc["filename"] == selected_doc)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_query = st.text_input("Ask a question about the document:")

    if user_query:
        document_text = json.loads(selected_data["data"])["extracted_text"]
        answer = ask_question_to_document(user_query, document_text)
        st.session_state["chat_history"].append(
            {"question": user_query, "answer": answer}
        )

    if st.session_state["chat_history"]:
        st.write("### 🗨️ Chat History")
        for chat in st.session_state["chat_history"]:
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Transformo Docs:** {chat['answer']}")

    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        st.success("Chat history cleared!")


# Function to handle API token generation and management
def api_token_page():
    st.title("🔑 API Token and Upload")
    st.info(
        "Generate API tokens and use them to upload and process documents via API. You can use these tokens with tools like Postman or other websites."
    )

    # Initialize session state for tokens
    if "tokens" not in st.session_state:
        st.session_state.tokens = []

    # Generate API token
    if st.button("Generate API Token"):
        token = jwt.encode(
            {"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            "a_very_strong_secret_key_that_should_be_kept_private",
            algorithm="HS256",
        )
        st.session_state.tokens.append(token)

    # Display tokens in a table with aligned buttons
    if st.session_state.tokens:
        st.subheader("Generated API Tokens")
        for i, token in enumerate(st.session_state.tokens):
            cols = st.columns([4, 1, 1, 1])
            with cols[0]:
                st.text_input(
                    f"Token {i+1}",
                    token,
                    key=f"token_{i}",
                    type="password",
                    label_visibility="collapsed",
                )
            with cols[1]:
                if st.button("📋 Copy", key=f"copy_{i}"):
                    pyperclip.copy(token)
                    st.success(f"Token {i+1} copied to clipboard!")
            with cols[2]:
                if st.button("❌ Delete", key=f"delete_{i}"):
                    st.session_state.tokens.pop(i)
                    st.experimental_rerun()
            with cols[3]:
                if st.button("📊 Stats", key=f"stats_{i}"):
                    try:
                        response = requests.get("http://localhost:8000/api/stats")
                        if response.status_code == 200:
                            stats = response.json()
                            st.write(f"Total Requests: {stats['request_count']}")
                            st.write(
                                f"Average Latency: {stats['average_latency']:.2f} seconds"
                            )
                        else:
                            st.error(
                                f"Error: {response.json().get('detail', 'Unknown error')}"
                            )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Upload file using API token
    uploaded_file = st.file_uploader(
        "Choose a file to upload via API", type=["pdf", "docx", "txt", "xlsx"]
    )
    api_token = st.text_input("Enter your API token")

    if uploaded_file and api_token:
        if st.button("Upload and Process via API"):
            try:
                headers = {"Authorization": f"Bearer {api_token}"}
                # Properly format the file upload
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }
                response = requests.post(
                    "http://localhost:8000/api/upload", headers=headers, files=files
                )
                if response.status_code == 200:
                    st.success("Document processed successfully!")
                    st.json(response.json())
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


# Main function to run the Streamlit app
def main():
    setup_page()


# Entry point of the script
if __name__ == "__main__":
    main()
