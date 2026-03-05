import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class RAGPipeline:
    def __init__(self):
        # Using a default embedding and LLM. 
        # In actual deployment, api keys are needed in environment variables (OPENAI_API_KEY)
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")
        self.vectorstore = None
        self.retriever = None

    def ingest_data(self, structured_data):
        """Processes structured doc (from data_engineering) and builds a vector store."""
        
        # We split the long document text into chunks
        text = structured_data.get("content", "")
        if not text:
            return False

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.create_documents([text])

        # Create localized Chroma vector store
        self.vectorstore = Chroma.from_documents(chunks, self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        return True

    def _hyde_generation(self, query):
        """Hypothetical Document Embeddings for Query Decomposition."""
        hyde_prompt = PromptTemplate.from_template(
            "Please write a hypothetical passage that would answer the following question. "
            "Question: {query}\n"
            "Passage:"
        )
        
        hyde_chain = hyde_prompt | self.llm | StrOutputParser()
        hypothetical_document = hyde_chain.invoke({"query": query})
        return hypothetical_document

    def query_document(self, query):
        """Executes Advanced RAG with HyDE."""
        if not self.retriever:
            return "No document ingested. Please upload a document first."

        # Generate HyDE passage
        hypothetical_doc = self._hyde_generation(query)
        
        # Retrieve context based on the hypothetical document
        docs = self.retriever.get_relevant_documents(hypothetical_doc)
        context = "\n".join([doc.page_content for doc in docs])

        # Final QA Chain
        qa_prompt = PromptTemplate.from_template(
            "Answer the question based strictly on the provided context.\n"
            "Context: {context}\n"
            "Question: {question}\n"
            "Answer:"
        )

        qa_chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | qa_prompt
            | self.llm
            | StrOutputParser()
        )

        answer = qa_chain.invoke(query)
        return answer
