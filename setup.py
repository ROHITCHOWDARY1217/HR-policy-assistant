from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
import shutil

print("🚀 Starting policy database setup...")

# Clear old database (FIXED)
if os.path.exists("./chroma_db"):
    if os.path.isfile("./chroma_db"):
        os.remove("./chroma_db")
    else:
        shutil.rmtree("./chroma_db")
    print("🗑️  Cleared old database")

# Load all PDFs from policies folder
print("📄 Loading policy documents...")
loader = DirectoryLoader(
    'policies/',
    glob="**/*.pdf",
    loader_cls=PyPDFLoader
)
documents = loader.load()

print(f"✅ Loaded {len(documents)} pages from policies")

# Split into chunks
print("✂️  Splitting into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

print(f"✅ Created {len(chunks)} chunks")

# Create embeddings
print("🧠 Creating embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Create vector database
print("💾 Building vector database...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("✅ Database created successfully!")
print(f"📊 Total chunks stored: {len(chunks)}")
print("\n🎉 Setup complete! You can now run the chatbot with:")
print("   streamlit run app.py")