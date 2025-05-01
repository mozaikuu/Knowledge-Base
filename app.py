import streamlit as st
from chatbot_model import EinsteinChatbot

# Set page config
st.set_page_config(
    page_title="Einstein Knowledge Base Chatbot",
    page_icon="🧠",
    layout="wide"
)

# Initialize chatbot
@st.cache_resource
def load_chatbot():
    return EinsteinChatbot()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Main app
def main():
    st.title("🧠 Einstein Knowledge Base Chatbot")
    st.markdown("""
    This chatbot has been trained on a comprehensive knowledge base about Albert Einstein,
    sourced from Wikidata. Ask any question about Einstein's life, work, or achievements!
    """)
    
    # Sidebar with information
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This chatbot combines:
        - Wikidata knowledge about Albert Einstein
        - Advanced language model for natural conversations
        - Information retrieval system for accurate answers
        """)
    
    # Chat interface
    chatbot = load_chatbot()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about Einstein..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            response = chatbot.generate_response(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 