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
from streamlit_option_menu import option_menu
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_lottie import st_lottie
from streamlit_navigation_bar import st_navbar
import pyperclip
import base64
import pandas as pd
from io import BytesIO
from docx import Document
from llm import EnhancedJSONAgent

# Load user data
user_data = pd.read_excel("employees.xlsx")  # Excel file containing user information


# Function to generate JWT token
def generate_token(username, role):
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, "secret_key", algorithm="HS256")
    return token


# Function to verify JWT token
def verify_token(token):
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Function to authenticate user using passcode
def authenticate_user():
    st.title("Passcode Authentication")
    st.write("Please enter your username and passcode")

    username = st.text_input("Username")
    passcode = st.text_input("Passcode", type="password")

    if st.button("Login"):
        user_info = user_data[user_data["username"] == username]
        if not user_info.empty:
            stored_passcode = user_info.iloc[0]["passcode"]
            if str(passcode) == str(stored_passcode):
                role = user_info.iloc[0]["role"]
                token = generate_token(username, role)
                st.success(f"Authentication successful! Welcome, {username}")
                st.write(f"Your role: {role}")
                st.write(f"Your token: {token}")
                st.session_state["token"] = token
            else:
                st.error("Invalid passcode. Please try again.")
        else:
            st.error("Invalid username or passcode. Please try again.")


# Function to check user role
def check_role(required_role):
    token = st.session_state.get("token")
    if token:
        payload = verify_token(token)
        if payload and payload["role"] == required_role:
            return True
    return False


# Function to calculate file sizes
def calculate_file_sizes(uploaded_file, result):
    original_size_mb = uploaded_file.size / (1024 * 1024)
    extracted_size_mb = len(json.dumps(result["json_output"])) / (1024 * 1024)
    return original_size_mb, extracted_size_mb


