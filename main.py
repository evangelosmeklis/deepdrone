import streamlit as st
import os
from dotenv import load_dotenv
from drone import drone_chat

# Load environment variables from .env file
load_dotenv()

def show_auth_screen():
    """Display the authentication screen with DeepDrone information"""
    
    st.markdown("<h1 class='futuristic-text' style='text-align: center; color: #00ffff; font-family: \"Orbitron\", sans-serif; margin-top: 0; margin-bottom: 10px;'>DEEPDRONE COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader futuristic-text' style='text-align: center; margin-bottom: 5px;'>ADVANCED AI-POWERED DRONE OPERATIONS</p>", unsafe_allow_html=True)

    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #00ffff; font-family: \"Orbitron\", sans-serif; text-shadow: 0 0 10px #00ffff;'>SYSTEM INITIALIZATION</h2>", unsafe_allow_html=True)
    
    cols = st.columns(2)
    with cols[0]:
        st.markdown("""
        <div style='font-family: "Orbitron", sans-serif; color: #00ffff;'>
        <b>SYSTEM STATUS:</b> STANDBY<br>
        <b>DATABASE:</b> CONNECTED<br>
        <b>SECURITY:</b> ENABLED
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style='font-family: "Orbitron", sans-serif; color: #00ffff;'>
        <b>PROTOCOL:</b> DS-AUTH-1<br>
        <b>ENCRYPTION:</b> AES-256<br>
        <b>AI MODULE:</b> OFFLINE
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='font-family: "Orbitron", sans-serif; color: #00ffff; text-align: left; margin: 15px 0;'>
    <p><b>DEEPDRONE</b> is an advanced AI-powered drone operations system:</p>
    
    <ul style='color: #00ffff; margin: 8px 0; padding-left: 20px;'>
        <li>Real-time <b>flight data analysis</b> and visualization</li>
        <li>Advanced <b>sensor monitoring</b> with AI detection</li>
        <li>Intelligent <b>mission planning</b> and execution</li>
        <li>Predictive <b>maintenance scheduling</b> and diagnostics</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid #00ffff; margin: 10px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='color: #00ffff; font-family: \"Orbitron\", sans-serif; text-shadow: 0 0 10px #00ffff;'>ENTER DEEPSEEK AUTHENTICATION TOKEN:</h3>", unsafe_allow_html=True)
    
    st.markdown("<div style='background-color: rgba(0, 255, 255, 0.1); padding: 10px; border-radius: 5px; border: 1px solid #00ffff;'>", unsafe_allow_html=True)
    api_key = st.text_input("DeepSeek Token", type="password", placeholder="Enter DeepSeek API token...", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("INITIALIZE SYSTEM"):
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
            st.markdown("<div style='color: #00ffff; background-color: rgba(0, 255, 255, 0.1); padding: 10px; border: 1px solid #00ffff; border-radius: 5px;'>SYSTEM INITIALIZED - WELCOME TO DEEPDRONE</div>", unsafe_allow_html=True)
            st.session_state['authenticated'] = True
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def display_message(role, content, avatar_map=None):
    """Display a chat message with custom styling."""
    if avatar_map is None:
        avatar_map = {
            "user": "👤", 
            "assistant": "🚁"
        }
    
    if role == "user":
        # User message styling - right aligned with user avatar
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(
                f"""
                <div style="
                    background-color: rgba(10, 25, 41, 0.9); 
                    border: 1px solid #00ffff;
                    border-radius: 10px; 
                    padding: 12px; 
                    margin-bottom: 8px;
                    text-align: right;
                    max-width: 90%;
                    float: right;
                    color: #FFFFFF;
                    font-family: 'Orbitron', sans-serif;
                    box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
                    backdrop-filter: blur(5px);
                ">
                    {content}
                </div>
                """, 
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(f"<div style='font-size: 24px; text-align: center; color: #00ffff; text-shadow: 0 0 10px #00ffff;'>{avatar_map['user']}</div>", unsafe_allow_html=True)
    else:
        # Assistant message styling - left aligned with drone avatar
        col1, col2 = st.columns([1, 6])
        with col1:
            st.markdown(f"<div style='font-size: 24px; text-align: center; color: #00ffff; text-shadow: 0 0 10px #00ffff;'>{avatar_map['assistant']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(
                f"""
                <div style="
                    background-color: rgba(10, 25, 41, 0.9); 
                    border: 1px solid #00ffff;
                    border-radius: 10px; 
                    padding: 12px; 
                    margin-bottom: 8px;
                    text-align: left;
                    max-width: 90%;
                    color: #00ffff;
                    font-family: 'Orbitron', sans-serif;
                    box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
                    backdrop-filter: blur(5px);
                ">
                    {content}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Add a smaller divider to separate messages
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

def initialize_chat_container():
    """Initialize the chat container with greeting message."""
    if "chat_container" not in st.session_state:
        chat_container = st.container()
        with chat_container:
            # Initialize with greeting message
            display_message(
                "assistant",
                "DEEPDRONE SYSTEM ONLINE. I am your advanced AI-powered drone operations assistant. How can I assist with your mission today? You can request flight data analysis, sensor readings, maintenance recommendations, or mission planning."
            )
            
        st.session_state.chat_container = chat_container

def main():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap');
        
        .stApp, body, [data-testid="stAppViewContainer"] {
            background-color: #0a1929 !important;
            color: #00ffff !important;
        }
        
        .auth-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: auto;
            min-height: 400px;
            max-width: 90vh;
            width: 70%;
            margin: 20px auto;
            padding: 30px;
            border: 1px solid #00ffff;
            border-radius: 10px;
            background-color: rgba(10, 25, 41, 0.9) !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
            overflow-y: auto;
        }
        
        footer, header {
            visibility: hidden !important;
            display: none !important;
        }
        
        .futuristic-text {
            text-shadow: 0 0 10px #00ffff !important;
            font-family: 'Orbitron', sans-serif !important;
        }
        
        /* Modern input styling */
        .stTextInput > div {
            background-color: rgba(10, 25, 41, 0.9) !important;
            color: #00ffff !important;
            border: 1px solid #00ffff !important;
            border-radius: 5px !important;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.2) !important;
        }
        
        .stTextInput input {
            color: #00ffff !important;
            background-color: rgba(10, 25, 41, 0.9) !important;
            font-family: 'Orbitron', sans-serif !important;
        }
        
        .stTextInput input::placeholder {
            color: rgba(0, 255, 255, 0.5) !important;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: rgba(10, 25, 41, 0.9) !important;
            color: #00ffff !important;
            border: 1px solid #00ffff !important;
            border-radius: 5px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: bold !important;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #00ffff !important;
            color: #0a1929 !important;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.4) !important;
        }
        
        /* Chat container styling */
        .chat-container {
            background-color: rgba(10, 25, 41, 0.9) !important;
            border: 1px solid #00ffff !important;
            border-radius: 10px !important;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2) !important;
            backdrop-filter: blur(10px);
        }
        
        /* Message styling */
        .message-container {
            background-color: rgba(10, 25, 41, 0.9) !important;
            border: 1px solid #00ffff !important;
            border-radius: 5px !important;
            margin: 5px 0 !important;
            padding: 10px !important;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.1) !important;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        
        .status-active {
            background-color: #00ffff;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0); }
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(10, 25, 41, 0.9) !important;
            border-right: 1px solid #00ffff !important;
            backdrop-filter: blur(10px);
        }
        
        /* Command bar styling */
        .command-bar-wrapper {
            background-color: rgba(10, 25, 41, 0.9) !important;
            border-top: 1px solid #00ffff !important;
            box-shadow: 0 -5px 20px rgba(0, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Check if user is authenticated via DeepSeek API Key
    if not os.environ.get("DEEPSEEK_API_KEY") and not st.session_state.get('authenticated', False):
        show_auth_screen()
        return
    
    # Run the drone chat application
    drone_chat.main()

if __name__ == "__main__":
    main() 