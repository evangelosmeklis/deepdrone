import streamlit as st
import os
from dotenv import load_dotenv
from drone import drone_chat

# Load environment variables from .env file
load_dotenv()

# Add dark theme CSS right at the beginning
st.markdown(
    """
    <style>
    /* Dark theme for the entire app, applied immediately */
    .stApp, body, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stHeader"] {
        background-color: #000000 !important;
        color: #00ff00 !important;
    }
    
    /* Dark styling for all inputs */
    [data-testid="stTextInput"] > div, .stTextInput > div {
        background-color: #1E1E1E !important;
        color: #00ff00 !important;
        border: 1px solid #00ff00 !important;
    }
    
    [data-testid="stTextInput"] input, .stTextInput input {
        color: #00ff00 !important;
        background-color: #1E1E1E !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page config is set in drone_chat.py at module level

# Remove duplicate page config since it's now in drone_chat.py at module level
# We'll just import the module and call its main function

def show_auth_screen():
    """Display the authentication screen with DeepDrone information"""
    
    # Military-style header
    st.markdown("<h1 class='glow-text' style='text-align: center; color: #00ff00; font-family: \"Courier New\", monospace; margin-top: 0; margin-bottom: 10px;'>DEEPDRONE COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader glow-text' style='text-align: center; margin-bottom: 5px;'>SECURE TACTICAL OPERATIONS INTERFACE</p>", unsafe_allow_html=True)

    # Create a centered container for the auth form
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #00ff00; font-family: \"Courier New\", monospace; text-shadow: 0 0 5px #00ff00;'>SYSTEM AUTHENTICATION REQUIRED</h2>", unsafe_allow_html=True)
    
    # System status information in a more compact layout
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
        <b>PROTOCOL:</b> HF-AUTH-1<br>
        <b>ENCRYPTION:</b> AES-256<br>
        <b>AI MODULE:</b> OFFLINE
        </div>
        """, unsafe_allow_html=True)
    
    # Compact information about DeepDrone
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
    
    # Token input with custom styling
    st.markdown("<h3 style='color: #00ff00; font-family: \"Courier New\", monospace; text-shadow: 0 0 5px #00ff00;'>ENTER HUGGING FACE AUTHENTICATION TOKEN FOR THE LLM TO RUN:</h3>", unsafe_allow_html=True)
    
    # Create a container with dark background for the input
    st.markdown("<div style='background-color: #0A0A0A; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
    api_key = st.text_input("HF Token", type="password", placeholder="Enter Hugging Face API token...", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Submit button with custom styling
    if st.button("AUTHORIZE ACCESS"):
        if api_key:
            os.environ["HF_TOKEN"] = api_key
            st.markdown("<div style='color: #00ff00; background-color: rgba(0, 128, 0, 0.2); padding: 10px; border: 1px solid #00ff00; border-radius: 5px;'>AUTHENTICATION SUCCESSFUL - INITIALIZING SYSTEM</div>", unsafe_allow_html=True)
            st.session_state['authenticated'] = True
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close text-align center div
    st.markdown("</div>", unsafe_allow_html=True)  # Close auth-container div

def main():
    # Add CSS styles
    st.markdown(
        """
        <style>
        /* Dark theme for the entire app */
        .stApp, body, [data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #00ff00 !important;
        }
        
        /* Make sure all containers are dark */
        [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], 
        [data-testid="stForm"], [data-testid="column"], .stBlock, 
        [data-testid="stMarkdownContainer"] {
            background-color: #000000 !important;
        }
        
        /* Dark inputs */
        [data-testid="stTextInput"] > div {
            background-color: #1E1E1E !important;
            color: #00ff00 !important;
            border: 1px solid #00ff00 !important;
        }
        
        [data-testid="stTextInput"] input {
            color: #00ff00 !important;
            background-color: #1E1E1E !important;
        }
        
        /* Dark buttons */
        .stButton > button {
            background-color: #0A0A0A !important;
            color: #00ff00 !important;
            border: 1px solid #00ff00 !important;
            border-radius: 2px !important;
            font-family: "Courier New", monospace !important;
        }
        
        .stButton > button:hover {
            background-color: #00ff00 !important;
            color: #000000 !important;
        }
        
        /* Success message styling */
        .element-container [data-testid="stAlert"] {
            background-color: rgba(0, 128, 0, 0.2) !important;
            color: #00ff00 !important;
            border: 1px solid #00ff00 !important;
        }
        
        /* Header styling */
        h1, h2, h3, h4, h5, h6, p, span, div, label {
            color: #00ff00 !important;
        }
        
        /* Centered container for HF token */
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
        
        /* Hide Streamlit's default footer */
        footer, header {
            visibility: hidden !important;
            display: none !important;
        }
        
        /* Remove white background from all components */
        .block-container, .main {
            background-color: #000000 !important;
        }
        
        /* Add a slight glow effect to green text */
        .glow-text {
            text-shadow: 0 0 5px #00ff00 !important;
        }
        
        /* Custom select styling */
        [data-testid="stSelectbox"] {
            background-color: #1E1E1E !important;
            color: #00ff00 !important;
            border: 1px solid #00ff00 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Check if user is authenticated
    if not os.environ.get("HF_TOKEN") and not st.session_state.get('authenticated', False):
        show_auth_screen()
        return
    
    # Run the drone chat application
    drone_chat.main()

if __name__ == "__main__":
    main() 