def load_logo():
    local_logo_path = os.path.join("assets", "logo-white.png")
    if os.path.exists(local_logo_path):
        return Image.open(local_logo_path)

    github_logo_url = "https://raw.githubusercontent.com/vayuputra2401/transformodocs/main/app/assets/logo-white.png"
    try:
        response = requests.get(github_logo_url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        st.warning(f"Failed to fetch logo from GitHub: {str(e)}")

    return None


# Main page setup function with enhanced UI elements
def setup_page():
    st.set_page_config(page_title="Transformo-Docs", layout="wide")

    # # Load and display logo
    # logo = load_logo()
    # if logo:
    #     st.sidebar.image(logo, width=250)
    # st.sidebar.markdown('<div style="background-color: black; padding: 10px 0;">' +
    #                     '<h2 style="color: white; text-align: center;">📄 Transformo Docs</h2>' +
    #                     '</div>', unsafe_allow_html=True)

    st.markdown(
        """
    <style>
    [data-testid="stAppViewContainer"] {
    background-image: linear-gradient(to right top, #232425, #3b5359, #548882, #87be9b, #daf0aa);
    font-family: Arial, sans-serif;
    color: white;
    }
    
    .stButton>button {
    width: 100%;
    height: 3em;
    background: linear-gradient(to right, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
    color: white;
    font-size: 16px;
    font-weight: bold;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 5px;
    cursor: pointer;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    }
    .stButton>button:hover {
        background: linear-gradient(to right, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2));
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    .navbar {
        position: fixed;
        top: 5em;
        left: 2%;
        right: 2%;
        z-index: 10;
        padding: 10px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        border-radius: 15px;        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .navbar-brand {
        color: white;
        font-size: 1.5em;
        font-weight: bold;
        margin-left: 10px;
    }
    .navbar-menu {
        display: flex;
        gap: 15px;
    }
    .navbar-item {
        color: white;
        text-decoration: none;
        padding: 8px 15px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    .navbar-item:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }
    .navbar-item.active {
        background-color: rgba(76, 175, 80, 0.5);
    }
    .navbar h1 {
        text-align: center;
        color: #fff;
        margin: 0;
    }
    .tabs {
        display: flex;
        gap: 10px;
    }
    
    .tab-button {
        background-color: #333;
        color: white;
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        cursor: pointer;
        text-align: center;
    }
    .tab-button:hover {
        background-color: #555;
    }
    .tab-button.selected {
        background-color: #4CAF50;
    }
    .tabs {
        display: flex;
        justify-content: center;
    }
    .content {
        margin-top: 100px;
        
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Define pages
    PAGES = {
        "Home": home_page,
        "Upload": document_processing_page,
        "Storage": saved_documents_page,
        "Chat Interface": chat_interface_page,
        "API Token": api_token_page,
        "Login": authenticate_user,
        "Logout": logout_user,
    }

    # Initialize session state for page selection if not set
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Home"

    #     # Navbar structure with dynamic buttons
    #     st.markdown("""
    #         <div class="navbar">
    #             <div class="navbar-brand">Transformo Docs</div>
    #             <div class="navbar-menu">
    #     """, unsafe_allow_html=True)

    #     # Close the navbar HTML
    #     st.markdown("</div></div>", unsafe_allow_html=True)

    #     st.markdown("""
    #     <style>
    #     .navbar-container {
    #         padding: 20px;
    #     }
    #     </style>
    # """, unsafe_allow_html=True)

    # # Create a container for the navbar
    # with st.container():
    #     # Start the custom navbar container with light grey background

    #     # Create a navbar layout with buttons for each page dynamically
    #     nav_cols = st.columns([1] * len(PAGES))  # Equal columns for spacing
    #     for i, (page_name, page_func) in enumerate(PAGES.items()):
    #         with nav_cols[i]:
    #             # Create a button for each page in the navbar
    #             button = st.button(page_name, key=f"nav_{page_name}")
    #             if button:
    #                 st.session_state.selected_page = page_name
    #                 st.rerun()  # Rerun to update the page content

    def create_glassmorphic_container(id, app_name="My App"):
        # Helper function to create a glassmorphic container
        plh = st.container()
        html_code = """<div id = 'my_div_outer'></div>"""
        st.markdown(html_code, unsafe_allow_html=True)

        with plh:
            inner_html_code = """<div id = 'my_div_inner_%s'></div>""" % id
            plh.markdown(inner_html_code, unsafe_allow_html=True)

        # Glassmorphism CSS with additional styling for buttons and container
        glassmorphic_style = """
            <style>
                /* Container Styling */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) {
                    position: fixed;
                    top: 5em;
                    left: 50%%;
                    transform: translateX(-50%%);
                    padding: 15px 20px;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.125);
                    overflow: hidden;
                    max-width: 120%%;
                    margin: 0 auto;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1000;
                }
                
                /* Navbar Layout */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) 
                div[data-testid='stHorizontalBlock'] {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%%;
                    padding-bottom: 15px;
                }
                
                /* App Name Label Styling */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) 
                .app-name-label {
                    font-size: 1.5rem;
                    font-weight: 800;
                    margin-right: 20px;
                    margin-left: 50px;
                    margin-bottom: 50px;
                    display: flex;
                    align-items: center;
                    color: inherit;
                    opacity: 0.8;
                }
                
                /* Columns Styling to Push Buttons Right */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) 
                div[data-testid='stHorizontalBlock'] > div:first-child {
                    flex-grow: 1;
                }
                
                /* Button Styling */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) 
                div[data-testid='stHorizontalBlock'] button {
                    padding: 5px 10px !important;
                    margin: 0 5px;
                    font-size: 0.8rem;
                    background-color: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: inherit;
                    transition: all 0.3s ease;
                    white-space: nowrap;
                }
                
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer)) 
                div[data-testid='stHorizontalBlock'] button:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    transform: scale(1.05);
                }
                
                /* Optional: Add a subtle gradient overlay for more depth */
                div[data-testid='stVerticalBlock']:has(div#my_div_inner_%s):not(:has(div#my_div_outer))::before {
                    content: "";
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(
                        135deg, 
                        rgba(255, 255, 255, 0.1), 
                        rgba(255, 255, 255, 0.05)
                    );
                    z-index: 1;
                    pointer-events: none;
                }
            </style>
            """ % (
            id,
            id,
            id,
            id,
            id,
            id,
            id,
        )

        st.markdown(glassmorphic_style, unsafe_allow_html=True)

        return plh

    def create_navbar(app_name="Transformo Docs"):
        # Create the navbar container with glassmorphism effect
        navbar_container = create_glassmorphic_container("navbar")

        with navbar_container:
            # Create a navbar layout with an extra column for app name
            nav_cols = st.columns([2, 1] + [1] * len(PAGES))

            # Add app name to the first column
            with nav_cols[0]:
                st.markdown(
                    f'<div style="font-size: 1.5rem; font-weight: 800; opacity: 0.8;">{app_name}</div>',
                    unsafe_allow_html=True,
                )

            # Create buttons in the remaining columns
            for i, (page_name, page_func) in enumerate(PAGES.items()):
                with nav_cols[
                    i + 2
                ]:  # Offset by 2 due to app name and initial spacing column
                    # Create a button for each page in the navbar
                    button = st.button(page_name, key=f"nav_{page_name}")
                    if button:
                        st.session_state.selected_page = page_name
                        st.rerun()  # Rerun to update the page content

    # Initialize selected page in session state if not already set
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = list(PAGES.keys())[0]  # Default to first page

    # Create the navbar
    create_navbar()

    # Render the selected page
    PAGES[st.session_state.selected_page]()


def logout_user():
    if "token" in st.session_state:
        del st.session_state["token"]
        st.success("You have been logged out.")


#     # Define pages and their corresponding functions
#     PAGES = {
#         "Home": home_page,
#         "Document Processing": document_processing_page,
#         "Saved Documents": saved_documents_page,
#         "Chat Interface": chat_interface_page,
#         "API Token": api_token_page,
#     }

#     # URLs for external links like GitHub
#     urls = {"GitHub": "https://github.com/gabrieltempass/streamlit-navigation-bar"}

#     # Styles for the navbar to retain the glassmorphism effect
#     styles = {
#         "nav": {
#             "background-color": "rgba(255, 255, 255, 0.1)",  # Semi-transparent for glassmorphism
#             "backdrop-filter": "blur(10px)",  # Glassmorphism effect
#             "border-radius": "15px",
#             "padding": "10px",
#         },
#         "img": {
#             "padding-right": "14px",
#         },
#         "span": {
#             "color": "white",
#             "padding": "14px",
#         },
#         "active": {
#             "background-color": "white",
#             "color": "var(--text-color)",
#             "font-weight": "normal",
#             "padding": "14px",
#         }
#     }

#     # Options for the navbar
#     options = {
#         "show_menu": False,  # Hide the menu
#         "show_sidebar": False,  # Hide the sidebar
#     }

#     # Initialize session state for page selection if not set
#     if "selected_page" not in st.session_state:
#         st.session_state.selected_page = "Home"

#     # Use st_navbar to create the navbar
#     page = st_navbar(
#         list(PAGES.keys()),  # Pass the page names from PAGES
#         logo_path=logo_path,
#         styles=styles,
#         options=options
#     )

#     # Get the corresponding page function based on the selected page
#     go_to = PAGES.get(page)
#     if go_to:
#         go_to()  # Render the selected page

#     # Optional: custom CSS to keep the glassmorphism effect on other elements
#     st.markdown("""
#     <style>
#         [data-testid="stAppViewContainer"] {
#             background-image: linear-gradient(to right top, #232425, #3b5359, #548882, #87be9b, #daf0aa);
#             font-family: Arial, sans-serif;
#             color: white;
#         }
#         .tab-button.selected {
#             background-color: #4CAF50;
#         }
#     </style>
#     """, unsafe_allow_html=True)


import base64


def get_base64_image(image_path):
    """Encodes an image to a Base64 string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def home_page():

    # Encode images as Base64
    image1_base64 = get_base64_image("assets/download.png")
    image2_base64 = get_base64_image("assets/download-2.jpg")

    # Custom CSS
    st.markdown(
        """
    <style>
    .feature-container {
        display: flex;
        align-items: center;
        margin-bottom: 40px;
        padding: 20px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    .feature-text {
        flex: 1;
        padding: 0 20px;
    }
    .feature-image {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .feature-image img {
        max-width: 100%;
        max-height: 500px;
        border-radius: 10px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <style>
    .stApp { scroll-behavior: smooth; }
    .explore-btn {
            text-decoration: none;
            display: inline-block;
            padding: 10px 20px;
            background-color: rgba(255,255,255,0.2);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            font-family: Arial, sans-serif;
        }
        .explore-btn:hover {
            background-color: rgba(255,255,255,0.3);
        }
        
    
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header with two-line text
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: white; text-align: center; opacity: 0.8; margin-bottom: -0.5em; font-size: 100px;'>Welcome to</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='text-align: center; color: white; margin-top: 0;font-size: 170px;'>Transformo Docs</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p style="text-align: center; font-size: 40px; color: white;">Empowering Document Management</p>',
        unsafe_allow_html=True,
    )
    # Explore button with anchor link
    st.markdown(
        """
        <div style='text-align: center; margin-top: 3px; margin-bottom: 55px'>
            <a style = 'text-decoration: none; 'href='#target-section' class='explore-btn'>
                Explore Features
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # # Title
    # st.markdown("<h1 style='text-align: center; color: white;'>Welcome to Transformo Docs</h1>", unsafe_allow_html=True)

    # First Feature Section
    st.markdown(
        f"""
    <div class="feature-container" id='target-section'>
        <div class="feature-text">
            <h3 style="color: white;">Transformo Docs: Revolutionizing Document Management</h3>
            <p style="color: white;">A powerful solution designed to tackle non-machine-readable documents like PDFs and Word files.</p>
            <ul style="color: white;">
                <li> Searchable Documents</li>
                <li> Enhanced Accessibility</li>
                <li> AI Integration Ready</li>
            </ul>
            <p style="color: white;">Transform your unstructured documents into organized, accessible data.</p>
        </div>
        <div class="feature-image">
            <img src="data:image/png;base64,{image1_base64}" alt="Document Management">
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Second Feature Section
    st.markdown(
        f"""
    <div class="feature-container">
        <div class="feature-image">
            <img src="data:image/jpeg;base64,{image2_base64}" alt="Key Features">
        </div>
        <div class="feature-text">
            <h3 style="color: white;"> Comprehensive Features</h3>
            <ul style="color: white;">
                <li> Advanced Document Analytics</li>
                <li> Seamless Conversion Tools</li>
                <li> Compliance and Security</li>
                <li> Productivity Enhancement</li>
            </ul>
            <p style="color: white;">Unlock the full potential of your documents with our cutting-edge features.</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Third Feature Section (Optional)
    st.markdown(
        f"""
    <div class="feature-container">
        <div class="feature-text">
            <h3 style="color: white;">AI-Powered Insights</h3>
            <ul style="color: white;">
                <li> Intelligent Document Processing</li>
                <li> Smart Content Extraction</li>
                <li> Automated Summarization</li>
                <li> Deep Document Analysis</li>
            </ul>
            <p style="color: white;">Leverage artificial intelligence to transform how you interact with documents.</p>
        </div>
        <div class="feature-image">
            <img src="data:image/jpeg;base64,{image2_base64}" alt="AI-Powered Insights">
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Document processing page function
def document_processing_page():

    st.markdown(
        """
    <style>
    .content {
        margin-top: 200px;
        
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='color: white; text-align: center; opacity: 0.8; margin-top: 50px;font-weight:bold; font-size: 5rem;'>Document Upload and Processing</p>",
        unsafe_allow_html=True,
    )

    # Add a bigger heading for the radio buttons
    st.markdown(
        "<h2 style='text-align: left;'>Select Document Type</h2>",
        unsafe_allow_html=True,
    )

    # Create radio buttons with a custom style
    processing_mode = st.radio(
        "", ["Regular Document", "Scanned Document (OCR)"], index=0
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
    st.subheader("Upload Document")
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

        # If a file is already in session state
    if st.session_state.uploaded_file is not None:
        file_name = st.session_state.uploaded_file.name

        # Display the button to preview the file
        if st.button("Preview File"):
            st.write(f"Preview of **{file_name}**:")
            # Full-page expander for preview
            with st.expander(f"Full-Page Preview: {file_name}", expanded=True):
                if file_name.endswith(".txt"):
                    # Display text content for .txt files
                    content = st.session_state.uploaded_file.read().decode("utf-8")
                    st.text_area("Text Content", content, height=700)
                elif file_name.endswith(".xlsx"):
                    # Display table content for .xlsx files
                    try:
                        data = pd.read_excel(st.session_state.uploaded_file)
                        st.dataframe(data, height=700)
                    except Exception as e:
                        st.error(f"Could not display Excel file: {str(e)}")
                elif file_name.endswith(".docx"):
                    # Display text content for .docx files
                    try:
                        doc = Document(st.session_state.uploaded_file)
                        doc_text = "\n".join([p.text for p in doc.paragraphs])
                        st.text_area("Document Content", doc_text, height=700)
                    except Exception as e:
                        st.error(f"Could not display Word document: {str(e)}")
                elif file_name.endswith(".pdf"):
                    # Embed PDF in an iframe
                    try:
                        pdf_bytes = st.session_state.uploaded_file.read()
                        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Could not preview PDF: {str(e)}")
                else:
                    st.warning("Preview not available for this file type.")
    return st.session_state.uploaded_file


# Function to display export options
def display_export_options(result, uploaded_file):
    st.subheader("Export Options")
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

    # with st.expander("View Processed Output"):
    #     st.code(download_content, language=file_extension.lower())
    # Full-page expander for preview and processed output
    with st.expander(f"Preview & Processed Output ", expanded=False):
        # Side-by-side columns for preview and processed content
        col1, col2 = st.columns(2)
        uploaded_file.seek(0)

        with col1:
            st.subheader("Document Preview")
            if uploaded_file.name.endswith("txt"):
                # Display text content for .txt files
                content = uploaded_file.read().decode("utf-8")
                st.text_area("Text Content", content, height=700)
            elif uploaded_file.name.endswith("xlsx"):
                # Display table content for .xlsx files
                try:
                    data = pd.read_excel(uploaded_file)
                    st.dataframe(data, height=700)
                except Exception as e:
                    st.error(f"Could not display Excel file: {str(e)}")
            elif uploaded_file.name.endswith("docx"):
                # Display text content for .docx files
                try:
                    doc = Document(uploaded_file)
                    doc_text = "\n".join([p.text for p in doc.paragraphs])
                    st.text_area("Document Content", doc_text, height=700)
                except Exception as e:
                    st.error(f"Could not display Word document: {str(e)}")
            elif uploaded_file.name.endswith("pdf"):
                # Embed PDF in an iframe
                try:
                    pdf_bytes = uploaded_file.read()
                    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not preview PDF: {str(e)}")
            else:
                st.warning("Preview not available for this file type.")

        with col2:
            st.subheader("Processed Output")
            st.code(download_content, language=file_extension.lower())


# Function to display analytics
def display_analytics(result):
    st.subheader("Document Analytics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("## Basic Metrics")
        st.write(f"**Word Count:** {result['analytics']['word_count']}")
        st.write(f"**Sentence Count:** {result['analytics']['sentence_count']}")
        st.write(
            f"**Average Sentence Length:** {result['analytics']['average_sentence_length']:.2f} words"
        )

        st.markdown("###  Named Entities")
        st.write(f"**Entity Count:** {result['analytics']['entity_count']}")
        st.write("**Most Common Entities:**")
        for entity, count in result["analytics"]["most_common_entities"]:
            st.write(f"- {entity}: {count}")

    with col2:
        st.markdown("### Keywords")
        st.write(f"**Keyword Count:** {result['analytics']['keyword_count']}")

        st.markdown("###  Word Frequency")
        st.write("**Most Common Words:**")
        for word, count in result["analytics"]["most_common_words"]:
            st.write(f"- {word}: {count}")

    with st.expander(" Document Preview"):
        preview_text = (
            result["extracted_text"][:500] + "..."
            if len(result["extracted_text"]) > 500
            else result["extracted_text"]
        )
        st.text_area("First 500 characters", preview_text, height=200)


# Function to display graphs
def display_graphs(result, uploaded_file):
    st.subheader("Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Word Frequency Graph
        word_freq = result["analytics"]["most_common_words"][:10]  # Top 10 words
        fig = px.bar(
            x=[word for word, _ in word_freq],
            y=[count for _, count in word_freq],
            labels={"x": "Word", "y": "Frequency"},
            title="Top 10 Most Frequent Words",
            color=[count for _, count in word_freq],  # Color by frequency
            color_continuous_scale="Blugrn",  # Change to your preferred color scale
        )
        fig.update_layout(
            title_x=0.35,  # Center title
            title_font=dict(size=18),
            margin=dict(
                t=100,  # Top margin
                b=50,  # Bottom margin
                l=50,  # Left margin
                r=50,  # Right margin
            ),
        )
        fig.update_traces(
            hovertemplate="Word: %{x}<br>Frequency: %{y}",
            hoverlabel=dict(bgcolor="black", font_size=12),
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
            color=[count for _, count in entity_freq],  # Color by frequency
            color_continuous_scale="Blugrn",  # Change to your preferred color scale
        )
        fig.update_layout(
            title_x=0.3,  # Center title
            title_font=dict(size=18),
            margin=dict(
                t=100,  # Top margin
                b=50,  # Bottom margin
                l=50,  # Left margin
                r=50,  # Right margin
            ),
        )
        fig.update_traces(
            hovertemplate="Entity: %{x}<br>Frequency: %{y}",
            hoverlabel=dict(bgcolor="black", font_size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Basic Metrics Graph
    metrics = {
        "Word Count": result["analytics"]["word_count"],
        "Sentence Count": result["analytics"]["sentence_count"],
        "Avg Sentence Length": round(result["analytics"]["average_sentence_length"], 2),
    }

    # Assign each metric a numerical value to apply the color gradient
    metric_values = {"Word Count": 0, "Sentence Count": 10, "Avg Sentence Length": 50}

    # Create the figure with color gradient based on the metric
    fig = go.Figure(
        data=[
            go.Bar(
                name=metric,
                x=[metric],
                y=[value],
                marker=dict(
                    color=[
                        metric_values[metric]
                    ],  # Assign a value from the metric_values dictionary
                    colorscale="Blugrn",
                ),
            )
            for metric, value in metrics.items()
        ]
    )

    # Update the layout with title and bar mode
    fig.update_layout(
        title_text="Basic Document Metrics",
        barmode="group",
        title_x=0.5,
        title_font=dict(size=18),
        margin=dict(
            t=100,  # Top margin
            b=50,  # Bottom margin
            l=50,  # Left margin
            r=50,  # Right margin
        ),
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    # File Size Comparison Graph
    original_size, extracted_size = calculate_file_sizes(uploaded_file, result)
    size_diff = original_size - extracted_size
    size_diff_percentage = (size_diff / original_size) * 100

    fig = go.Figure(
        data=[
            go.Bar(
                name="Original Size",
                x=["Document Size"],
                y=[original_size],
                marker=dict(color="rgb(77,162,132)"),
            ),
            go.Bar(
                name="Extracted Size",
                x=["Document Size"],
                y=[extracted_size],
                marker=dict(color="rgb(196,230,195)"),
            ),
        ]
    )
    fig.update_layout(title_text="Document Size Comparison (MB)", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"Size reduction: {size_diff:.2f} MB ({size_diff_percentage:.2f}%)")

    # Keyword Information
    st.subheader("Keyword Information")
    st.write(f"**Total Keywords:** {result['analytics']['keyword_count']}")
    st.write("**Top Keywords:**")
    keyword_data = pd.DataFrame(
        result["analytics"]["most_common_words"], columns=["Keyword", "Count"]
    )
    st.dataframe(keyword_data)


# Function to display database options
def display_database_options(result, filename):
    st.subheader("Database Options")
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
    st.markdown(
        """
        <h1 style='text-align: center; opacity:0.8; margin-top: 50px; font-size: 5rem;'>Saved Documents</h1>
        """,
        unsafe_allow_html=True,
    )

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
import json


def chat_interface_page():
    st.markdown(
        """
        <h1 style='text-align: center; opacity:0.8; margin-top: 50px; font-size: 5rem;'>Chat with Your Document</h1>
        """,
        unsafe_allow_html=True,
    )

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

    # Initialize EnhancedJSONAgent with the selected document's JSON data
    try:
        with open("temp_selected.json", "w", encoding="utf-8") as temp_file:
            temp_file.write(selected_data["data"])

        agent = EnhancedJSONAgent("temp_selected.json")
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return

    user_query = st.text_input("Ask a question about the document:")

    if user_query:
        with st.spinner("Processing your query..."):
            try:
                answer = agent.process_query(user_query)

                if isinstance(answer, pd.DataFrame):
                    st.dataframe(answer)
                elif answer:
                    st.markdown(f"**Transformo Docs:** {answer}")

                st.session_state["chat_history"].append(
                    {"question": user_query, "answer": answer}
                )
            except Exception as e:
                st.warning(f"Error processing query: {e}")

    if st.session_state["chat_history"]:
        st.write("### Chat History")
        for chat in st.session_state["chat_history"]:
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Transformo Docs:** {chat['answer']}")

    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        st.success("Chat history cleared!")


# Function to handle API token generation and management
def api_token_page():
    st.markdown(
        """
        <h1 style='text-align: center; opacity:0.8; margin-top: 50px; font-size: 5rem;'>API Token and Upload</h1>
        """,
        unsafe_allow_html=True,
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
                if st.button(" Copy", key=f"copy_{i}"):
                    pyperclip.copy(token)
                    st.success(f"Token {i+1} copied to clipboard!")
            with cols[2]:
                if st.button(" Delete", key=f"delete_{i}"):
                    st.session_state.tokens.pop(i)
                    st.experimental_rerun()
            with cols[3]:
                if st.button(" Stats", key=f"stats_{i}"):
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
