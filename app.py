import streamlit as st
from groq import Groq
import PyPDF2
import io

# ==========================================
# 0. إعداد الواجهة الفخمة (Streamlit)
# ==========================================
st.set_page_config(page_title="Mad Genius AI Portal", page_icon="⚖️", layout="wide")

# كود ضبط اتجاه النص العربي (RTL)
st.markdown("""
<style>
    * { direction: rtl; text-align: right; }
    .stTextInput input { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #D4AF37;'>Mad Genius AI - Unified Portal</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>بوابة الأعمال الذكية (قانون | موارد بشرية | محاسبة)</h3>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 1. إعداد محرك Groq
# ==========================================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("يرجى التأكد من إضافة مفتاح Groq API الصحيح.")

# ==========================================
# 2. القائمة الجانبية: ميزة رفع الملفات 📎
# ==========================================
with st.sidebar:
    st.header("📎 التحليل المتقدم للمستندات")
    st.write("ارفع ملفك هنا (عقد قانوني، فاتورة، لائحة عمل) وسيقوم النظام بقراءته وتحليله بناءً على استفسارك.")
    uploaded_file = st.file_uploader("اختر ملف (PDF أو TXT)", type=['pdf', 'txt'])

def extract_text_from_file(file):
    text = ""
    if file.name.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    elif file.name.endswith('.txt'):
        text = file.read().decode('utf-8')
    return text

# ==========================================
# 3. هندسة القبعات والموجه الذكي (Router)
# ==========================================
PROMPTS = {
    "LEGAL": "أنت مستشار قانوني سعودي (Mad Legal). أجب بصرامة واحترافية وفقاً للأنظمة السعودية. استخدم محتوى الملف المرفق إذا وجد لتحليل العقود أو القضايا بذكاء. لا تستخدم الإنجليزية أبداً.",
    
    "HR": "أنت خبير موارد بشرية سعودي (Mad HR). أجب بناءً على نظام العمل السعودي. إذا تم إرفاق لائحة أو عقد موظف، قم بتحليله بدقة بناءً على سؤال المستخدم. لا تستخدم الإنجليزية أبداً.",
    
    "ACCOUNTING": "أنت محاسب قانوني ومالي سعودي (Mad Accountant). أجب بناءً على معايير المحاسبة وأنظمة (ZATCA). إذا تم إرفاق فاتورة أو قائمة مالية، استخرج الأرقام وحللها بدقة. لا تستخدم الإنجليزية أبداً."
}

def smart_router(user_input):
    hr_keywords = ['موظف', 'إجازة', 'راتب', 'غياب', 'استقالة', 'تأمينات', 'نهاية خدمة', 'دوام']
    acc_keywords = ['ضريبة', 'زكاة', 'فاتورة', 'ميزانية', 'قوائم مالية', 'خصم', 'إيرادات', 'تكاليف', 'محاسبة', 'هللة']
    
    if any(word in user_input for word in acc_keywords):
        return "ACCOUNTING", "💼 تم التوجيه لقسم المحاسبة (Mad Accountant)"
    elif any(word in user_input for word in hr_keywords):
        return "HR", "👥 تم التوجيه لقسم الموارد البشرية (Mad HR)"
    else:
        return "LEGAL", "⚖️ تم التوجيه للقسم القانوني (Mad Legal)"

# ==========================================
# 4. إدارة ذاكرة المحادثة (Session State)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] != "system": # عشان ما نطبع الملف الكامل في الشاشة للمستخدم
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ==========================================
# 5. محرك المحادثة الحي (Chat Logic)
# ==========================================
if prompt := st.chat_input("اكتب استفسارك هنا (مثال: استخرج الثغرات في هذا العقد المرفق)"):
    
    # عرض سؤال المستخدم في الشاشة
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # التوجيه الذكي (يحلل سؤال المستخدم فقط عشان ما يتشتت بنص الملف)
    domain, status_msg = smart_router(prompt)
    
    # دمج نص الملف مع الطلب (بالخفاء) إذا فيه ملف مرفوع
    final_prompt_to_groq = prompt
    if uploaded_file is not None:
        file_content = extract_text_from_file(uploaded_file)
        # نغلف النص بطريقة هندسية تفهمها الموديلات
        final_prompt_to_groq = f"طلب المستخدم: {prompt}\n\n--- محتوى المستند المرفق للتحليل ---\n{file_content}"

    with st.chat_message("assistant"):
        st.info(status_msg) 
        if uploaded_file is not None:
            st.success(f"📎 تم قراءة واستيعاب ملف: {uploaded_file.name}")
            
        message_placeholder = st.empty()
        full_response = ""
        
        # تجهيز الرسائل مع القبعة المناسبة
        groq_messages = [{"role": "system", "content": PROMPTS[domain]}]
        
        # نحط المحادثات السابقة
        for m in st.session_state.messages[:-1]: 
            groq_messages.append({"role": m["role"], "content": m["content"]})
            
        # نحط الطلب النهائي (السؤال + نص الملف إن وجد)
        groq_messages.append({"role": "user", "content": final_prompt_to_groq})
            
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=groq_messages,
                temperature=0.1, 
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌") 
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال: {e}")
            
    # نحفظ الرد في الذاكرة
    st.session_state.messages.append({"role": "assistant", "content": full_response})
