from dotenv import load_dotenv
import os

from langchain_community.document_loaders import TextLoader,PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
CHROMA_DIR = "chroma_store"
load_dotenv()
print(os.getenv("GROQ_API_KEY"))

def ingest_document(file_path: str, doc_id: int):
    """Load, chunk, embed and store a document."""
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding='utf-8')

    docs = loader.load()

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_documents(docs)
    print(f"✅ Created {len(chunks)} chunks")
    for chunk in chunks:
            chunk.metadata['doc_id'] = str(doc_id)
    
  
            print(chunk.page_content)
# 3. Embed locally (free, no API key needed)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    Chroma.from_documents (
         chunks, 
         embeddings,
         persist_directory=CHROMA_DIR,
        collection_name=f"doc_{doc_id}"
    )
    print("✅ Stored in ChromaDB")

def ask_question(question: str, doc_id: int) -> str:
    """Retrieve relevant chunks and answer the question."""
    embeddings = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=f"doc_{doc_id}"
    )









# 4. Retriever + Groq LLM (free)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile"
    )

# 5. Chain
    prompt = ChatPromptTemplate.from_template("""
    Answer the question using only the context below.
    If the answer is not in the context, say "I don't know."

    Context: {context}

    Question: {question}
    """)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain.invoke(question)
    # 6. Ask a question

# Is the document structured with clear sections?
#   YES → RecursiveCharacterTextSplitter, chunk_size=500-1000
  
# Is it conversational / narrative text?
#   YES → SemanticChunker
  
# Do answers require full paragraph context?  
#   YES → ParentDocumentRetriever
  
# Is speed critical and docs are short?
#   YES → Fixed-size, chunk_size=200-400


# from langchain_experimental.text_splitter import SemanticChunker
# from langchain_community.embeddings import SentenceTransformerEmbeddings

# embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
# chunks = splitter.split_documents(docs)

# from langchain.retrievers import ParentDocumentRetriever
# from langchain.storage import InMemoryStore
# from langchain_community.vectorstores import Chroma
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
# child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

# store = InMemoryStore()
# vectorstore = Chroma(embedding_function=embeddings)

# retriever = ParentDocumentRetriever(
#     vectorstore=vectorstore,
#     docstore=store,
#     child_splitter=child_splitter,
#     parent_splitter=parent_splitter,
# )





























