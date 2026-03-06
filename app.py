import streamlit as st
from google import genai
from google.genai import types

# 1. إعداد شكل صفحة الويب
st.set_page_config(page_title="سماك - المسوق الذكي", page_icon="🤖", layout="centered")
st.title("🤖 سماك - خبير التسويق (شركة مجال الحدث)")
st.write("أهلاً بك يا مدير! أنا جاهز لكتابة المحتوى، تخطيط الحملات، وتوليد الأفكار.")

# 2. إعداد مفتاح جوجل بشكل آمن
GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GOOGLE_API_KEY)

# 3. تجهيز ذاكرة المحادثة (عشان يتذكر السياق في المتصفح)
if "chat" not in st.session_state:
    system_instruction = (
        "أنت 'سماك' (Smak)، خبير تسويق استراتيجي وصانع محتوى إبداعي يعمل لدى شركة 'مجال الحدث' لتجهيز الفعاليات والمسارح في السعودية. "
        "أسلوبك احترافي، ذكي، مقنع، وتفهم السوق السعودي جيداً."
    )
    config = types.GenerateContentConfig(
        temperature=0.7,
        system_instruction=system_instruction,
    )
    # بدء المحادثة مع النموذج
    st.session_state.chat = client.chats.create(model="gemini-2.5-flash", config=config)
    st.session_state.messages = []

# 4. عرض الرسائل السابقة على الشاشة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. مربع إدخال النص للمستخدم
if prompt := st.chat_input("اكتب فكرتك أو طلبك هنا..."):
    
    # عرض رسالتك في الشاشة وحفظها
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # إرسال الطلب لسماك وعرض الرد
    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text)
    
    # حفظ رد سماك في الذاكرة
    st.session_state.messages.append({"role": "assistant", "content": response.text})