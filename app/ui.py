import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from extractor import validate_document, extract_text
from processor import process_document, ask_question_to_document
from database import save_to_database, get_saved_documents, delete_document
import pandas as pd
from datetime import datetime
import json

def setup_page():
    st.set_page_config(page_title="Transformo-Docs", layout="wide")
    st.sidebar.title("📄 Transformo Docs")
    pages = {
        "Home": home_page,
        "Upload Document and Processing": document_processing_page,
        "Saved Documents Storage": saved_documents_page,
        "Chat Interface": chat_interface_page,
    }
    page = st.sidebar.radio("Navigate", list(pages.keys()))
    pages[page]()

def home_page():
    st.title("🏠 Welcome to Transformo Docs")
    st.write("""
        ### 🚀 Transformo Docs: Empowering Document Management

    Transformo Docs is a powerful solution designed to tackle the challenge of non-machine-readable documents like PDFs and Word files. 🌐 This app automates the conversion of such documents into machine-readable formats, making them searchable, accessible, and ready for AI integration. 🤖

    Whether you're working with scanned documents or files generated through software, Transformo Docs ensures your data is always organized and easily accessible. 📊 Unlock the potential of automation, advanced analytics, and compliance with Transformo Docs—streamline your document management and boost productivity. 📈
    """)
    st.info("Use the sidebar to navigate through different features of the application.")

