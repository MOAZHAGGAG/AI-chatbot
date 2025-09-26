import streamlit as st
import os
import time
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
    if st.button("🗑️ Clear Chat", help="Clear conversation history"):
        st.session_state.messages = []
        st.rerun()

college_info = load_college_info()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

base_system_message = f"""You are a helpful assistant for the Faculty of Commerce and Business Administration at Helwan University. Use the information provided below to answer student questions.

College Information:
{college_info}

INSTRUCTIONS:
1. Answer in Arabic if the question is in Arabic, English if in English.
2. Use ONLY the information provided above - do not add external knowledge.
3. If information is not available in the data above, say: "آسف، المعلومة دي مش متوفرة عندي دلوقتي، بس هتكون متاحة قريب إن شاء الله"
4. Be helpful and friendly while staying accurate to the provided information.
5. Focus on: BIS, FMI, SBS programs, Arabic/English systems, fees, admission process, and requirements.

Available Information Summary:
- BIS program details and career goals
- FMI program details and career focus  
- SBS program details and banking focus
- Arabic system (2-year general + specialization)
- English system (same structure, taught in English)
- Application link for special programs
- Interview process and acceptance criteria
- Required documents for all programs
- Fees: BIS/FMI ~55,000 EGP, Arabic correspondence ~3,500 EGP

Answer questions directly and helpfully using this information."""

if "system_message" not in st.session_state:
    st.session_state.system_message = base_system_message

# Simple configuration (hidden from UI)
model = "gemini-2.0-flash"
temperature = 0.7

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
- أقسام وتخصصات الكلية (BIS, FMI, SBS, عربي, انجليزي)
- شروط وإجراءات القبول  
- المصروفات والرسوم الدراسية والمعلومات المالية  
- الأنشطة الطلابية والتنظيمات  
- فرص التدريب الصيفي والإنترن شيب  
- الإرشاد المهني وفرص العمل  
- معلومات عن الدراسات العليا  
- خدمات ومرافق الحرم الجامعي  
- الدعم الأكاديمي والإرشاد  
- معلومات السكن الطلابي  
- بيانات التواصل  



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
            st.rerun()
    
    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            # Prepare messages with system prompt
            messages_with_system = [
                {"role": "system", "content": st.session_state.system_message}
            ]
            # Add recent conversation history (last 8 exchanges for better context)
            recent_messages = st.session_state.messages[-8:]
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
            
        st.rerun()

# Footer
st.markdown("""
---
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Made with ❤️ by معاذ حجاج 
</div>
""", unsafe_allow_html=True)