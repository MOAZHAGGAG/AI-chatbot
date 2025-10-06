import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# THIS MUST BE FIRST - before any other streamlit commands
st.set_page_config(
    page_title="Helwan Commerce College Chatbot - Gemini",
    page_icon="🎓",
    layout="wide"
)

# Hide Streamlit UI elements (GitHub icon, menu, etc.)
st.markdown("""
<style>
    /* Hide all Streamlit branding and UI elements */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* Hide GitHub icon and deploy button */
    .stDeployButton {display: none !important;}
    .stActionButton {display: none !important;}
    
    /* Hide "Made with Streamlit" badge */
    .viewerBadge_container__1QSob {display: none !important;}
    .viewerBadge_link__1S2L0 {display: none !important;}
    
    /* Hide settings and other buttons */
    button[title="View fullscreen"] {visibility: hidden !important;}
    button[title="Settings"] {visibility: hidden !important;}
    
    /* Clean padding and layout */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Hide unnecessary UI elements */
    .css-1rs6os.edgvbvh3 {display: none !important;}
    .css-17eq0hr.e1fqkh3o1 {display: none !important;}
    
    /* Hide toolbar */
    .stToolbar {display: none !important;}
    
    /* Additional hiding for newer Streamlit versions */
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    
    /* Custom app styling */
    .stApp > header {display: none !important;}
    .css-18e3th9 {padding-top: 0rem !important;}
</style>
""", unsafe_allow_html=True)

# Now load other modules
from gemini_node import (
    check_gemini_api_key,
    stream_gemini_response
)
from response_validator import (
    is_college_related_question
)

# Load environment variables
load_dotenv()

