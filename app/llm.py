import streamlit as st
import json
import pandas as pd
import torch
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer


class EnhancedJSONAgent:
    def __init__(self, json_file_path):
        """
        Initialize the Enhanced JSON Agent with LLM support

        :param json_file_path: Path to the JSON file
        """
        # Load JSON data
        with open(json_file_path, "r", encoding="utf-8") as file:
            self.raw_data = json.load(file)

        # Prepare context for LLM
        self.context = self._prepare_context()

        # Initialize LLM Question Answering Pipeline
        try:
            # Use a robust open-source QA model
            model_name = "distilbert-base-uncased-distilled-squad"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForQuestionAnswering.from_pretrained(model_name)

            self.qa_pipeline = pipeline(
                "question-answering", model=model, tokenizer=self.tokenizer
            )
        except Exception as e:
            st.error(f"Error loading LLM model: {e}")
            self.qa_pipeline = None

    def _prepare_context(self):
        """
        Prepare a comprehensive text context from JSON data

        :return: Flattened text representation of the data
        """

        def flatten_json(data, parent_key="", sep=" > "):
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, (dict, list)):
                        items.extend(flatten_json(v, new_key, sep))
                    else:
                        items.append(f"{new_key}: {v}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    if isinstance(item, (dict, list)):
                        items.extend(flatten_json(item, new_key, sep))
                    else:
                        items.append(f"{new_key}: {item}")
            return items

        # Create context string
        context_items = flatten_json(self.raw_data)
        return " ".join(context_items)

    def process_query(self, query):
        """
        Process user query using multiple approaches

        :param query: User's natural language query
        :return: Processed query results
        """
        # Prioritize "words" and "sentences" fields
        prioritized_context = self._prepare_prioritized_context(query)

        # If LLM is available, use question-answering
        if self.qa_pipeline:
            try:
                # Use LLM for initial processing
                llm_response = self.qa_pipeline(
                    {"question": query, "context": prioritized_context}
                )

                st.write("### Answer:")

                return llm_response["answer"]
            except Exception as e:
                st.warning(f"LLM processing error: {e}")

        # Fallback to traditional extraction methods
        return self._traditional_extraction(query)

    def _prepare_prioritized_context(self, query):
        """
        Prepare a prioritized context based on the query

        :param query: User's natural language query
        :return: Prioritized context string
        """

        def flatten_json(data, parent_key="", sep=" > "):
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, (dict, list)):
                        items.extend(flatten_json(v, new_key, sep))
                    else:
                        items.append(f"{new_key}: {v}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    if isinstance(item, (dict, list)):
                        items.extend(flatten_json(item, new_key, sep))
                    else:
                        items.append(f"{new_key}: {item}")
            return items

        # Flatten JSON data
        context_items = flatten_json(self.raw_data)

        # Prioritize "words" and "sentences" fields
        prioritized_items = [
            item for item in context_items if "words" in item or "sentences" in item
        ]

        # Add other fields if specified in the query
        if any(field in query.lower() for field in ["words", "sentences"]):
            return " ".join(prioritized_items)
        else:
            return " ".join(context_items)

    def _traditional_extraction(self, query):
        """
        Traditional data extraction methods

        :param query: User query
        :return: Extracted data
        """
        # Lowercase query for easier matching
        normalized_query = query.lower()

        # Extraction strategies
        extraction_strategies = [
            (r"(give me|show|list).*?(name|names)", self._extract_names),
            (r"(contact|phone|email|telephone)", self._extract_contacts),
            (r"(all|every).*?(\w+)", self._extract_specific_field),
            (r"(find|filter|where|containing)", self._filter_data),
        ]

        # Try each strategy
        for pattern, extraction_method in extraction_strategies:
            if any(pattern in normalized_query for pattern in pattern):
                return extraction_method(query)

        # Fallback to general exploration
        return self._explore_data()

    # Include the traditional extraction methods from the previous implementation
    # (Methods like _extract_names, _extract_contacts, etc. remain the same)

    def _extract_names(self, query):
        """
        Extract names from the JSON data

        :param query: User query
        :return: Extracted names
        """

        def find_names(data):
            names = []
            if isinstance(data, dict):
                for key, value in data.items():
                    if any(
                        name_key in key.lower()
                        for name_key in ["name", "nome", "full_name", "fullname"]
                    ):
                        names.append(str(value))
                    if isinstance(value, (dict, list)):
                        names.extend(find_names(value))
            elif isinstance(data, list):
                for item in data:
                    names.extend(find_names(item))
            return names

        found_names = find_names(self.raw_data)

        if found_names:
            st.write("### Extracted Names:")
            return pd.DataFrame(found_names, columns=["Names"])
        return "No names found."

    def _extract_contacts(self, query):
        """
        Extract contact information from the JSON data

        :param query: User query
        :return: Extracted contacts
        """

        def find_contacts(data):
            contacts = []
            if isinstance(data, dict):
                for key, value in data.items():
                    if any(
                        contact_key in key.lower()
                        for contact_key in ["contact", "phone", "email", "telephone"]
                    ):
                        contacts.append(str(value))
                    if isinstance(value, (dict, list)):
                        contacts.extend(find_contacts(value))
            elif isinstance(data, list):
                for item in data:
                    contacts.extend(find_contacts(item))
            return contacts

        found_contacts = find_contacts(self.raw_data)

        if found_contacts:
            st.write("### Extracted Contacts:")
            return pd.DataFrame(found_contacts, columns=["Contacts"])
        return "No contacts found."

    def _extract_specific_field(self, query):
        """
        Extract specific field from the JSON data

        :param query: User query
        :return: Extracted field data
        """
        field_name = query.split()[-1].lower()

        def find_field(data, field_name):
            fields = []
            if isinstance(data, dict):
                for key, value in data.items():
                    if field_name in key.lower():
                        fields.append(str(value))
                    if isinstance(value, (dict, list)):
                        fields.extend(find_field(value, field_name))
            elif isinstance(data, list):
                for item in data:
                    fields.extend(find_field(item, field_name))
            return fields

        found_fields = find_field(self.raw_data, field_name)

        if found_fields:
            st.write(f"### Extracted {field_name.capitalize()}:")
            return pd.DataFrame(found_fields, columns=[field_name.capitalize()])
        return f"No {field_name} found."

    def _filter_data(self, query):
        """
        Filter data based on query

        :param query: User query
        :return: Filtered data
        """

        def filter_json(data, query):
            filtered_data = []
            if isinstance(data, dict):
                for key, value in data.items():
                    if (
                        query.lower() in key.lower()
                        or query.lower() in str(value).lower()
                    ):
                        filtered_data.append({key: value})
                    if isinstance(value, (dict, list)):
                        filtered_data.extend(filter_json(value, query))
            elif isinstance(data, list):
                for item in data:
                    filtered_data.extend(filter_json(item, query))
            return filtered_data

        filtered_results = filter_json(self.raw_data, query)

        if filtered_results:
            st.write("### Filtered Data:")
            return pd.DataFrame(filtered_results)
        return "No matching data found."

    def _explore_data(self):
        """
        General exploration of the JSON data

        :return: Explored data
        """

        def explore_json(data, parent_key="", sep=" > "):
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, (dict, list)):
                        items.extend(explore_json(v, new_key, sep))
                    else:
                        items.append(f"{new_key}: {v}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    if isinstance(item, (dict, list)):
                        items.extend(explore_json(item, new_key, sep))
                    else:
                        items.append(f"{new_key}: {item}")
            return items

        explored_items = explore_json(self.raw_data)

        if explored_items:
            st.write("### General Exploration:")
            return pd.DataFrame(explored_items, columns=["Explored Data"])
        return "No data to explore."


def main():
    st.title("LLM-Enhanced JSON Data Extraction Agent")

    # File uploader for JSON
    uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with open("temp_upload.json", "wb") as f:
            f.write(uploaded_file.getvalue())

        # Initialize agent
        try:
            agent = EnhancedJSONAgent("temp_upload.json")

            # Query input
            user_query = st.text_input("Enter your query about the data:")

            if user_query:
                with st.spinner("Processing your query..."):
                    # Process query and display results
                    result = agent.process_query(user_query)

                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result)
                    elif result:
                        st.write(result)

        except Exception as e:
            st.error(f"Error processing the JSON file: {e}")


if __name__ == "__main__":
    main()
