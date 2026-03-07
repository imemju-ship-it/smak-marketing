import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import pandas as pd
from duckduckgo_search import DDGS
import PyPDF2

# 1. إعدادات الواجهة
st.set_page_config(page_title="سماك V4 - النسخة المجانية المستقلة", page_icon="🚀", layout="wide")
st.title("🤖 سماك V4: صائد العملاء (بدون قيود)")
st.sidebar.header("إدارة شركة مجال الحدث")

# 2. تفعيل محرك Groq المجاني
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# 3. إعداد الذاكرة
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "أنت 'سماك'، خبير تسويق في شركة 'مجال الحدث' في السعودية. تجيب باللغة العربية بطلاقة، وتستخرج البيانات من النصوص وترتبها في جداول احترافية."}
    ]

# 4. شريط المهام (لرفع الكراسات)
with st.sidebar:
    st.info("💡 ارفع كراسة الشروط (PDF) وسيقوم سماك بتحليلها مجاناً.")
    uploaded_file = st.file_uploader("ارفع كراسة الشروط", type=["pdf"])

# 5. عرض المحادثة
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 6. معالجة الطلب
if prompt := st.chat_input("ابحث عن شركات مسارح في الرياض، أو اسألني عن الكراسة..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("سماك يحلل ويبحث بسرعة البرق..."):
            try:
                # أ. إضافة محتوى الـ PDF إذا تم رفعه
                pdf_text = ""
                if uploaded_file:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    pdf_text = "\n".join([page.extract_text() for page in reader.pages])
                    pdf_text = f"\n\n[معلومات من ملف الـ PDF المرفق]:\n{pdf_text[:5000]}" # نأخذ أول 5000 حرف لتجنب الضغط

                # ب. البحث المجاني في الإنترنت
                search_results = DDGS().text(prompt, max_results=5)
                context = f"بناءً على هذا البحث من الإنترنت:\n{search_results}{pdf_text}\n\nأجب على طلب المستخدم ورتب البيانات بوضوح: {prompt}"

                # ج. إرسال الطلب لمحرك Groq المجاني
                api_messages = st.session_state.messages.copy()
                api_messages[-1] = {"role": "user", "content": context}

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # نموذج جبار ومجاني
                    messages=api_messages,
                    temperature=0.7
                )
                
                bot_reply = response.choices[0].message.content
                st.markdown(bot_reply)
                
                # النطق الصوتي
                try:
                    tts = gTTS(text=bot_reply[:300], lang='ar')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except: pass

                # حفظ النتائج للإكسل
                df = pd.DataFrame([{"الرد": bot_reply}])
                st.download_button("حفظ كـ Excel", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="smak_free.csv")
                
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            except Exception as e:
                st.error(f"⚠️ خطأ بسيط: {e}")
