import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import pandas as pd
from duckduckgo_search import DDGS
import PyPDF2
import base64
from PIL import Image

# 1. إعدادات الواجهة
st.set_page_config(page_title="سماك V5 - المحلل البصري", page_icon="👁️", layout="wide")
st.title("🤖 سماك V5: ذو الرؤية الحاسوبية (مجاني)")
st.sidebar.header("إدارة شركة مجال الحدث")

# 2. تفعيل محرك Groq المجاني
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# 3. الذاكرة
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. شريط المهام (لرفع الكراسات والصور)
with st.sidebar:
    st.info("👁️ ارفع صورة (شاشة، موقع، تصميم) أو كراسة شروط.")
    uploaded_image = st.file_uploader("ارفع صورة (JPG/PNG)", type=["jpg", "png", "jpeg"])
    uploaded_file = st.file_uploader("ارفع كراسة الشروط (PDF)", type=["pdf"])

# 5. عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. معالجة الطلب
if prompt := st.chat_input("اطلب من سماك تحليل الصورة المرفقة أو البحث..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("سماك يفتح عيونه ويحلل..."):
            try:
                # إذا المستخدم رفع صورة (رؤية حاسوبية)
                if uploaded_image:
                    # تحويل الصورة لشفرة يفهمها الموديل
                    base64_image = base64.b64encode(uploaded_image.read()).decode('utf-8')
                    
                    # نستخدم نموذج الرؤية الخاص من Groq
                    response = client.chat.completions.create(
                        model="llama-3.2-90b-vision-preview", # 👈 هذا الموديل مخصص للرؤية ومجاني!
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }]
                    )
                    bot_reply = response.choices[0].message.content

                # إذا مافي صورة، يكمل شغل كالمعتاد (بحث ونصوص)
                else:
                    pdf_text = ""
                    if uploaded_file:
                        reader = PyPDF2.PdfReader(uploaded_file)
                        pdf_text = "\n".join([page.extract_text() for page in reader.pages])[:5000]
                        pdf_text = f"\n\n[معلومات الـ PDF]:\n{pdf_text}"

                    search_results = DDGS().text(prompt, max_results=5)
                    context = f"نتائج بحث:\n{search_results}{pdf_text}\n\nالمطلوب: {prompt}"
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": context}]
                    )
                    bot_reply = response.choices[0].message.content

                # عرض الرد
                st.markdown(bot_reply)
                
                # النطق الصوتي
                try:
                    tts = gTTS(text=bot_reply[:300], lang='ar')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except: pass

                # حفظ إكسل
                df = pd.DataFrame([{"الرد": bot_reply}])
                st.download_button("حفظ كـ Excel", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="smak_vision.csv")
                
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            except Exception as e:
                st.error(f"⚠️ خطأ: {e}")
