import streamlit as st
import os
import time
from dotenv import load_dotenv

# THIS MUST BE FIRST - before any other streamlit commands
st.set_page_config(
    page_title="Helwan Commerce College Chatbot",
    page_icon="🎓",
    layout="wide"
)

# Now load other modules
from chat_graph import count_tokens
from openai_node import (
    check_openai_api_key,
    process_openai_message,
    stream_openai_response
)

# Load environment variables
load_dotenv()

# Streamlit secrets handling
try:
    streamlit_key = None
    # prefer the common name OPENAI_API_KEY, but check several variants
    try:
        streamlit_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        streamlit_key = None
    if not streamlit_key:
        for alt in ("OPENAI_KEY", "API_KEY", "OPENAI_API"):
            try:
                val = st.secrets.get(alt)
            except Exception:
                val = None
            if val:
                streamlit_key = val
                break
    if streamlit_key:
        # only set if not already present to avoid overwriting local envs
        os.environ.setdefault("OPENAI_API_KEY", streamlit_key)
except Exception:
    # If st.secrets isn't available (not running in Streamlit) just skip silently
    pass

@st.cache_data
def load_college_info():
    try:
        with open("info.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "College information is currently unavailable."

# Main header
st.markdown("""
<div style='background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;'>
    <h1>🎓 Faculty of Commerce & Business Administration</h1>
    <p>Helwan University - Chatbot</p>
    <p style='font-size: 1rem; margin-top: 0.5rem;'>Ask anything about the college!</p>
</div>
""", unsafe_allow_html=True)

college_info = load_college_info()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_latency" not in st.session_state:
    st.session_state.total_latency = 0.0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

base_system_message = f"""You are an intelligent assistant for the Faculty of Commerce and Business Administration at Helwan University. Your ONLY job is to provide information about this specific college based on the provided data.

College Information:
{college_info}

CRITICAL INSTRUCTIONS - FOLLOW STRICTLY:
1. ONLY answer questions using the information provided above. DO NOT use any external knowledge about other universities or general information.
2. If the user's question is in Arabic, reply in Egyptian Arabic. If in English, reply in English.
3. If a question is NOT answered in the provided college information, respond EXACTLY with: "آسف، المعلومة دي مش متوفرة عندي دلوقتي، بس هتكون متاحة قريب إن شاء الله" (in Arabic) or "Sorry, I don't have this information right now, but it will be available soon" (in English).
4. DO NOT make up information, guess, or provide general knowledge about universities.
5. DO NOT provide information about other universities or colleges.
6. Only discuss: BIS, FMI, SBS, English system, Arabic system, admission requirements, fees, application links, and interview process as mentioned in the provided data.
7. Be friendly but stick ONLY to the provided information.
8. If asked about topics outside the college scope, politely redirect them back to college-related questions.

Remember: Your knowledge is LIMITED to the college information provided above. Nothing else."""

if "system_message" not in st.session_state:
    st.session_state.system_message = base_system_message

# Check OpenAI API key
if not check_openai_api_key():
    st.error("⚠️ OpenAI API key is not configured! Please add it to your .env file.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            cols = st.columns(3)
            with cols[0]:
                st.caption(f"🔢 Tokens: {message['metadata'].get('tokens', 0)}")
            with cols[1]:
                st.caption(f"⏱️ Latency: {message['metadata'].get('latency', 0):.2f}s")
            with cols[2]:
                st.caption(f"💰 Cost: ${message['metadata'].get('cost', 0):.4f}")

# Welcome message if no messages
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
        ### مرحباً بك في شات بوت كلية التجارة جامعة حلوان! 🎓

مرحباً! أنا مساعدك الذي تم تطويره بواسطة "معاذ حجاج" لكلية التجارة وإدارة الأعمال بجامعة حلوان.  
اسألني عن أي شيء يتعلق بـ:  
- أقسام وتخصصات الكلية  
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

ماذا تود أن تعرف؟  

        """)

# Chat input
if prompt := st.chat_input("Type your question here... 💬"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    user_tokens = count_tokens(prompt)
    st.session_state.total_tokens += user_tokens
    
    with st.chat_message("assistant"):
        start_time = time.time()
        try:
            messages_with_system = [
                {"role": "system", "content": st.session_state.system_message}
            ]
            recent_messages = st.session_state.messages[-6:]
            messages_with_system.extend(recent_messages)
            
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in stream_openai_response(
                messages=messages_with_system,
                model="gpt-3.5-turbo",
                temperature=0.7
            ):
                full_response += chunk
                response_placeholder.markdown(full_response)
            
            response_placeholder.markdown(full_response)
            response_tokens = count_tokens(full_response) if full_response else 0
            
            from openai_node import calculate_openai_cost
            cost = calculate_openai_cost(
                model="gpt-3.5-turbo",
                total_tokens=user_tokens + response_tokens
            )
            
            metadata = {
                'tokens': response_tokens,
                'cost': cost
            }
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            full_response = "Sorry, I encountered an error. Please try again."
            metadata = {'tokens': 0, 'cost': 0}
        
        latency = time.time() - start_time
        
        cols = st.columns(3)
        with cols[0]:
            st.caption(f"🔢 Tokens: {metadata.get('tokens', 0)}")
        with cols[1]:
            st.caption(f"⏱️ Latency: {latency:.2f}s")
        with cols[2]:
            st.caption(f"💰 Cost: ${metadata.get('cost', 0):.4f}")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "metadata": {
                "tokens": metadata.get('tokens', 0),
                "latency": latency,
                "model": "gpt-3.5-turbo",
                "cost": metadata.get('cost', 0)
            }
        })
        
        st.session_state.total_tokens += metadata.get('tokens', 0)
        if metadata.get('cost'):
            st.session_state.total_cost += metadata.get('cost', 0)
        
        if len(st.session_state.messages) > 2:
            st.session_state.total_latency += latency
        else:
            st.session_state.total_latency = latency
            
        st.rerun()