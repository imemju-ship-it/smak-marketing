import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import pandas as pd
import pyautogui
import time
import os

# 1. إعدادات الواجهة
st.set_page_config(page_title="سماك V3 - الموظف الرقمي", page_icon="🏗️", layout="wide")
st.title("🤖 سماك V3: المحلل، الباحث، والمُنفذ")
st.sidebar.header("إدارة شركة مجال الحدث")

# 2. جلب المفتاح (تأكد من وضعه في Secrets أو كتابته مباشرة للتجربة المحلية)
GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GOOGLE_API_KEY)

# 3. وظائف التحكم الفيزيائي (تشتغل محلياً فقط)
def execute_physical_task(task_type):
    st.warning("⚠️ سيبدأ سماك بالتحكم في الجهاز.. ابعد يدك عن الماوس!")
    time.sleep(2)
    if task_type == "search_haraj":
        pyautogui.press('win')
        time.sleep(1)
        pyautogui.write('chrome')
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.write('https://haraj.com.sa')
        pyautogui.press('enter')
    elif task_type == "open_excel":
        os.system("start excel")

# 4. إعداد الذاكرة وأدوات البحث
if "chat" not in st.session_state:
    search_tool = types.Tool(google_search=types.GoogleSearch())
    system_instruction = (
        "أنت 'سماك' (Smak)، المساعد التنفيذي لشركة 'مجال الحدث'. "
        "مهمتك: 1. البحث عن أرقام الشركات والعملاء أونلاين. 2. تحليل ملفات كراسات الشروط. "
        "3. تقديم نصائح تسويقية ذكية. 4. التحدث بوضوح للمستخدم."
    )
    st.session_state.chat = client.chats.create(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(system_instruction=system_instruction, tools=[search_tool])
    )
    st.session_state.messages = []

# 5. شريط المهام الجانبي (الأوامر السريعة)
with st.sidebar:
    st.subheader("🛠️ أوامر فيزيائية (Local Only)")
    if st.button("فتح حراج والبحث"):
        execute_physical_task("search_haraj")
    if st.button("تشغيل إكسل"):
        execute_physical_task("open_excel")
    
    st.divider()
    uploaded_file = st.file_uploader("ارفع كراسة الشروط (PDF)", type=["pdf"])

# 6. عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. معالجة الإدخال
if prompt := st.chat_input("يا سماك، ابحث لي عن عملاء لشاشات P2.5 في الرياض..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # تجهيز المحتوى (نص + ملف إن وجد)
    content = [prompt]
    if uploaded_file:
        file_bytes = uploaded_file.read()
        content.append(types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"))

    with st.chat_message("assistant"):
        with st.spinner("سماك يفكر ويبحث..."):
            response = st.session_state.chat.send_message(content)
            st.markdown(response.text)
            
            # أ. ميزة النطق الصوتي
            try:
                tts = gTTS(text=response.text[:300], lang='ar') # نطق أول 300 حرف للسرعة
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            except: pass

            # ب. زر تصدير إكسل
            df = pd.DataFrame([{"الرد": response.text}])
            st.download_button("حفظ النتائج كـ Excel", data=df.to_csv().encode('utf-8-sig'), file_name="smak_data.csv")

    st.session_state.messages.append({"role": "assistant", "content": response.text})