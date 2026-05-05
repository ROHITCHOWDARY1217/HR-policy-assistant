import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="👔",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .popular-q {
        background: #f0f2f6;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        cursor: pointer;
        border-left: 4px solid #1f77b4;
    }
    .popular-q:hover {
        background: #e0e2e6;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chain" not in st.session_state:
    st.session_state.chain = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Initialize chatbot (load once)
if not st.session_state.initialized:
    with st.spinner("🔄 Loading company policies..."):
        try:
            # Load embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
            
            # Load vector database
            vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=embeddings
            )
            
            # Create LLM
            llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model="llama-3.1-8b-instant",
                temperature=0.7  # ✅ Increased for natural conversation
            )

            # Create memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
                max_token_limit=2000
            )

            # ✅ Custom prompt that allows conversation
            from langchain.prompts import PromptTemplate

            custom_prompt = PromptTemplate(
                template="""You are a friendly HR Policy Assistant.
                You help employees with company policy questions.

                You have two modes:
                1. If question is about HR policies/company:
                Answer ONLY from the context provided below
                Always cite which policy/page you got answer from

                2. If question is general conversation
                (greetings, thanks, how are you, etc.):
                Respond naturally and friendly
                Then gently remind you can help with HR policies

                Context from policies:
                {context}

                Previous conversation:
                {chat_history}

                Employee question: {question}

                Your response:""",
                    input_variables=["context", "chat_history", "question"]
                )

            # Create chain with custom prompt
            st.session_state.chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(
                    search_kwargs={"k": 3}
                ),
                memory=memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": custom_prompt}
            )
            
            st.session_state.initialized = True
            
        except Exception as e:
            st.error(f"""
            ❌ **Error loading policies!**
            
            Have you run setup.py first?
            
            Run this command once:
            ```
            python3 setup.py
            ```
            
            Error details: {str(e)}
            """)
            st.stop()

# Header
st.markdown('<h1 class="main-header">👔 HR Policy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask me anything about company policies!</p>', unsafe_allow_html=True)

# Sidebar with popular questions
with st.sidebar:
    st.header("💡 Popular Questions")
    
    popular_questions = [
        "How many annual leaves do I get?",
        "What is the work from home policy?",
        "How do I apply for sick leave?",
        "What is the notice period?",
        "Am I eligible for health insurance?",
        "What are the office timings?",
        "How does the appraisal process work?",
        "Can I carry forward unused leaves?"
    ]
    
    st.markdown("**Click to ask:**")
    
    for q in popular_questions:
        if st.button(q, key=q, use_container_width=True):
            st.session_state.selected_question = q
    
    st.divider()
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    st.caption("💼 Powered by AI")

# Display chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant", avatar="👔"):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📑 Policy Reference"):
                    for source in message["sources"]:
                        st.caption(f"**{source['file']}** - Page {source['page']}")
                        st.text(source['content'][:150] + "...")

# Chat input
user_question = st.chat_input("Ask about leave policy, benefits, WFH, etc...")

# Handle selected question from sidebar
if "selected_question" in st.session_state and st.session_state.selected_question:
    user_question = st.session_state.selected_question
    st.session_state.selected_question = None

if user_question:
    # Display user message
    with st.chat_message("user"):
        st.write(user_question)
    
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })
    
    # Get AI response
    with st.chat_message("assistant", avatar="👔"):
        with st.spinner("🔍 Checking policies..."):
            response = st.session_state.chain({
                "question": user_question
            })
            
            answer = response.get("answer", "I couldn't find information about that in our policies.")
            st.write(answer)
            
            # Show sources
            sources = response.get("source_documents", [])
            source_info = []
            
            if sources:
                with st.expander("📑 Policy Reference"):
                    for doc in sources:
                        page = doc.metadata.get('page', 0)
                        file = doc.metadata.get('source', 'Unknown')
                        
                        # Extract filename
                        filename = os.path.basename(file)
                        
                        st.caption(f"**{filename}** - Page {page + 1}")
                        st.text(doc.page_content[:150] + "...")
                        
                        source_info.append({
                            'file': filename,
                            'page': page + 1,
                            'content': doc.page_content
                        })
    
    # Add to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "sources": source_info
    })
    
    st.rerun()

# Welcome message if no chat yet
if not st.session_state.chat_history:
    st.info("""
    👋 **Welcome!** I'm your HR Policy Assistant.
    
    I can help you with:
    - Leave policies
    - Work from home guidelines
    - Benefits information
    - Company procedures
    - And more!
    
    Just ask me anything or click a question from the sidebar.
    """)