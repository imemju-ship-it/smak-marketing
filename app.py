import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import pandas as pd
from duckduckgo_search import DDGS  # 👈 محرك البحث المجاني الجديد!

# 1. إعدادات الواجهة
st.set_page_config(page_title="سماك V3 - النسخة المجانية", page_icon="🤖", layout="wide")
st.title("🤖 سماك V3: صائد العملاء (بحث مجاني)")

# 2. جلب المفتاح السري (بنستخدم الحد المجاني للنص فقط)
GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=GOOGLE_API_KEY)

# 3. إعداد الذاكرة
if "chat" not in st.session_state:
    system_instruction = (
        "أنت 'سماك' (Smak). ستصلك نتائج بحث خام من الإنترنت. "
        "مهمتك استخراج أسماء الشركات، أرقام التواصل، والروابط، وترتيبها في جدول احترافي."
    )
    # 👈 شلنا أداة جوجل المدفوعة من هنا عشان ما يزعل السيرفر
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(system_instruction=system_instruction)
    )
    st.session_state.messages = []

# 4. شريط المهام
with st.sidebar:
    st.info("💡 تقدر ترفع كراسة الشروط وسيقوم سماك بتحليلها.")
    uploaded_file = st.file_uploader("ارفع كراسة الشروط (PDF)", type=["pdf"])

# 5. عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. معالجة الطلب (السر هنا)
if prompt := st.chat_input("ابحث لي عن شركات تجهيز مسارح في الرياض..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("سماك يسحب الداتا من النت مجاناً..."):
            try:
                # 👈 1. البحث المجاني باستخدام بايثون
                search_results = DDGS().text(prompt, max_results=5)
                context = f"هذه نتائج بحث حقيقية من الإنترنت:\n{search_results}\n\nالمطلوب منك: رتب هذه البيانات في جدول بناءً على طلب المستخدم التالي: {prompt}"
                
                # 👈 2. نرسل الداتا لـ سماك عشان يضبطها كجدول
                content = [context]
                if uploaded_file:
                    file_bytes = uploaded_file.read()
                    content.append(types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"))

                response = st.session_state.chat.send_message(content)
                st.markdown(response.text)
                
                # النطق الصوتي
                try:
                    tts = gTTS(text=response.text[:300], lang='ar')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except: pass

                # حفظ النتائج للإكسل
                df = pd.DataFrame([{"الرد": response.text}])
                st.download_button("حفظ النتائج كـ Excel", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="smak_leads.csv")
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                st.error(f"⚠️ واجهنا مشكلة بسيطة: {e}")
