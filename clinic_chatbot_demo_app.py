import os
import re
from textwrap import dedent

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="Clinique X AI Assistant", page_icon="🏥", layout="wide")

st.markdown(
    dedent("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #f6f8fb 0%, #eef3f9 100%);
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #18253b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #2563eb 100%);
        border-radius: 24px;
        padding: 28px 30px;
        color: white;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.92;
        line-height: 1.5;
    }
    .info-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        min-height: 120px;
    }
    .info-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin-bottom: 0.45rem;
        font-weight: 700;
    }
    .info-value {
        font-size: 1rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.5;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0.25rem 0 0.75rem 0;
    }
    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 6px;
    }
    .pill {
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        background: #dbeafe;
        color: #1d4ed8;
        font-size: 0.88rem;
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    .lang-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    div[data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 0.35rem 0.2rem;
    }
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
        line-height: 1.6;
    }
    [data-testid="stChatInput"] {
        background: white;
        border-radius: 18px;
        border: 1px solid #dbe3ef;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    .footer-note {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    </style>
    """),
    unsafe_allow_html=True,
)

CLINIC_INFO = {
    "clinic_name": "Clinique X",
    "hours": {
        "monday_friday": "08:00 - 18:00",
        "saturday": "09:00 - 13:00",
        "sunday": "Closed"
    },
    "address": "Tunis, Tunisia",
    "phone": "+216 70 000 000",
    "email": "contact@cliniquex.tn",
    "specialties": {
        "en": [
            "General Medicine",
            "Cardiology",
            "Dermatology",
            "Pediatrics",
            "Gynecology",
            "Orthopedics"
        ],
        "fr": [
            "Médecine générale",
            "Cardiologie",
            "Dermatologie",
            "Pédiatrie",
            "Gynécologie",
            "Orthopédie"
        ],
        "ar": [
            "الطب العام",
            "أمراض القلب",
            "الأمراض الجلدية",
            "طب الأطفال",
            "أمراض النساء",
            "جراحة العظام"
        ]
    },
    "faq": {
        "en": {
            "appointment": "You can request an appointment by giving your specialty, preferred day, and phone number.",
            "insurance": "The clinic works with selected insurance partners. Coverage depends on the policy.",
            "preparation": "For a cardiology consultation, bring your previous reports, ECGs, and current medication list.",
            "emergency": "This assistant is not for emergencies. In urgent cases, call emergency services immediately."
        },
        "fr": {
            "appointment": "Vous pouvez demander un rendez-vous en indiquant la spécialité souhaitée, le jour préféré et votre numéro de téléphone.",
            "insurance": "La clinique travaille avec certains partenaires d’assurance. La prise en charge dépend du contrat.",
            "preparation": "Pour une consultation en cardiologie, veuillez apporter vos anciens comptes rendus, ECG et la liste de vos médicaments.",
            "emergency": "Cet assistant n’est pas destiné aux urgences. En cas d’urgence, appelez immédiatement les services d’urgence."
        },
        "ar": {
            "appointment": "يمكنك طلب موعد عبر ذكر الاختصاص المطلوب واليوم المفضل ورقم الهاتف.",
            "insurance": "تتعامل العيادة مع بعض شركات التأمين حسب التغطية المتوفرة في العقد.",
            "preparation": "لاستشارة أمراض القلب، يُرجى إحضار التقارير السابقة وتخطيط القلب وقائمة الأدوية الحالية.",
            "emergency": "هذا المساعد غير مخصص للحالات الطارئة. في الحالات المستعجلة، يرجى الاتصال بخدمات الطوارئ فورًا."
        }
    }
}

SPECIALTY_TRANSLATIONS = {
    "General Medicine": {"fr": "Médecine générale", "ar": "الطب العام"},
    "Cardiology": {"fr": "Cardiologie", "ar": "أمراض القلب"},
    "Dermatology": {"fr": "Dermatologie", "ar": "الأمراض الجلدية"},
    "Pediatrics": {"fr": "Pédiatrie", "ar": "طب الأطفال"},
    "Gynecology": {"fr": "Gynécologie", "ar": "أمراض النساء"},
    "Orthopedics": {"fr": "Orthopédie", "ar": "جراحة العظام"}
}

DEMO_SLOTS = {
    "General Medicine": ["Monday 08:30", "Tuesday 11:00", "Friday 16:00"],
    "Cardiology": ["Tuesday 10:00", "Thursday 15:30", "Friday 11:00"],
    "Dermatology": ["Monday 09:30", "Wednesday 14:00"],
    "Pediatrics": ["Monday 11:00", "Saturday 10:30"],
    "Gynecology": ["Tuesday 14:30", "Friday 09:00"],
    "Orthopedics": ["Wednesday 10:00", "Thursday 09:30"]
}

SYSTEM_PROMPT = f"""
You are a multilingual intelligent assistant for {CLINIC_INFO['clinic_name']}.
You can reply in English, French, or Arabic depending on the user's language.
Be clear, professional, reassuring, and concise.
Your role is to help patients:
- get clinic information
- discover specialties
- ask for appointments
- prepare for consultations
Do not invent clinic policies, doctors, pricing, or medical advice.
If the user asks for diagnosis, say you cannot diagnose and recommend booking a consultation.
If the user mentions an emergency, tell them to call emergency services immediately.
If the user asks for an appointment, ask for specialty, preferred slot, name, and phone number.
Only use the clinic information below.

Clinic information:
{CLINIC_INFO}
Available slots:
{DEMO_SLOTS}
""".strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    fr_markers = ["bonjour", "rendez", "médec", "clinique", "horaire", "assurance", "préparer", "où", "spécialité"]
    lowered = normalize_text(text)
    if any(marker in lowered for marker in fr_markers):
        return "fr"
    return "en"


def display_specialty_name(canonical: str, lang: str) -> str:
    if lang == "en":
        return canonical
    return SPECIALTY_TRANSLATIONS.get(canonical, {}).get(lang, canonical)


def detect_specialty(text: str):
    text_n = normalize_text(text)
    keyword_map = {
        "General Medicine": ["general medicine", "general", "médecine générale", "generaliste", "الطب العام"],
        "Cardiology": ["cardiology", "cardio", "heart", "cardiologie", "coeur", "cœur", "أمراض القلب", "قلب"],
        "Dermatology": ["dermatology", "skin", "dermatologie", "peau", "الأمراض الجلدية", "جلدية"],
        "Pediatrics": ["pediatrics", "child", "kid", "baby", "pédiatrie", "enfant", "طب الأطفال", "أطفال"],
        "Gynecology": ["gynecology", "women", "preg", "gynécologie", "grossesse", "أمراض النساء", "نساء"],
        "Orthopedics": ["orthopedics", "bone", "knee", "back pain", "orthopédie", "os", "جراحة العظام", "عظام"]
    }
    for canonical, keywords in keyword_map.items():
        if any(keyword in text_n for keyword in keywords):
            return canonical
    return None


def get_hours_text(lang: str) -> str:
    if lang == "fr":
        return f"Nos horaires sont : du lundi au vendredi {CLINIC_INFO['hours']['monday_friday']}, samedi {CLINIC_INFO['hours']['saturday']}, dimanche {CLINIC_INFO['hours']['sunday']}."
    if lang == "ar":
        return f"مواعيد العمل هي: من الإثنين إلى الجمعة {CLINIC_INFO['hours']['monday_friday']}، السبت {CLINIC_INFO['hours']['saturday']}، والأحد {CLINIC_INFO['hours']['sunday']}."
    return f"Our hours are: Monday to Friday {CLINIC_INFO['hours']['monday_friday']}, Saturday {CLINIC_INFO['hours']['saturday']}, Sunday {CLINIC_INFO['hours']['sunday']}."


def get_contact_text(lang: str) -> str:
    if lang == "fr":
        return f"Vous pouvez nous contacter au {CLINIC_INFO['phone']} ou par email à {CLINIC_INFO['email']}."
    if lang == "ar":
        return f"يمكنكم التواصل معنا على {CLINIC_INFO['phone']} أو عبر البريد الإلكتروني {CLINIC_INFO['email']}."
    return f"You can contact us at {CLINIC_INFO['phone']} or {CLINIC_INFO['email']}."


def get_address_text(lang: str) -> str:
    if lang == "fr":
        return f"La clinique est située à {CLINIC_INFO['address']}."
    if lang == "ar":
        return f"تقع العيادة في {CLINIC_INFO['address']}."
    return f"The clinic is located at {CLINIC_INFO['address']}."


def get_specialties_text(lang: str) -> str:
    specs = ", ".join(CLINIC_INFO["specialties"][lang])
    if lang == "fr":
        return f"Nous proposons actuellement les spécialités suivantes : {specs}."
    if lang == "ar":
        return f"الاختصاصات المتوفرة حاليا هي: {specs}."
    return f"We currently offer these specialties: {specs}."


def get_appointment_prompt(lang: str) -> str:
    if lang == "fr":
        return "Bien sûr. Quelle spécialité souhaitez-vous ? Par exemple : Médecine générale, Cardiologie, Dermatologie, Pédiatrie, Gynécologie ou Orthopédie."
    if lang == "ar":
        return "بكل سرور. ما هو الاختصاص الذي تحتاجه؟ مثال: الطب العام، أمراض القلب، الأمراض الجلدية، طب الأطفال، أمراض النساء أو جراحة العظام."
    return "Sure. Which specialty do you need? For example: General Medicine, Cardiology, Dermatology, Pediatrics, Gynecology, or Orthopedics."


def get_diagnosis_text(lang: str) -> str:
    if lang == "fr":
        return "Je ne peux pas fournir de diagnostic médical. Je peux toutefois vous orienter vers la bonne spécialité ou vous aider à demander un rendez-vous."
    if lang == "ar":
        return "لا يمكنني تقديم تشخيص طبي. لكن يمكنني مساعدتك في اختيار الاختصاص المناسب أو طلب موعد."
    return "I cannot provide a medical diagnosis. I can help you find the right specialty or request an appointment."


def get_generic_help_text(lang: str) -> str:
    if lang == "fr":
        return "Je peux vous aider pour les rendez-vous, les horaires, les spécialités, les coordonnées de la clinique, les assurances et la préparation avant consultation. Comment puis-je vous aider ?"
    if lang == "ar":
        return "يمكنني مساعدتك في المواعيد، أوقات العمل، الاختصاصات، معلومات التواصل، التأمين، والتحضير قبل الاستشارة. كيف يمكنني مساعدتك؟"
    return "I can help with appointments, clinic hours, specialties, contact information, insurance, and visit preparation. How can I assist you?"


def get_booking_followup(canonical_specialty: str, lang: str) -> str:
    local_name = display_specialty_name(canonical_specialty, lang)
    slots = DEMO_SLOTS.get(canonical_specialty, [])
    if lang == "fr":
        if slots:
            return f"Pour {local_name}, les créneaux de démonstration disponibles sont : {', '.join(slots)}. Merci de me donner le créneau souhaité, votre nom complet et votre numéro de téléphone pour confirmer la demande."
        return f"Nous pouvons organiser un rendez-vous en {local_name}. Merci de me préciser votre jour préféré, votre nom complet et votre numéro de téléphone."
    if lang == "ar":
        if slots:
            return f"بالنسبة إلى {local_name}، المواعيد التجريبية المتاحة هي: {', '.join(slots)}. يرجى تزويدي بالموعد المناسب، الاسم الكامل، ورقم الهاتف لتأكيد الطلب."
        return f"يمكننا ترتيب موعد في اختصاص {local_name}. يرجى تزويدي باليوم المفضل، الاسم الكامل، ورقم الهاتف."
    if slots:
        return f"For {local_name}, available demo slots are: {', '.join(slots)}. Please share your preferred slot, full name, and phone number to confirm the request."
    return f"We can arrange a {local_name} appointment. Please provide your preferred day, full name, and phone number."


def rule_based_reply(user_message: str):
    text = normalize_text(user_message)
    lang = detect_language(user_message)

    emergency_terms = ["emergency", "urgent", "severe pain", "chest pain now", "urgence", "douleur intense", "طوارئ", "مستعجل", "ألم شديد"]
    if any(term in text for term in emergency_terms):
        return CLINIC_INFO["faq"][lang]["emergency"]

    if any(word in text for word in ["hour", "open", "schedule", "horaire", "horaires", "ouvert", "وقت", "مواعيد", "ساعات"]):
        return get_hours_text(lang)

    if any(word in text for word in ["address", "where", "location", "adresse", "où", "عنوان", "أين", "موقع"]):
        return get_address_text(lang)

    if any(word in text for word in ["phone", "call", "contact", "email", "téléphone", "contacter", "هاتف", "اتصال", "بريد"]):
        return get_contact_text(lang)

    if any(word in text for word in ["specialty", "specialties", "services", "doctor", "doctors", "spécialité", "spécialités", "médecin", "اختصاص", "اختصاصات", "خدمات", "طبيب"]):
        return get_specialties_text(lang)

    if any(word in text for word in ["insurance", "assurance", "تأمين"]):
        return CLINIC_INFO["faq"][lang]["insurance"]

    if any(word in text for word in ["prepare", "preparation", "before consultation", "préparer", "préparation", "avant consultation", "تحضير", "قبل الاستشارة"]):
        return CLINIC_INFO["faq"][lang]["preparation"]

    if any(word in text for word in ["appointment", "book", "consultation", "rendez", "rdv", "موعد", "حجز", "استشارة"]):
        specialty = detect_specialty(user_message)
        if specialty:
            return get_booking_followup(specialty, lang)
        return get_appointment_prompt(lang)

    if any(word in text for word in ["diagnose", "diagnosis", "what do i have", "is this serious", "diagnostic", "تشخيص", "هل هذا خطير"]):
        return get_diagnosis_text(lang)

    return get_generic_help_text(lang)


def llm_reply(messages):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        return None


st.sidebar.title("🏥 Clinique X")
st.sidebar.markdown("### Smart Reception Demo")
st.sidebar.markdown("""
This demo presents a multilingual front-desk assistant for:
- appointment guidance
- patient information
- specialty orientation
- AI-ready service automation
""")

st.sidebar.markdown("### Supported languages")
st.sidebar.write("English · Français · العربية")

st.sidebar.markdown("### Available specialties")
for specialty in CLINIC_INFO["specialties"]["en"]:
    st.sidebar.write(f"• {specialty}")

st.sidebar.markdown("### Quick positioning")
st.sidebar.caption(
    "This interface can later connect to scheduling systems, internal FAQs, CRM tools, and analytics dashboards."
)

if st.sidebar.button("Reset conversation"):
    st.session_state.messages = []
    st.rerun()

st.markdown("""
<div class="hero-card">
    <div class="hero-title">Clinique X Intelligent Assistant</div>
    <div class="hero-subtitle">
        A multilingual assistant for appointments, patient guidance, and clinic information.<br>
        Designed as a premium demonstration of AI-enabled reception and service automation.
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    st.markdown(f"""
    <div class="info-card">
        <div class="info-label">Clinic Hours</div>
        <div class="info-value">Mon–Fri {CLINIC_INFO['hours']['monday_friday']}<br>Sat {CLINIC_INFO['hours']['saturday']}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="info-card">
        <div class="info-label">Contact</div>
        <div class="info-value">{CLINIC_INFO['phone']}<br>{CLINIC_INFO['email']}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="info-card">
        <div class="info-label">Location</div>
        <div class="info-value">{CLINIC_INFO['address']}</div>
    </div>
    """, unsafe_allow_html=True)

col_left, col_right = st.columns([1.35, 1])

with col_left:
    st.markdown('<div class="section-title">Available specialties</div>', unsafe_allow_html=True)
    pills_html = "".join([f'<span class="pill">{item}</span>' for item in CLINIC_INFO["specialties"]["en"]])
    st.markdown(f'<div class="pill-row">{pills_html}</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-title">Suggested demo questions</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="lang-box">
    <strong>English</strong><br>
    • What are your opening hours?<br>
    • I want an appointment with a cardiologist<br>
    • Do you accept insurance?<br><br>
    <strong>Français</strong><br>
    • Quels sont vos horaires ?<br>
    • Je veux un rendez-vous en cardiologie<br>
    • Acceptez-vous l’assurance ?<br><br>
    <strong>العربية</strong><br>
    • ما هي أوقات العمل؟<br>
    • أريد موعدًا مع طبيب قلب<br>
    • هل تقبلون التأمين؟
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="section-title">Live conversation</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello and welcome to Clinique X.\n\n"
                "Bonjour et bienvenue chez Clinique X.\n\n"
                "مرحبًا بكم في Clinique X.\n\n"
                "I can help with appointments, clinic information, and specialties."
            )
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type your message here | Tapez votre message ici | اكتب رسالتك هنا")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    llm_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] in ["user", "assistant"]
    ]

    answer = llm_reply(llm_messages)
    if not answer:
        answer = rule_based_reply(user_input)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

st.divider()
st.markdown("### Clinique X Assistant")
st.markdown("This assistant helps patients with appointments, clinic information, and service orientation.")
st.markdown(
    '<div class="footer-note">Built as a premium demonstration for AI-enabled patient reception and smart service automation.</div>',
    unsafe_allow_html=True,
)
