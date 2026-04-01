import os
import re
from datetime import datetime

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="Clinic AI Assistant Demo", page_icon="🏥", layout="centered")

# =========================
# DEMO KNOWLEDGE BASE
# =========================
CLINIC_INFO = {
    "clinic_name": "NovaCare Clinic",
    "hours": {
        "monday_friday": "08:00 - 18:00",
        "saturday": "09:00 - 13:00",
        "sunday": "Closed"
    },
    "specialties": [
        "General Medicine",
        "Cardiology",
        "Dermatology",
        "Pediatrics",
        "Gynecology",
        "Orthopedics"
    ],
    "doctors": {
        "Cardiology": ["Dr. Sami Ben Amor", "Dr. Lina Gharbi"],
        "Dermatology": ["Dr. Yasmine Trabelsi"],
        "Pediatrics": ["Dr. Amine Kefi"],
        "General Medicine": ["Dr. Hela Mansouri"],
        "Gynecology": ["Dr. Salma Rekik"],
        "Orthopedics": ["Dr. Aziz Jebali"]
    },
    "address": "Les Berges du Lac, Tunis",
    "phone": "+216 70 000 000",
    "email": "contact@novacare.tn",
    "services": [
        "Consultations",
        "Routine checkups",
        "ECG and cardiac follow-up",
        "Vaccination",
        "Skin consultations",
        "Pediatric follow-up"
    ],
    "faq": {
        "appointment": "You can request an appointment by giving your specialty, preferred day, and phone number.",
        "insurance": "The clinic works with selected insurance partners. Coverage depends on the policy.",
        "preparation": "For a cardiology consultation, bring your previous reports, ECGs, and current medication list.",
        "emergency": "This chatbot is not for emergencies. In urgent cases, call emergency services immediately."
    }
}

DEMO_SLOTS = {
    "Cardiology": ["Tuesday 10:00", "Thursday 15:30", "Friday 11:00"],
    "Dermatology": ["Monday 09:30", "Wednesday 14:00"],
    "Pediatrics": ["Monday 11:00", "Saturday 10:30"],
    "General Medicine": ["Every weekday from 08:30"],
    "Gynecology": ["Tuesday 14:30", "Friday 09:00"],
    "Orthopedics": ["Wednesday 10:00", "Thursday 09:30"]
}

SYSTEM_PROMPT = f"""
You are a professional clinic assistant for {CLINIC_INFO['clinic_name']}.
Your role is to answer clearly, politely, and briefly.
Only use the clinic information provided below.
Do not invent doctors, opening hours, specialties, or policies.
If the user asks for medical diagnosis, say that the chatbot does not provide diagnosis and recommend booking a consultation.
If the user asks for emergencies, clearly instruct them to call emergency services.
If the user asks about appointments, guide them to choose a specialty and an available slot.

Clinic information:
{CLINIC_INFO}
Available slots:
{DEMO_SLOTS}
""".strip()


# =========================
# HELPERS
# =========================
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_specialty(text: str):
    text = normalize_text(text)
    for specialty in CLINIC_INFO["specialties"]:
        if specialty.lower() in text:
            return specialty

    keyword_map = {
        "heart": "Cardiology",
        "cardio": "Cardiology",
        "skin": "Dermatology",
        "child": "Pediatrics",
        "kid": "Pediatrics",
        "baby": "Pediatrics",
        "general": "General Medicine",
        "women": "Gynecology",
        "preg": "Gynecology",
        "bone": "Orthopedics",
        "knee": "Orthopedics",
        "back pain": "Orthopedics",
    }
    for key, value in keyword_map.items():
        if key in text:
            return value
    return None


def rule_based_reply(user_message: str):
    text = normalize_text(user_message)

    if any(word in text for word in ["emergency", "urgent", "dying", "severe pain", "chest pain now"]):
        return "This chatbot is not for emergencies. Please call emergency services immediately or go to the nearest emergency department."

    if any(word in text for word in ["hour", "open", "schedule", "when are you open"]):
        return (
            f"Our hours are: Monday to Friday {CLINIC_INFO['hours']['monday_friday']}, "
            f"Saturday {CLINIC_INFO['hours']['saturday']}, Sunday {CLINIC_INFO['hours']['sunday']}."
        )

    if any(word in text for word in ["address", "where", "location"]):
        return f"The clinic is located at {CLINIC_INFO['address']}."

    if any(word in text for word in ["phone", "call", "contact", "email"]):
        return f"You can contact us at {CLINIC_INFO['phone']} or {CLINIC_INFO['email']}."

    if any(word in text for word in ["specialty", "specialities", "services", "doctor", "doctors"]):
        specs = ", ".join(CLINIC_INFO["specialties"])
        return f"We currently offer these specialties: {specs}."

    if any(word in text for word in ["insurance", "assurance"]):
        return CLINIC_INFO["faq"]["insurance"]

    if any(word in text for word in ["prepare", "preparation", "before consultation"]):
        return CLINIC_INFO["faq"]["preparation"]

    if any(word in text for word in ["appointment", "book", "rendez", "consultation"]):
        specialty = detect_specialty(text)
        if specialty:
            slots = DEMO_SLOTS.get(specialty, [])
            if slots:
                return f"For {specialty}, available demo slots are: {', '.join(slots)}. Reply with the slot you prefer and your phone number."
            return f"We can arrange a {specialty} appointment. Please provide your preferred day and phone number."
        return "Sure. Which specialty do you need? For example: Cardiology, Dermatology, Pediatrics, General Medicine, Gynecology, or Orthopedics."

    if any(word in text for word in ["diagnose", "diagnosis", "what do i have", "is this serious"]):
        return "I cannot provide a medical diagnosis. I can help you find the right specialty or book a consultation."

    return (
        "I can help with appointments, clinic hours, specialties, doctors, address, insurance information, and visit preparation. "
        "How can I assist you?"
    )


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


# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏥 Clinic AI Demo")
st.sidebar.markdown("### What this demo shows")
st.sidebar.markdown(
    """
- Patient FAQ assistant
- Appointment guidance
- Specialty routing
- Basic clinic information retrieval
- AI-ready front layer for future integration
"""
)

st.sidebar.markdown("### Demo specialties")
for specialty in CLINIC_INFO["specialties"]:
    st.sidebar.write(f"• {specialty}")

if st.sidebar.button("Reset conversation"):
    st.session_state.messages = []
    st.rerun()


# =========================
# HEADER
# =========================
st.title("Clinic AI Assistant Demo")
st.caption("Demonstration version for healthcare, chatbot, data centralization, and AI service pitching")

with st.expander("Suggested demo questions"):
    st.markdown(
        """
- What are your opening hours?
- I want an appointment with a cardiologist
- What specialties do you have?
- How should I prepare for a cardiology consultation?
- Where is the clinic located?
- Do you accept insurance?
        """
    )


# =========================
# CHAT STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                f"Hello, welcome to {CLINIC_INFO['clinic_name']}. "
                "I can help with appointments, specialties, clinic hours, and general information."
            )
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# CHAT INPUT
# =========================
user_input = st.chat_input("Type your message here...")

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
st.markdown("### NovaCare Clinic Assistant")
st.markdown("This assistant helps patients with appointments, clinic information, and guidance.")