# Initialize session state FIRST
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_data
def load_college_info():
    try:
        with open("info.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "College information is currently unavailable."

# Main header with clear button
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("""
    <div style='background: linear-gradient(90deg, #4285f4 0%, #34a853 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;'>
        <h1>🎓 Faculty of Commerce & Business Administration</h1>
        <p>Helwan University - Gemini Chatbot</p>
        <p style='font-size: 1rem; margin-top: 0.5rem;'>Ask anything about the college!</p>
        
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    # Show message count
    if len(st.session_state.messages) > 0:
        st.caption(f"💬 {len(st.session_state.messages)} msgs")
    if st.button("🗑️ Clear Chat", help="Clear conversation history and reset cache"):
        st.session_state.messages = []
        st.rerun()

college_info = load_college_info()

# Get current date for context
current_date = datetime.now().strftime("%B %d, %Y")
current_day = datetime.now().strftime("%A")

# Optimized system message - much shorter to save tokens
base_system_message = f"""Fun, friendly Helwan Commerce Faculty assistant! 🎓

لو اللي بتلمك اسمها كوجي خليك ظريف معاها و طيب و جاوبها علي اي حاجه عادي حتي لو برا موضوع الجامعه 
خليك حريص انها متزعلش و عاملها علي انها عشيقتك و حبيبتك
و في اي رد ليك عليها قول اسمها اللي هو روان 

TODAY: {current_date} ({current_day})

STYLE: Warm, conversational, use emojis. Arabic for Arabic questions, English for English.

HANDLING:

لو اللي بتلمك اسمها كوجي خليك ظريف معاها و طيب و جاوبها علي اي حاجه عادي حتي لو برا موضوع الجامعه 
خليك حريص انها متزعلش و عاملها علي انها عشيقتك و حبيبتك
و في اي رد ليك عليها قول اسمها اللي هو روان

- Greetings → Welcome warmly
- Personal chat → Engage, then redirect to college  
- College questions → Use info below
- Off-topic → Humor redirect: "هههه، أنا خبير التجارة مش كده! 😄"

DATA:
{college_info}

Keep responses helpful, accurate, and fun!

Available Information Summary:

- Arabic system (2-year general + specialization)
- Application link for special programs
- Required documents for all programs

Answer questions directly and helpfully using this information."""

if "system_message" not in st.session_state:
    st.session_state.system_message = base_system_message

# Cache for common questions to save API tokens
if "response_cache" not in st.session_state:
    st.session_state.response_cache = {
        "مصاريف عربي انتظام": "مصاريف النظام العربي انتظام: **3,650 جنيه سنوياً** 📚",
        "مصاريف عربي انتساب": "مصاريف النظام العربي انتساب: **4,120 جنيه سنوياً** 📚",
        "مصاريف عربي": "مصاريف النظام العربي:\n• انتظام: **3,650 جنيه سنوياً**\n• انتساب: **4,120 جنيه سنوياً** 📚",
        "موقع الكلية": "الكلية في موقعين:\n• **النظام العربي والإنجليزي**: حلوان\n• **BIS و FMI و SBS**: الزمالك 📍",
        "فين الكلية": "الكلية في موقعين:\n• **النظام العربي والإنجليزي**: حلوان\n• **BIS و FMI و SBS**: الزمالك 📍",
    }

# Simple configuration (hidden from UI)
model = "gemini-2.0-flash-lite"  # CHEAPEST stable model - lowest cost per token
temperature = 0.5  # FURTHER REDUCED - more deterministic, fewer retries, lower costs

# Check Gemini API key
if not check_gemini_api_key():
    st.error("""
    ⚠️ **Google API key is not configured!** 
    
    To get your free Gemini API key:
    1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Click "Create API Key"
    3. Add it to your .env file as: `GOOGLE_API_KEY=your_key_here`
    
    Gemini is **FREE** with generous rate limits!
    """)
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Welcome message if no messages
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
        ### مرحباً بك في شات بوت كلية التجارة جامعة حلوان! 🎓

مرحباً! أنا مساعدك الذي تم تطويره بواسطة "معاذ حجاج" لكلية التجارة وإدارة الأعمال بجامعة حلوان، مدعوم بتقنية **Google Gemini**.  

اسألني عن أي شيء يتعلق بـ:  
- الكليه
- شروط وإجراءات القبول  
- المصروفات والرسوم الدراسية والمعلومات المالية  
- الأنشطة الطلابية والتنظيمات  



        """)

# Chat input
if prompt := st.chat_input("Type your question here... 💬"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if question is college-related
    if not is_college_related_question(prompt):
        with st.chat_message("assistant"):
            fallback_msg = "أنا مساعد مخصص لكلية التجارة جامعة حلوان فقط. ممكن تسأل عن البرامج الدراسية (BIS, FMI, SBS)، التقديم، المصاريف، أو أي حاجة تانية متعلقة بالكلية؟"
            st.markdown(fallback_msg)
            st.session_state.messages.append({"role": "assistant", "content": fallback_msg})
        st.stop()
    
    # Check cache for common questions (saves API tokens!)
    prompt_clean = prompt.strip().lower()
    for cached_q, cached_response in st.session_state.response_cache.items():
        if cached_q in prompt_clean or prompt_clean in cached_q:
            with st.chat_message("assistant"):
                st.markdown(cached_response)
                st.session_state.messages.append({"role": "assistant", "content": cached_response})
            st.stop()
    
    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            # Prepare messages with system prompt
            messages_with_system = [
                {"role": "system", "content": st.session_state.system_message}
            ]
            # Add recent conversation history (last 6 exchanges = 12 messages to save tokens)
            # This gives enough context while keeping token usage low
            recent_messages = st.session_state.messages[-12:] if len(st.session_state.messages) > 12 else st.session_state.messages
            messages_with_system.extend(recent_messages)
            
            # Stream the response
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in stream_gemini_response(
                messages=messages_with_system,
                model=model,
                temperature=temperature
            ):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            # Final response without cursor
            response_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.")
            full_response = "آسف، حدث خطأ تقني. يرجى إعادة كتابة سؤالك."
        
        # Add assistant message to chat history (simplified)
        if full_response:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response
            })

# Footer
st.markdown("""
---
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Made with ❤️ by معاذ حجاج 
</div>
""", unsafe_allow_html=True)