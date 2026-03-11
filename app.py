import streamlit as st
from groq import Groq

# ==========================================
# 0. إعداد الواجهة الفخمة (Streamlit)
# ==========================================
st.set_page_config(page_title="Mad Genius AI Portal", page_icon="⚖️", layout="wide")

st.markdown("<h1 style='text-align: center; color: #D4AF37;'>Mad Genius AI - Unified Portal</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>بوابة الأعمال الذكية (قانون | موارد بشرية | محاسبة)</h3>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 1. إعداد محرك Groq الخارق
# ==========================================
# كذا الكود بيسحب المفتاح من خزنة سرية بدل ما يكون مكشوف
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("يرجى التأكد من إضافة مفتاح Groq API الصحيح.")

# ==========================================
# 2. هندسة القبعات والموجه الذكي (Router)
# ==========================================
PROMPTS = {
    "LEGAL": "أنت مستشار قانوني سعودي (Mad Legal). أجب بصرامة واحترافية وفقاً للأنظمة السعودية. اكتب الإجابة مقسمة إلى: التكييف القانوني، السند النظامي، الرأي، والإجراء. لا تستخدم الإنجليزية أبداً.",
    
    "HR": "أنت خبير موارد بشرية سعودي (Mad HR). أجب بناءً على نظام العمل السعودي والتأمينات الاجتماعية وقوى. لا تستخدم الإنجليزية أبداً.",
    
    "ACCOUNTING": "أنت محاسب قانوني ومالي سعودي (Mad Accountant). أجب بناءً على معايير المحاسبة (IFRS) وأنظمة هيئة الزكاة (ZATCA). لا تستخدم الإنجليزية أبداً."
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
# 3. إدارة ذاكرة المحادثة (Session State)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 4. محرك المحادثة الحي (Chat Logic)
# ==========================================
if prompt := st.chat_input("اكتب استفسارك هنا (مثال: طريقة حساب نهاية الخدمة، أو نسبة الضريبة؟)"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    domain, status_msg = smart_router(prompt)
    
    with st.chat_message("assistant"):
        st.info(status_msg) 
        message_placeholder = st.empty()
        full_response = ""
        
        groq_messages = [{"role": "system", "content": PROMPTS[domain]}]
        for m in st.session_state.messages:
            groq_messages.append({"role": m["role"], "content": m["content"]})
            
        try:
            # 🌟 الموديل الجديد المحدث جاهز للعمل
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
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
