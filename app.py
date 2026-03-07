import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import pandas as pd

# 1. إعدادات الواجهة
st.set_page_config(page_title="سماك V3 - المساعد التسويقي", page_icon="🤖", layout="wide")
st.title("🤖 سماك V3: المحلل والباحث الذكي")
st.sidebar.header("إدارة شركة مجال الحدث")

# 2. جلب المفتاح السري وحفظ الاتصال
GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=GOOGLE_API_KEY)

# 3. إعداد الذاكرة وأدوات البحث
if "chat" not in st.session_state:
    # استخدام الصيغة المباشرة للبحث لتجنب أي أخطاء من المكتبة
    search_tool = {"google_search": {}}
    system_instruction = (
        "أنت 'سماك' (Smak)، المساعد التنفيذي. "
        "مهمتك: 1. البحث عن أرقام الشركات والعملاء أونلاين. 2. تحليل ملفات كراسات الشروط. "
        "3. تقديم نصائح تسويقية ذكية."
    )
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(
            system_instruction=system_instruction, 
            tools=[search_tool]
        )
    )
    st.session_state.messages = []

# 4. شريط المهام
with st.sidebar:
    st.info("💡 يمكنك رفع كراسة الشروط هنا وسيقوم سماك بتحليلها.")
    uploaded_file = st.file_uploader("ارفع كراسة الشروط (PDF)", type=["pdf"])

# 5. عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. معالجة الطلب
if prompt := st.chat_input("يا سماك، ابحث لي عن عملاء لشاشات P2.5 في الرياض..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # التعديل الذكي لحل مشكلة السيرفر (ClientError)
    if uploaded_file:
        file_bytes = uploaded_file.read()
        content = [prompt, types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")]
    else:
        content = prompt  # نرسل النص مباشرة إذا ما فيه ملف

    with st.chat_message("assistant"):
        with st.spinner("سماك يحلل ويبحث..."):
            try:
                # إرسال الطلب بشكل آمن
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
                st.download_button("حفظ النتائج كـ Excel", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="smak_data.csv")
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                st.error(f"⚠️ واجه سماك مشكلة مؤقتة في الاتصال بسيرفر البحث. التفاصيل: {e}")