def document_processing_page():
    st.title("🔄 Document Processing")
    
    uploaded_file = upload_document()
    template = st.selectbox(
    "Choose a template for extraction",
    ["Default", "Data Only", "Analytics Only", "Specific Entities"],
    help="Select a predefined template for structuring the output."
)
    custom_fields = st.multiselect(
    "Select custom fields to extract",
    ["Persons", "Organizations", "Locations", "Dates"],
    help="Choose specific entity types you want to extract from the document."
)
    
    result = None
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            try:
                file_type = validate_document(uploaded_file)
                extracted_text = extract_text(uploaded_file, file_type)
                template = template.lower().replace(" ", "_") if template != "Default" else None
                custom_fields = [field.lower() for field in custom_fields] if custom_fields else None
                result = process_document(extracted_text, template, custom_fields)
                
                if result["warnings"]:
                    st.warning("Processing completed with warnings:")
                    for warning in result["warnings"]:
                        st.write(warning)
                else:
                    st.success("Document processed successfully!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if result:
        display_export_options(result, uploaded_file)
        display_analytics(result)
        display_graphs(result)
        display_database_options(result, uploaded_file.name)

def upload_document():
    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt", "xlsx"])
    if uploaded_file:
        st.info(f"File '{uploaded_file.name}' uploaded successfully. Choose a template and custom fields for extraction.")
    return uploaded_file

def display_export_options(result, uploaded_file):
    st.subheader("💾 Export Options")
    export_format = st.selectbox("Choose export format", ["JSON", "XML"])
    
    if export_format == "JSON":
        download_content = result['json_output']
        file_extension = "json"
    else:
        download_content = result['xml_output']
        file_extension = "xml"

    download_filename = f"{uploaded_file.name}_processed.{file_extension}"
    st.download_button(
        label=f"Download {export_format} File",
        data=download_content,
        file_name=download_filename,
        mime=f"application/{file_extension}"
    )

    with st.expander("View Processed Output"):
        st.code(download_content, language=file_extension.lower())

def display_analytics(result):
    st.subheader("📊 Document Analytics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📏 Basic Metrics")
        st.write(f"**Word Count:** {result['analytics']['word_count']}")
        st.write(f"**Sentence Count:** {result['analytics']['sentence_count']}")
        st.write(f"**Average Sentence Length:** {result['analytics']['average_sentence_length']:.2f} words")

        st.markdown("### 🏷️ Named Entities")
        st.write(f"**Entity Count:** {result['analytics']['entity_count']}")
        st.write("**Most Common Entities:**")
        for entity, count in result['analytics']['most_common_entities']:
            st.write(f"- {entity}: {count}")

    with col2:
        st.markdown("### 🔑 Keywords")
        st.write(f"**Keyword Count:** {result['analytics']['keyword_count']}")

        st.markdown("### 📊 Word Frequency")
        st.write("**Most Common Words:**")
        for word, count in result['analytics']['most_common_words']:
            st.write(f"- {word}: {count}")

    with st.expander("📝 Document Preview"):
        preview_text = result['extracted_text'][:500] + "..." if len(result['extracted_text']) > 500 else result['extracted_text']
        st.text_area("First 500 characters", preview_text, height=200)
        
def display_graphs(result):
    st.subheader("📈 Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Word Frequency Graph
        word_freq = result['analytics']['most_common_words'][:10]  # Top 10 words
        fig = px.bar(
            x=[word for word, _ in word_freq],
            y=[count for _, count in word_freq],
            labels={'x': 'Word', 'y': 'Frequency'},
            title='Top 10 Most Frequent Words'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Named Entities Graph
        entity_freq = result['analytics']['most_common_entities'][:10]  # Top 10 entities
        fig = px.bar(
            x=[entity for entity, _ in entity_freq],
            y=[count for _, count in entity_freq],
            labels={'x': 'Entity', 'y': 'Frequency'},
            title='Top 10 Most Common Named Entities'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Basic Metrics Graph
    metrics = {
        'Word Count': result['analytics']['word_count'],
        'Sentence Count': result['analytics']['sentence_count'],
        'Avg Sentence Length': round(result['analytics']['average_sentence_length'], 2)
    }
    fig = go.Figure(data=[
        go.Bar(name=metric, x=[metric], y=[value])
        for metric, value in metrics.items()
    ])
    fig.update_layout(title_text='Basic Document Metrics', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    # Keyword Information
    st.subheader("🔑 Keyword Information")
    st.write(f"**Total Keywords:** {result['analytics']['keyword_count']}")
    st.write("**Top Keywords:**")
    keyword_data = pd.DataFrame(result['analytics']['most_common_words'], columns=['Keyword', 'Count'])
    st.dataframe(keyword_data)

def display_database_options(result, filename):
    st.subheader("💽 Database Options")
    st.info("Choose a database to save the processed document. Currently, only local storage is available.")
    database_options = ["Local Storage", "MongoDB (Disabled)", "PostgreSQL (Disabled)", "MySQL (Disabled)"]
    selected_db = st.selectbox("Select Database", database_options)
    
    if selected_db == "Local Storage":
        if st.button("Save to Local Storage"):
            save_to_database(result, filename)
            st.success("Document saved to local storage successfully!")
    else:
        st.warning("Selected database option is currently disabled.")

def saved_documents_page():
    st.title("💾 Saved Documents")
    st.info("This page displays all documents saved in the local storage.")
    
    documents = get_saved_documents()
    if not documents:
        st.warning("No saved documents found.")
        return
    
    df = pd.DataFrame(documents)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{row['filename']}** - {row['date'].strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            if st.button("Preview", key=f"preview_{row['id']}"):
                st.json(row['data'])
        with col3:
            if st.button("Download", key=f"download_{row['id']}"):
                st.download_button(
                    label="Download JSON",
                    data=row['data'],
                    file_name=f"{row['filename']}_processed.json",
                    mime="application/json"
                )
        with col4:
            if st.button("Delete", key=f"delete_{row['id']}"):
                delete_document(row['id'])
                st.experimental_rerun()

def chat_interface_page():
    st.title("💬 Chat with Your Document")
    st.info("This feature allows you to ask questions about your processed documents.")

    documents = get_saved_documents()
    if not documents:
        st.warning("No saved documents found. Process and save a document first.")
        return

    selected_doc = st.selectbox("Select a document to chat with", [doc['filename'] for doc in documents])
    selected_data = next(doc for doc in documents if doc['filename'] == selected_doc)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_query = st.text_input("Ask a question about the document:")

    if user_query:
        document_text = json.loads(selected_data['data'])['extracted_text']
        answer = ask_question_to_document(user_query, document_text)
        st.session_state["chat_history"].append({"question": user_query, "answer": answer})

    if st.session_state["chat_history"]:
        st.write("### 🗨️ Chat History")
        for chat in st.session_state["chat_history"]:
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Transformo Docs:** {chat['answer']}")

    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []

def main():
    setup_page()

if __name__ == "__main__":
    main()