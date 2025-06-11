import streamlit as st
import os
from dotenv import load_dotenv
from drone import drone_chat

# Load environment variables from .env file
load_dotenv()

def show_auth_screen():
    """Display the authentication screen with DeepDrone information"""
    
    st.markdown("<h1 class='glow-text' style='text-align: center; color: #00ff00; font-family: \"Courier New\", monospace; margin-top: 0; margin-bottom: 10px;'>DEEPDRONE COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader glow-text' style='text-align: center; margin-bottom: 5px;'>SECURE TACTICAL OPERATIONS INTERFACE</p>", unsafe_allow_html=True)

    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #00ff00; font-family: \"Courier New\", monospace; text-shadow: 0 0 5px #00ff00;'>SYSTEM AUTHENTICATION REQUIRED</h2>", unsafe_allow_html=True)
    
    cols = st.columns(2)
    with cols[0]:
        st.markdown("""
        <div style='font-family: "Courier New", monospace; color: #00dd00;'>
        <b>SYSTEM STATUS:</b> STANDBY<br>
        <b>DATABASE:</b> CONNECTED<br>
        <b>SECURITY:</b> ENABLED
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style='font-family: "Courier New", monospace; color: #00dd00;'>
        <b>PROTOCOL:</b> DS-AUTH-1<br>
        <b>ENCRYPTION:</b> AES-256<br>
        <b>AI MODULE:</b> OFFLINE
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='font-family: "Courier New", monospace; color: #00ff00; text-align: left; margin: 15px 0;'>
    <p><b>DEEPDRONE</b> is an advanced command and control system for drone operations:</p>
    
    <ul style='color: #00ff00; margin: 8px 0; padding-left: 20px;'>
        <li>Real-time <b>flight data analysis</b> and visualization</li>
        <li>Comprehensive <b>sensor monitoring</b> with anomaly detection</li>
        <li>AI-powered <b>mission planning</b> and execution</li>
        <li>Predictive <b>maintenance scheduling</b> and diagnostics</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid #00ff00; margin: 10px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='color: #00ff00; font-family: \"Courier New\", monospace; text-shadow: 0 0 5px #00ff00;'>ENTER DEEPSEEK AUTHENTICATION TOKEN FOR THE LLM TO RUN:</h3>", unsafe_allow_html=True)
    
    st.markdown("<div style='background-color: #0A0A0A; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
    api_key = st.text_input("DeepSeek Token", type="password", placeholder="Enter DeepSeek API token...", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("AUTHORIZE ACCESS"):
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
            st.markdown("<div style='color: #00ff00; background-color: rgba(0, 128, 0, 0.2); padding: 10px; border: 1px solid #00ff00; border-radius: 5px;'>AUTHENTICATION SUCCESSFUL - INITIALIZING SYSTEM</div>", unsafe_allow_html=True)
            st.session_state['authenticated'] = True
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.markdown(
        """
        <style>
        .stApp, body, [data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #00ff00 !important;
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
            border: 1px solid #00ff00;
            border-radius: 10px;
            background-color: #0A0A0A !important;
            overflow-y: auto;
        }
        footer, header {
            visibility: hidden !important;
            display: none !important;
        }
        .glow-text {
            text-shadow: 0 0 5px #00ff00 !important;
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