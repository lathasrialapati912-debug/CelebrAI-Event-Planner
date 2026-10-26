import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import uuid
from html import escape
from streamlit.errors import StreamlitSecretNotFoundError
from app_resources import get_gemini_client
from checklist_utils import (
    checklist_progress,
    filter_checklist_tasks,
    is_task_overdue,
)
from expense_utils import (
    EXPENSE_COLUMNS,
    budget_status,
    calculate_expense_summary,
)
from plan_utils import (
    MAX_CHECKLIST_ITEMS,
    decode_event_plan,
    encode_event_plan,
)
from translations import LANGUAGES, t, translate
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)    

st.set_page_config(
    page_title="CelebrAI | Smart Event Planner",
    page_icon="✨",
    layout="wide"
)


def clear_expense_editor_state():
    st.session_state.pop("expense_editor", None)


def current_event_plan_data():
    """Build a JSON-safe snapshot from current session state."""
    event_type = st.session_state.get("event_type", "Wedding")
    event_name = st.session_state.get("event_name", "")
    location = st.session_state.get("event_location", "")
    event_date = st.session_state.get("celebrai_event_date", date.today())
    invitation_date = st.session_state.get("invitation_date", date.today())
    expenses = st.session_state.get("event_expenses")
    if not isinstance(expenses, pd.DataFrame):
        expenses = pd.DataFrame({
            "Expense": ["Venue", "Food & Catering", "Decoration"],
            "Category": ["Venue", "Food", "Decoration"],
            "Estimated Cost (₹)": [10000, 15000, 5000],
            "Actual Cost (₹)": [10000, 14000, 4500],
        })
    expenses = expenses.reindex(columns=EXPENSE_COLUMNS)
    expense_rows = []
    for row in expenses.to_dict(orient="records"):
        expense_row = {}
        for column in EXPENSE_COLUMNS:
            value = row[column]
            if pd.isna(value):
                value = None
            elif column in ("Estimated Cost (₹)", "Actual Cost (₹)"):
                value = float(value)
            elif column == "Expense":
                value = str(value)
            elif column == "Category":
                value = str(value)
            expense_row[column] = value
        expense_rows.append(expense_row)

    return {
        "version": 1,
        "event": {
            "type": event_type,
            "name": event_name,
            "location": location,
            "budget": st.session_state.get("event_budget", 50000),
            "guests": st.session_state.get("event_guest_count", 100),
            "theme": st.session_state.get("event_theme", "Royal & Luxurious"),
            "date": event_date.isoformat(),
        },
        "preferences": {
            "language": st.session_state.get("celebrai_language", "English"),
            "visual_theme": st.session_state.get("theme_selector", "Royal Purple"),
            "font": st.session_state.get("font_selector", "Modern"),
        },
        "expense_budget": st.session_state.get("expense_tracker_budget", 50000),
        "expenses": expense_rows,
        "checklist": st.session_state.get("checklist_tasks", []),
        "invitation": {
            "title": st.session_state.get(
                "invitation_title", event_name or "Our Special Day"
            ),
            "date": invitation_date.isoformat(),
            "location": st.session_state.get("invitation_location", location),
            "message": st.session_state.get(
                "invitation_message", translate(
                    "invitation_default_message",
                    st.session_state.get("celebrai_language", "English"),
                )
            ),
            "style": st.session_state.get("invitation_design", "Royal Gold"),
        },
    }


def restore_event_plan(plan):
    """Apply a previously validated plan before its widgets are created."""
    clear_expense_editor_state()
    for key in list(st.session_state):
        if key.startswith(("checklist_completed_", "checklist_text_")):
            st.session_state.pop(key, None)
    event = plan["event"]
    preferences = plan["preferences"]
    invitation = plan["invitation"]
    st.session_state["event_type"] = event["type"]
    st.session_state["event_name"] = event["name"]
    st.session_state["event_location"] = event["location"]
    st.session_state["event_budget"] = event["budget"]
    st.session_state["event_guest_count"] = event["guests"]
    st.session_state["event_theme"] = event["theme"]
    st.session_state["celebrai_event_date"] = date.fromisoformat(event["date"])
    st.session_state["celebrai_language"] = preferences["language"]
    st.session_state["theme_selector"] = preferences["visual_theme"]
    st.session_state["font_selector"] = preferences["font"]
    st.session_state["expense_tracker_budget"] = plan["expense_budget"]
    st.session_state["event_expenses"] = pd.DataFrame(
        plan["expenses"], columns=EXPENSE_COLUMNS
    )
    st.session_state["checklist_tasks"] = plan["checklist"]
    st.session_state["invitation_title"] = invitation["title"]
    st.session_state["invitation_date"] = date.fromisoformat(invitation["date"])
    st.session_state["invitation_location"] = invitation["location"]
    st.session_state["invitation_message"] = invitation["message"]
    st.session_state["invitation_design"] = invitation["style"]


with st.expander(t("plan_backup_title"), expanded=False):
    st.write(t("plan_backup_description"))
    st.caption(t("backup_download_note"))
    try:
        backup_data = encode_event_plan(current_event_plan_data())
    except ValueError as error:
        st.error(str(error))
    else:
        st.download_button(
            t("download_backup"),
            data=backup_data,
            file_name="CelebrAI_Event_Plan_Backup.json",
            mime="application/json",
            key="download_event_plan_backup",
        )

    uploaded_plan = st.file_uploader(
        t("upload_backup"),
        type=["json"],
        max_upload_size=1,
        key="event_plan_backup_upload",
    )
    if st.button(t("restore_backup"), key="restore_event_plan"):
        if uploaded_plan is None:
            st.warning(t("backup_missing"))
        else:
            try:
                restored_plan = decode_event_plan(uploaded_plan.getvalue())
            except ValueError as error:
                st.error(t("backup_error", error=str(error)))
            else:
                restore_event_plan(restored_plan)
                st.success(t("backup_restored"))


st.markdown(
    """
    <style>
    .celebrai-welcome {
        padding: 35px 25px;
        border-radius: 24px;
        text-align: center;
        color: white;
        background: linear-gradient(
            120deg,
            #241044,
            #7739a8,
            #db6099,
            #d4a642
        );
        background-size: 250% 250%;
        animation: welcomeGradient 8s ease infinite;
        box-shadow: 0 12px 35px rgba(100, 50, 150, 0.25);
    }

    @keyframes welcomeGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .celebrai-welcome h1 {
        color: white;
        font-family: Georgia, serif;
        font-size: clamp(28px, 5vw, 44px);
    }

    .celebrai-welcome p {
        color: white;
        font-size: 17px;
    }

    .celebrai-feature {
        padding: 18px;
        border: 1px solid rgba(150, 120, 200, 0.4);
        border-radius: 16px;
        text-align: center;
        min-height: 130px;
        margin-bottom: 12px;
        background: #10091f;
    }

    .celebrai-welcome-content {
        padding: 16px;
        border-radius: 16px;
        background: #10091f;
    }
    :root {
        --ink: #24183f;
        --muted: #e8dff2;
    }

    *:focus-visible {
        outline: 3px solid #ffffff !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 6px #24183f !important;
    }

    .small-note,
    .metric-label,
    .stCaption,
    [data-testid="stCaptionContainer"] {
        color: #e8dff2 !important;
    }

    .stApp label,
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    .stApp input,
    .stApp textarea,
    .stApp select {
        color: #24183F !important;
        background-color: #FFFFFF !important;
    }

    .stApp [data-baseweb="select"] {
        color: #24183F !important;
    }

    .stApp [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #24183F !important;
        border-radius: 12px !important;
    }

    .stApp [data-testid="stDownloadButton"] > button {
        background: linear-gradient(90deg, #FFD166, #FF8FAB) !important;
        color: #24183F !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        min-height: 48px !important;
        width: 100% !important;
        opacity: 1 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }

    .stApp [data-testid="stDownloadButton"] > button p,
    .stApp [data-testid="stDownloadButton"] > button span {
        color: #24183F !important;
        font-weight: 700 !important;
    }

    .stApp [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(90deg, #FFB703, #FF6FAE) !important;
        color: #24183F !important;
        border-color: #FFD166 !important;
        transform: translateY(-2px);
    }

    </style>
    """,
    unsafe_allow_html=True
)

_, language_col = st.columns([4, 1])
with language_col:
    selected_language = st.selectbox(
        t("language_label"),
        list(LANGUAGES),
        index=0,
        key="celebrai_language",
        on_change=clear_expense_editor_state,
    )

if LANGUAGES[selected_language] == "ar":
    st.markdown(
        "<style>.stApp { direction: rtl; }</style>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="celebrai-welcome">
        <div class="celebrai-welcome-content">
            <h1><span aria-hidden="true">✨</span> {t("welcome_title")} <span aria-hidden="true">✨</span></h1>
        <p>{t("welcome_tagline")}</p>
        <p>
            {t("welcome_intro")}
        </p>
        <div aria-hidden="true" style="font-size: 30px; margin-top: 15px;">
            🎉 💜 🎂 💐 🎊
        </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.header(f"🌟 {t('studio_title')}")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown(
        f"""
        <div class="celebrai-feature">
            <div aria-hidden="true" style="font-size:32px;">🤖</div>
            <h3>{t("feature_ai")}</h3>
            <p>{t("feature_ai_desc")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature_col2:
    st.markdown(
        f"""
        <div class="celebrai-feature">
            <div aria-hidden="true" style="font-size:32px;">💰</div>
            <h3>{t("feature_budget")}</h3>
            <p>{t("feature_budget_desc")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature_col3:
    st.markdown(
        f"""
        <div class="celebrai-feature">
            <div aria-hidden="true" style="font-size:32px;">💌</div>
            <h3>{t("feature_invitation")}</h3>
            <p>{t("feature_invitation_desc")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.info(
    f"💡 {t('tip')}"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&family=Pacifico&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --gold: #ffd782;
    --pink: #ff8fca;
    --purple: #a78bfa;
    --glass: rgba(255,255,255,0.075);
    --border: rgba(255,255,255,0.16);
}

.stApp {
    background:
        radial-gradient(ellipse at 10% 5%, rgba(142,68,173,.24), transparent 35%),
        radial-gradient(ellipse at 90% 30%, rgba(225,90,150,.16), transparent 35%),
        linear-gradient(135deg,#10091f,#211137 50%,#10152c);
    color: #fff;
    font-family: 'Outfit', sans-serif;
    animation: backgroundShift 12s ease-in-out infinite alternate;
}

@keyframes backgroundShift {
    0% { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}

@keyframes floatUp {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes sparkle {
    0%,100% { opacity: .35; transform: scale(.8); }
    50% { opacity: 1; transform: scale(1.15); }
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--gold) !important;
}

p, label, .stMarkdown, [data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif;
}

.hero {
    position: relative;
    overflow: hidden;
    padding: 45px 22px;
    border: 1px solid var(--border);
    border-radius: 28px;
    text-align: center;
    background: linear-gradient(
        135deg,
        rgba(167,139,250,.16),
        rgba(255,143,202,.09),
        rgba(255,215,130,.09)
    );
    backdrop-filter: blur(18px);
    box-shadow: 0 15px 50px rgba(0,0,0,.18);
    animation: fadeIn 1s ease-out both;
}

.hero::before {
    content: "";
    position: absolute;
    top: 12px;
    right: 15px;
    color: var(--gold);
    letter-spacing: 8px;
    animation: sparkle 3s ease-in-out infinite;
}

.hero-title {
    font-family: 'Pacifico', cursive;
    font-size: clamp(38px, 7vw, 68px);
    line-height: 1.4;
    color: #ffd782;
    background: linear-gradient(
        90deg,#ffd782,#ff8fca,#b9a4ff,#ffd782
    );
    background-size: 250% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 7s linear infinite;
}

.event-card {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 22px 12px;
    text-align: center;
    min-height: 135px;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 24px rgba(0,0,0,.12);
    transition: transform .3s ease, border-color .3s ease,
                background .3s ease;
    animation: fadeIn .7s ease-out both;
}

.event-card:hover {
    transform: translateY(-8px) scale(1.025);
    border-color: var(--gold);
    background: rgba(255,215,130,.12);
}

.event-card h2 {
    font-size: 38px !important;
    animation: floatUp 3s ease-in-out infinite;
}

div.stButton > button {
    background: linear-gradient(100deg,#ffd782,#ff8fca,#b9a4ff);
    background-size: 200% auto;
    color: #21102e;
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 15px;
    font-family: 'Outfit', sans-serif;
    font-size: 16px;
    font-weight: 700;
    min-height: 48px;
    box-shadow: 0 5px 22px rgba(255,143,202,.15);
    transition: transform .25s ease, box-shadow .25s ease;
}

div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 30px rgba(255,143,202,.3);
    border-color: white;
}

div[data-testid="stMetric"] {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    transition: transform .25s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg,#ffd782,#ff8fca,#a78bfa);
    border-radius: 20px;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background-color: #ffffff;
    border: 2px solid #24183f;
    border-radius: 12px;
}

div[data-testid="stVerticalBlock"] > div {
    animation: fadeIn .45s ease-out;
}

hr {
    border-color: rgba(255,255,255,.16);
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

@media (max-width: 640px) {
    .celebrai-welcome,
    .hero {
        padding: 24px 16px;
    }
}

.stApp {
    color: #f8f5fb;
    font-family: 'Outfit', 'Segoe UI', sans-serif;
    animation: none;
}

.celebrai-welcome {
    padding: clamp(20px, 4vw, 36px) 20px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.06);
    box-shadow: none;
    animation: none;
}

.celebrai-welcome-content {
    padding: 12px;
    background: transparent;
}

h1, h2, h3, h4 {
    color: var(--celebrai-accent, #ffd782) !important;
}

.hero {
    padding: clamp(24px, 5vw, 48px) 22px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.06);
    box-shadow: none;
    animation: none;
}

.hero-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(36px, 6vw, 58px);
    line-height: 1.2;
    color: var(--celebrai-accent, #ffd782);
    background: none;
    -webkit-text-fill-color: currentColor;
    animation: none;
}

.event-card,
.celebrai-feature,
div[data-testid="stMetric"] {
    min-height: auto;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    box-shadow: none;
    backdrop-filter: none;
    animation: none;
}

.event-card {
    padding: 18px 12px;
}

.event-card:hover,
div[data-testid="stMetric"]:hover {
    transform: none;
    border-color: var(--celebrai-accent, #ffd782);
    background: rgba(255, 255, 255, 0.09);
}

div.stButton > button,
.stApp [data-testid="stDownloadButton"] > button {
    min-height: 44px;
    border: 1px solid var(--celebrai-accent, #ffd782);
    border-radius: 10px;
    background: var(--celebrai-accent, #ffd782);
    color: #21102e;
    box-shadow: none;
    transition: background-color 0.15s ease, border-color 0.15s ease;
}

div.stButton > button:hover,
.stApp [data-testid="stDownloadButton"] > button:hover {
    transform: none;
    border-color: #ffffff;
    box-shadow: none;
}

div[data-testid="stMetric"] {
    padding: 16px;
}

div[data-testid="stVerticalBlock"] > div {
    animation: none;
}

*:focus-visible {
    outline: 3px solid var(--celebrai-accent, #ffd782) !important;
    outline-offset: 3px !important;
    box-shadow: 0 0 0 2px #21102e !important;
}

@media (max-width: 640px) {
    .event-card {
        padding: 14px 8px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
    }
}
</style>
""", unsafe_allow_html=True)
# Visual theme selector
st.sidebar.header(f"🎨 {t('customize_experience')}")

theme_option_labels = {
    "Royal Purple": "theme_option_royal_purple",
    "Rose Gold": "theme_option_rose_gold",
    "Ocean Dream": "theme_option_ocean_dream",
    "Emerald Elegance": "theme_option_emerald_elegance",
    "Midnight Galaxy": "theme_option_midnight_galaxy",
}
selected_theme = st.sidebar.selectbox(
    t("choose_theme"),
    list(theme_option_labels),
    format_func=lambda option: translate(
        theme_option_labels[option], selected_language
    ),
    key="theme_selector",
)

theme_settings = {
    "Royal Purple": ("#10091f", "#ffd782", "#ff8fca"),
    "Rose Gold": ("#29141f", "#ffcfb3", "#ff91b8"),
    "Ocean Dream": ("#071c2c", "#83e9ff", "#80bfff"),
    "Emerald Elegance": ("#0b211b", "#b5f5cb", "#75dfbd"),
    "Midnight Galaxy": ("#10102e", "#c4a7ff", "#f0a5ff")
}

bg_color, accent_color, secondary_color = theme_settings[selected_theme]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: radial-gradient(
            ellipse at top right,
            {secondary_color}20,
            transparent 45%
        ), {bg_color};
        animation: none;
        --celebrai-accent: {accent_color};
        --celebrai-secondary: {secondary_color};
    }}
    h1, h2, h3 {{
        color: var(--celebrai-accent) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
font_option_labels = {
    "Modern": "font_option_modern",
    "Elegant": "font_option_elegant",
    "Playful": "font_option_playful",
    "Futuristic": "font_option_futuristic",
}
font_choice = st.sidebar.selectbox(
    t("choose_typography"),
    list(font_option_labels),
    format_func=lambda option: translate(
        font_option_labels[option], selected_language
    ),
    key="font_selector",
)

font_settings = {
    "Modern": "'Outfit', sans-serif",
    "Elegant": "'Playfair Display', serif",
    "Playful": "'Pacifico', cursive",
    "Futuristic": "'Space Grotesk', sans-serif"
}

selected_font = font_settings[font_choice]

st.markdown(
    f"""
    <style>
    .stApp {{
        font-family: {selected_font};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(f"### {t('quick_navigation')}")
for section_label, section_anchor in [
    (t("preview_title"), "celebration-preview"),
    (t("timeline"), "preparation-timeline"),
    (t("checklist"), "event-checklist"),
    (t("download_plan"), "download-event-plan"),
    (t("ai_planner"), "ai-event-planner"),
    (t("countdown"), "celebration-countdown"),
    (t("invitation"), "invitation-studio"),
    (t("expense_tracker"), "expense-tracker"),
    (t("theme_gallery"), "theme-gallery"),
    (t("professional_plan"), "professional-event-plan"),
    (t("theme_recommendations"), "ai-theme-recommendations"),
]:
    st.sidebar.markdown(f"[{section_label}](#{section_anchor})")

st.markdown(f"""
<div class="hero">
    <div class="hero-title">{t("hero_title")}</div>
    <h3>{t("hero_subtitle")}</h3>
    <p>{t("hero_description")}</p>
</div>
""", unsafe_allow_html=True)

st.write("")

st.subheader(f"🎊 {t('choose_celebration')}")

col1, col2, col3, col4 = st.columns(4)

event_type_labels = {
    "Wedding": "option_wedding",
    "Birthday": "option_birthday",
    "College Fest": "option_college_fest",
    "Anniversary": "option_anniversary",
    "Community Celebration": "option_community",
}
events = [
    ("💍", "Wedding", "event_card_wedding"),
    ("🎂", "Birthday", "event_card_birthday"),
    ("🎓", "College Fest", "event_card_college"),
    ("🎉", "Anniversary", "event_card_anniversary"),
]

for col, (emoji, name, label_key) in zip(
    [col1, col2, col3, col4], events
):
    with col:
        st.markdown(
            f'<div class="event-card">'
            f'<span aria-hidden="true" style="font-size:38px;">{emoji}</span>'
            f'<p><strong>{t(label_key)}</strong></p></div>',
            unsafe_allow_html=True
        )

st.write("")
st.divider()

st.subheader(f"💫 {t('design_event')}")

event_type = st.selectbox(
    t("event_type"),
    list(event_type_labels),
    format_func=lambda option: translate(
        event_type_labels[option], selected_language
    ),
    key="event_type",
)

event_name = st.text_input(
    t("event_name"),
    placeholder=t("event_name_placeholder"),
    max_chars=120,
    key="event_name",
)

location = st.text_input(
    t("location"),
    placeholder=t("location_placeholder"),
    max_chars=200,
    key="event_location",
)

budget = st.slider(
    f"💰 {t('budget')}",
    min_value=5000,
    max_value=500000,
    value=50000,
    step=5000,
    key="event_budget",
)

guests = st.number_input(
    f"👥 {t('guest_count')}",
    min_value=1,
    max_value=10000,
    value=100,
    key="event_guest_count",
)

event_vibe_labels = {
    "Royal & Luxurious": "option_royal",
    "Traditional Indian": "option_traditional",
    "Elegant & Minimal": "option_minimal",
    "Colorful & Fun": "option_colorful",
    "Modern & Futuristic": "option_futuristic",
}
theme = st.selectbox(
    f"🎨 {t('event_vibe')}",
    list(event_vibe_labels),
    format_func=lambda option: translate(
        event_vibe_labels[option], selected_language
    ),
    key="event_theme",
)

st.metric(f"💎 {t('budget_per_guest')}", f"₹{budget / guests:,.0f}")

st.write(f"#### 💰 {t('live_budget')}")

allocations = {
    "Venue": 0.25,
    "Catering": 0.30,
    "Decoration": 0.15,
    "Photography": 0.10,
    "Entertainment": 0.10,
    "Miscellaneous": 0.10
}
allocation_labels = {
    "Venue": "budget_venue",
    "Catering": "budget_catering",
    "Decoration": "budget_decoration",
    "Photography": "budget_photography",
    "Entertainment": "budget_entertainment",
    "Miscellaneous": "budget_miscellaneous",
}

for category, percentage in allocations.items():
    amount = budget * percentage
    st.write(f"**{t(allocation_labels[category])}** — ₹{amount:,.0f}")
    st.progress(percentage)

if st.button(f"✨ {t('generate_event')}", width="stretch"):
    st.balloons()

    st.success(t("concept_ready"))

    st.markdown(f"### 👑 {t('preview_title')}")

    st.write(
        f"**{t('event_name')}:** "
        f"{event_name or t(event_type_labels[event_type])}"
    )
    st.write(
        f"**{t('event_type')}:** {t(event_type_labels[event_type])}"
    )
    st.write(
        f"**{t('event_location')}:** {location or t('not_specified')}"
    )
    st.write(f"**{t('guests')}:** {guests}")
    st.write(f"**{t('event_vibe')}:** {t(event_vibe_labels[theme])}")
    st.write(f"**{t('total_budget')}:** ₹{budget:,.0f}")

st.divider()

st.header(f"🎨 {t('preview_title')}", anchor="celebration-preview")

theme_visuals = {
    "Royal & Luxurious": {
        "emoji": "👑",
        "description_key": "visual_royal",
        "color": "#b8860b"
    },
    "Traditional Indian": {
        "emoji": "🪷",
        "description_key": "visual_traditional",
        "color": "#c2410c"
    },
    "Elegant & Minimal": {
        "emoji": "🤍",
        "description_key": "visual_minimal",
        "color": "#64748b"
    },
    "Colorful & Fun": {
        "emoji": "🎊",
        "description_key": "visual_colorful",
        "color": "#db2777"
    },
    "Modern & Futuristic": {
        "emoji": "🚀",
        "description_key": "visual_futuristic",
        "color": "#7c3aed"
    }
}

visual = theme_visuals[theme]

with st.container(border=True):
    st.subheader(
        f"{visual['emoji']} {event_name or t(event_type_labels[event_type])}"
    )
    st.write(t(visual["description_key"]))
    detail_col1, detail_col2, detail_col3 = st.columns(3)
    detail_col1.metric(
        t("event_location"),
        location or t("not_specified"),
    )
    detail_col2.metric(t("guests"), f"{guests:,}")
    detail_col3.metric(t("total_budget"), f"₹{budget:,.0f}")

st.caption(f"✨ {t('preview_updates')}")
st.divider()

st.markdown(
    f"<center>✨ {t('crafted_by')} ✨</center>",
    unsafe_allow_html=True
)
st.divider()

st.header(f"📅 {t('timeline')}", anchor="preparation-timeline")

timeline = [
    ("timeline_four_weeks", "task_four_weeks"),
    ("timeline_three_weeks", "task_three_weeks"),
    ("timeline_two_weeks", "task_two_weeks"),
    ("timeline_one_week", "task_one_week"),
    ("timeline_two_days", "task_two_days"),
    ("timeline_event_day", "task_event_day"),
]

localized_timeline = [(t(timing), t(task)) for timing, task in timeline]
for timing, task in localized_timeline:
    with st.expander(f"🗓️ {timing}"):
        st.write(task)
        st.divider()

st.header(f"✅ {t('checklist')}", anchor="event-checklist")
st.write(t("checklist_desc"))

checklist_stages = {
    "four_weeks": "timeline_four_weeks",
    "three_weeks": "timeline_three_weeks",
    "two_weeks": "timeline_two_weeks",
    "one_week": "timeline_one_week",
    "two_days": "timeline_two_days",
    "event_day": "timeline_event_day",
    "custom": "checklist_stage_custom",
}

if "checklist_tasks" not in st.session_state:
    st.session_state["checklist_tasks"] = []

with st.form("add_checklist_task_form"):
    task_description = st.text_input(
        t("checklist_task"),
        max_chars=300,
        key="new_checklist_task",
    )
    task_stage = st.selectbox(
        t("checklist_stage"),
        list(checklist_stages),
        format_func=lambda stage: translate(
            checklist_stages[stage], selected_language
        ),
        key="new_checklist_stage",
    )
    task_due_date = st.date_input(
        t("checklist_due_date"),
        value=None,
        key="new_checklist_due_date",
    )
    add_task = st.form_submit_button(t("add_checklist_task"))

if add_task:
    if not task_description.strip():
        st.error(t("checklist_task_required"))
    elif len(st.session_state["checklist_tasks"]) >= MAX_CHECKLIST_ITEMS:
        st.error(t("checklist_limit", maximum=MAX_CHECKLIST_ITEMS))
    else:
        st.session_state["checklist_tasks"].append({
            "id": uuid.uuid4().hex,
            "stage": task_stage,
            "task": task_description.strip(),
            "completed": False,
            "due_date": (
                task_due_date.isoformat() if task_due_date is not None else None
            ),
        })

for task in st.session_state["checklist_tasks"]:
    completion_key = f"checklist_completed_{task['id']}"
    text_key = f"checklist_text_{task['id']}"
    if completion_key in st.session_state:
        task["completed"] = st.session_state[completion_key]
    if text_key in st.session_state and st.session_state[text_key].strip():
        task["task"] = st.session_state[text_key].strip()

completed_tasks, total_tasks, completion = checklist_progress(
    st.session_state["checklist_tasks"]
)
st.progress(completion)
st.write(t(
    "checklist_progress",
    completed=completed_tasks,
    total=total_tasks,
    percent=f"{completion * 100:.0f}",
))

filter_labels = {
    "all": "filter_all",
    "pending": "filter_pending",
    "completed": "filter_completed",
}
checklist_filter = st.selectbox(
    t("checklist_filter"),
    list(filter_labels),
    format_func=lambda status: translate(
        filter_labels[status], selected_language
    ),
    key="checklist_filter",
)
visible_tasks = filter_checklist_tasks(
    st.session_state["checklist_tasks"],
    checklist_filter,
)

if not st.session_state["checklist_tasks"]:
    st.info(t("checklist_empty"))
else:
    updated_tasks = {
        task["id"]: dict(task)
        for task in st.session_state["checklist_tasks"]
    }
    for stage in checklist_stages:
        stage_tasks = [
            task for task in visible_tasks if task["stage"] == stage
        ]
        if not stage_tasks:
            continue
        st.subheader(t(checklist_stages[stage]))
        for task in stage_tasks:
            completion_key = f"checklist_completed_{task['id']}"
            text_key = f"checklist_text_{task['id']}"
            if completion_key not in st.session_state:
                st.session_state[completion_key] = task["completed"]
            if text_key not in st.session_state:
                st.session_state[text_key] = task["task"]
            task_col, completed_col = st.columns([4, 1])
            edited_task = task_col.text_input(
                t("checklist_task"),
                max_chars=300,
                key=text_key,
            )
            marked_complete = completed_col.checkbox(
                f"{edited_task or task['task']} — {t('checklist_completed')}",
                key=completion_key,
            )
            if edited_task.strip():
                updated_tasks[task["id"]]["task"] = edited_task.strip()
            else:
                st.error(t("checklist_task_required"))
            updated_tasks[task["id"]]["completed"] = marked_complete
            if is_task_overdue(task, date.today()):
                st.warning(
                    f"{t('checklist_overdue')}: {task['task']} "
                    f"({task['due_date']})"
                )
    st.session_state["checklist_tasks"] = list(updated_tasks.values())

st.header(f"📄 {t('download_plan')}", anchor="download-event-plan")

report = f"""
{t('report_title').upper()}

{t('pdf_overview').upper()}

{t('event_name')}: {event_name or t(event_type_labels[event_type])}
{t('event_type')}: {t(event_type_labels[event_type])}
{t('event_location')}: {location or t('not_specified')}
{t('guest_count')}: {guests}
{t('event_vibe')}: {t(event_vibe_labels[theme])}
{t('total_budget')}: ₹{budget:,.0f}
{t('budget_per_guest')}: ₹{budget / guests:,.0f}

{t('pdf_breakdown').upper()}
"""

for category, percentage in allocations.items():
    amount = budget * percentage
    report += f"\n{t(allocation_labels[category])}: ₹{amount:,.0f}"

report += f"\n\n{t('timeline').upper()}\n"

for timing, task in localized_timeline:
    report += f"\n{timing}: {task}"

report += f"\n\n{t('pdf_created')}"

st.download_button(
    label=f"📥 {t('download_plan')}",
    data=report,
    file_name="CelebrAI_Event_Plan.txt",
    mime="text/plain",
    width="stretch"
)


st.divider()

st.header(f"🤖 {t('ai_planner')}", anchor="ai-event-planner")

st.write(
    t("ai_planner_desc")
)

if st.button(f"✨ {t('generate_ai_plan')}", width="stretch"):

    prompt = f"""
    You are an expert event planner.

    Create a personalised event plan using these details:

    Event Name: {event_name or event_type}
    Event Type: {event_type}
    Location: {location or "Not specified"}
    Budget: ₹{budget:,.0f}
    Number of Guests: {guests}
    Decoration Theme: {theme}

    Include:
    1. Creative event concept.
    2. Decoration ideas.
    3. Food and menu suggestions.
    4. Budget breakdown in Indian Rupees.
    5. Entertainment and activities.
    6. Preparation checklist.
    7. Event-day schedule.
    8. Three unique ideas to make the event memorable.

    Keep the estimated expenditure within the stated budget.
    """

    try:
        client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
        with st.spinner(f"✨ {t('ai_loading')}"):

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

        if response.text:
            st.success(f"🎉 {t('ai_ready')}")
            st.markdown(response.text)
            st.caption(t("interface_translation_note"))

            st.download_button(
                label=f"📥 {t('download_ai_plan')}",
                data=response.text,
                file_name="CelebrAI_AI_Event_Plan.txt",
                mime="text/plain",
                width="stretch"
            )
        else:
            st.warning(t("ai_empty_response"))

    except (KeyError, StreamlitSecretNotFoundError):
        st.error(t("ai_missing_key"))

    except Exception as e:
        error_message = str(e)

        if "503" in error_message or "UNAVAILABLE" in error_message:
            st.warning(f"🌟 {t('ai_busy')}")

        elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            st.warning(f"⏳ {t('ai_quota')}")

        else:
            st.error(t("ai_failed"))

st.divider()

st.header(f"⏳ {t('countdown')}", anchor="celebration-countdown")

st.write(
    t("countdown_desc")
)

event_date = st.date_input(
    f"📅 {t('event_date')}",
    value=date.today(),
    min_value=date(2000, 1, 1),
    key="celebrai_event_date"
)

today = date.today()
days_left = (event_date - today).days

st.markdown(
    """
    <style>
    .countdown-card {
        background: linear-gradient(
            135deg,
            #211137,
            #673ab7,
            #b83280
        );
        padding: 35px 20px;
        border-radius: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 10px 35px rgba(167,139,250,0.25);
    }

    .countdown-number {
        font-size: 75px;
        font-weight: 800;
        color: #ffd782;
        animation: countdownGlow 2s ease-in-out infinite alternate;
    }

    .countdown-caption {
        font-size: 20px;
        color: white;
    }

    @keyframes countdownGlow {
        from {
            text-shadow: 0 0 5px #ffd782;
            transform: scale(1);
        }
        to {
            text-shadow: 0 0 25px #ff8fca;
            transform: scale(1.04);
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

if days_left > 0:
    st.metric(t("days_until"), f"{days_left}")
    st.info(t("countdown_future"))

elif days_left == 0:
    st.success(f"🎉🎂 {t('today_event')}")

else:
    st.info(t("past_event", days=-days_left))

st.caption(
    f"📅 {t('selected_date', date=event_date.strftime('%d/%m/%Y'))}"
)
st.divider()

st.header(f"💌 {t('invitation')}", anchor="invitation-studio")

st.write(
    t("invitation_desc")
)

# Invitation customisation
invite_title = st.text_input(
    t("invitation_title"),
    value=event_name or t(
        "example_event_title",
        event_type=t(event_type_labels[event_type]),
    ),
    key="invitation_title",
)

invite_date = st.date_input(
    t("invitation_date"),
    key="invitation_date"
)

invite_location = st.text_input(
    t("invitation_venue"),
    value=location,
    key="invitation_location"
)

invite_message = st.text_area(
    t("invitation_message"),
    value=t("invitation_default_message"),
    key="invitation_message",
)

invitation_style_labels = {
    "Royal Gold": "option_invite_gold",
    "Rose Romance": "option_invite_rose",
    "Midnight Purple": "option_invite_purple",
    "Emerald Elegance": "option_invite_emerald",
}
invite_style = st.selectbox(
    t("invitation_style"),
    list(invitation_style_labels),
    format_func=lambda option: translate(
        invitation_style_labels[option], selected_language
    ),
    key="invitation_design",
)

# Theme colours
invitation_themes = {
    "Royal Gold": {
        "background": (35, 20, 40),
        "accent": (255, 215, 130),
        "text": (255, 250, 235)
    },
    "Rose Romance": {
        "background": (65, 25, 45),
        "accent": (255, 170, 195),
        "text": (255, 240, 245)
    },
    "Midnight Purple": {
        "background": (25, 20, 65),
        "accent": (195, 170, 255),
        "text": (250, 245, 255)
    },
    "Emerald Elegance": {
        "background": (15, 50, 40),
        "accent": (175, 240, 195),
        "text": (240, 255, 245)
    }
}

if st.button(
    f"✨ {t('invitation_create')}",
    width="stretch"
):
    colors = invitation_themes[invite_style]

    width, height = 1000, 1200

    # Create a transparent canvas for the invitation
    image = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (45, 25, 955, 1175),
        fill=colors["background"],
        outline=colors["accent"],
        width=7
    )

    # Inner decorative oval border
    draw.ellipse(
        (65, 45, 935, 1155),
        outline=colors["accent"],
        width=2
    )

    try:
        title_font = ImageFont.truetype(
            r"C:\Windows\Fonts\georgia.ttf", 62
        )

        heading_font = ImageFont.truetype(
            r"C:\Windows\Fonts\georgiab.ttf", 34
        )

        body_font = ImageFont.truetype(
            r"C:\Windows\Fonts\arial.ttf", 27
        )

        small_font = ImageFont.truetype(
            r"C:\Windows\Fonts\arial.ttf", 22
        )

    except OSError:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    for ornament_x in (460, 500, 540):
        draw.polygon(
            [
                (ornament_x, 93),
                (ornament_x + 12, 105),
                (ornament_x, 117),
                (ornament_x - 12, 105),
            ],
            fill=colors["accent"],
        )

    def draw_centered(text, y, font, fill):
        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            ((width - text_width) / 2, y),
            text,
            font=font,
            fill=fill
        )

    draw_centered(
        t("invitation_greeting"),
        165,
        small_font,
        colors["text"]
    )

    draw_centered(
        t("invitation_event"),
        220,
        heading_font,
        colors["accent"]
    )

    # Decorative divider
    draw.line(
        (300, 285, 700, 285),
        fill=colors["accent"],
        width=3
    )

    title_lines = textwrap.wrap(
        invite_title.strip() or t("invitation_default_title"),
        width=23
    )[:2]

    title_y = 320

    for line in title_lines:
        draw_centered(
            line,
            title_y,
            title_font,
            colors["accent"]
        )
        title_y += 75


    draw_centered(
        t("invitation_join"),
        465,
        small_font,
        colors["text"]
    )

    message_lines = textwrap.wrap(
        invite_message.strip() or
        t("invitation_default_message"),
        width=43
    )[:4]

    message_y = 510

    for line in message_lines:
        draw_centered(
            line,
            message_y,
            body_font,
            colors["text"]
        )
        message_y += 43

    draw.line(
        (350, 705, 650, 705),
        fill=colors["accent"],
        width=2
    )

    draw_centered(
        t("invitation_date_label"),
        730,
        heading_font,
        colors["accent"]
    )

    draw_centered(
        invite_date.strftime("%d/%m/%Y"),
        780,
        body_font,
        colors["text"]
    )

    draw_centered(
        t("invitation_venue_label"),
        840,
        heading_font,
        colors["accent"]
    )

    venue_lines = textwrap.wrap(
        invite_location.strip() or t("venue_to_be_announced"),
        width=35
    )[:2]

    venue_y = 890

    for line in venue_lines:
        draw_centered(
            line,
            venue_y,
            body_font,
            colors["text"]
        )
        venue_y += 40

    draw_centered(
        "*  *  *",
        1010,
        heading_font,
        colors["accent"]
    )

    draw_centered(
        t("invitation_closing"),
        1055,
        small_font,
        colors["text"]
    )

    draw_centered(
        t("made_with"),
        1100,
        small_font,
        colors["accent"]
    )


    image_bytes = BytesIO()

    image.save(
        image_bytes,
        format="PNG"
    )

    png_data = image_bytes.getvalue()

    st.success(
        f"✨ {t('invitation_ready')}"
    )

    st.image(
        png_data,
        caption=t("invitation_image_caption"),
        width="stretch",
        alt=(
            t(
                "invitation_alt",
                title=invite_title.strip() or t("invitation_default_title"),
                date=invite_date.strftime("%d/%m/%Y"),
                venue=invite_location.strip() or t("venue_to_be_announced"),
            )
        ),
    )

    st.download_button(
        label=f"📥 {t('invitation_download')}",
        data=png_data,
        file_name="CelebrAI_Invitation.png",
        mime="image/png",
        width="stretch"
    )

    st.divider()

st.header(f"💰 {t('expense_tracker')}", anchor="expense-tracker")
st.write(f"{t('expense_desc')} ✨")

if "event_expenses" not in st.session_state:
    st.session_state.event_expenses = pd.DataFrame({
        "Expense": ["Venue", "Food & Catering", "Decoration"],
        "Category": ["Venue", "Food", "Decoration"],
        "Estimated Cost (₹)": [10000, 15000, 5000],
        "Actual Cost (₹)": [10000, 14000, 4500]
    })

expense_category_labels = {
    "Venue": "expense_category_venue",
    "Food": "expense_category_food",
    "Decoration": "expense_category_decoration",
    "Photography": "expense_category_photography",
    "Entertainment": "expense_category_entertainment",
    "Transport": "expense_category_transport",
    "Gifts": "expense_category_gifts",
    "Other": "expense_category_other",
}
localized_category_values = {
    category: t(label_key)
    for category, label_key in expense_category_labels.items()
}
localized_expenses = st.session_state.event_expenses.copy()
localized_expenses["Category"] = localized_expenses["Category"].map(
    lambda category: localized_category_values.get(category, category)
)

expense_budget = st.number_input(
    f"🎯 {t('set_budget')}",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="expense_tracker_budget"
)

st.subheader(f"📝 {t('manage_expenses')}")

edited_expenses = st.data_editor(
    localized_expenses,
    num_rows="dynamic",
    width="stretch",
    key="expense_editor",
    column_config={
        "Expense": st.column_config.TextColumn(
            t("expense_name"),
            required=True
        ),
        "Category": st.column_config.SelectboxColumn(
            t("category"),
            options=list(localized_category_values.values()),
            required=True
        ),
        "Estimated Cost (₹)": st.column_config.NumberColumn(
            t("estimated_cost"),
            min_value=0,
            format="₹%.2f"
        ),
        "Actual Cost (₹)": st.column_config.NumberColumn(
            t("actual_cost"),
            min_value=0,
            format="₹%.2f"
        )
    }
)

canonical_category_values = {
    localized: category
    for category, localized in localized_category_values.items()
}
edited_expenses["Category"] = edited_expenses["Category"].map(
    lambda category: canonical_category_values.get(category, category)
)
st.session_state.event_expenses = edited_expenses

expense_summary = calculate_expense_summary(edited_expenses, expense_budget)
estimated_total = expense_summary.estimated_total
actual_total = expense_summary.actual_total
remaining_budget = expense_summary.remaining_budget

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        f"🎯 {t('total_budget_metric')}",
        f"₹{expense_budget:,.0f}"
    )

with metric2:
    st.metric(
        f"💸 {t('actual_spending')}",
        f"₹{actual_total:,.0f}",
        delta=t(
            "budget_delta",
            amount=f"₹{actual_total - estimated_total:,.0f}",
        ),
        delta_color="inverse"
    )

with metric3:
    st.metric(
        f"💚 {t('remaining_budget')}",
        f"₹{remaining_budget:,.0f}"
    )

if actual_total > expense_budget:
    st.error(
        t("budget_exceeded", amount=f"₹{abs(remaining_budget):,.0f}")
    )
elif remaining_budget == 0:
    st.warning(t("budget_fully_used"))
elif budget_status(actual_total, expense_budget) == "approaching":
    st.warning(
        t(
            "budget_approaching",
            percent=f"{actual_total / expense_budget * 100:.1f}",
        )
    )
else:
    st.success(t("within_budget"))

# Budget usage
progress = min(actual_total / expense_budget, 1.0)

st.progress(
    progress,
    text=t("budget_progress", percent=f"{progress * 100:.1f}%")
)
st.caption(f"{t('remaining_budget')}: ₹{remaining_budget:,.0f}")


st.subheader(f"📊 {t('expense_analytics')}")

if not edited_expenses.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(f"#### {t('actual_by_category')}")
        category_totals = expense_summary.category_totals.rename(
            index=lambda category: (
                t(expense_category_labels[category])
                if category in expense_category_labels
                else category
            )
        )
        st.bar_chart(
            category_totals,
            alt=t("expense_category_chart_alt"),
        )
        category_table = (
            category_totals
            .rename("Actual Cost (₹)")
            .rename_axis(t("category"))
            .reset_index()
        )
        st.dataframe(
            category_table,
            hide_index=True,
            height="content",
            width="stretch",
            alt=t("expense_category_table_alt"),
        )

    with chart_col2:
        st.markdown(f"#### {t('estimate_vs_actual')}")
        st.bar_chart(
            expense_summary.comparison,
            alt=t("expense_comparison_chart_alt"),
        )
        st.dataframe(
            expense_summary.comparison.rename_axis("Expense").reset_index(),
            hide_index=True,
            height="content",
            width="stretch",
            alt=t("expense_comparison_table_alt"),
        )
else:
    st.info(t("empty_expenses"))

st.caption(
    t("budget_footer")
)
st.divider()

st.header(f"🎨 {t('theme_gallery')}", anchor="theme-gallery")
st.write(
    f"{t('theme_gallery_desc')} ✨"
)

event_gallery = {
    "👑 Royal Luxury": {
        "name_key": "gallery_royal_name",
        "heading_key": "gallery_royal_heading",
        "description_key": "gallery_royal_description",
        "background": "linear-gradient(135deg, #1a103d, #5b238a, #d4af37)",
        "colors": ["#2D1555", "#D4AF37", "#FFF4D6"],
        "decor": "👑 ✨ 🏰 🥂 💎"
    },
    "🌸 Rose Gold Romance": {
        "name_key": "gallery_rose_name",
        "heading_key": "gallery_rose_heading",
        "description_key": "gallery_rose_description",
        "background": "linear-gradient(135deg, #f7c5cc, #c77986, #7c3f58)",
        "colors": ["#C77986", "#F7C5CC", "#FFF0E8"],
        "decor": "🌸 💐 💗 🕯️ 🌹"
    },
    "🌊 Ocean Dream": {
        "name_key": "gallery_ocean_name",
        "heading_key": "gallery_ocean_heading",
        "description_key": "gallery_ocean_description",
        "background": "linear-gradient(135deg, #042f40, #087e8b, #65d6ce)",
        "colors": ["#042F40", "#087E8B", "#65D6CE"],
        "decor": "🌊 🐚 🐬 🫧 🪸"
    },
    "🌿 Emerald Elegance": {
        "name_key": "gallery_emerald_name",
        "heading_key": "gallery_emerald_heading",
        "description_key": "gallery_emerald_description",
        "background": "linear-gradient(135deg, #092b23, #176b4d, #b6c77b)",
        "colors": ["#092B23", "#176B4D", "#B6C77B"],
        "decor": "🌿 🌱 🌳 🌼 🍃"
    },
    "🎉 Colorful Carnival": {
        "name_key": "gallery_carnival_name",
        "heading_key": "gallery_carnival_heading",
        "description_key": "gallery_carnival_description",
        "background": "linear-gradient(135deg, #ff416c, #ff9a44, #7b2ff7)",
        "colors": ["#FF416C", "#FF9A44", "#7B2FF7"],
        "decor": "🎈 🎊 🎉 🎂 🪩"
    },
    "🌌 Midnight Galaxy": {
        "name_key": "gallery_galaxy_name",
        "heading_key": "gallery_galaxy_heading",
        "description_key": "gallery_galaxy_description",
        "background": "linear-gradient(135deg, #080820, #302b63, #7f53ac)",
        "colors": ["#080820", "#302B63", "#7F53AC"],
        "decor": "🌌 🌙 ⭐ ✨ 🪐"
    }
}

selected_gallery_theme = st.selectbox(
    f"✨ {t('choose_style')}",
    list(event_gallery.keys()),
    format_func=lambda option: translate(
        event_gallery[option]["name_key"], selected_language
    ),
    key="gallery_theme_choice"
)

selected_theme_data = event_gallery[selected_gallery_theme]

st.markdown(
    f"""
    <div style="
        background: {selected_theme_data['background']};
        padding: 45px 25px;
        border-radius: 25px;
        text-align: center;
        color: white;
        box-shadow: 0 10px 35px rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.3);
    ">
        <div aria-hidden="true" style="font-size: 38px; margin-bottom: 18px;">
            {selected_theme_data['decor']}
        </div>
        <div style="
            background: rgba(0, 0, 0, 0.68);
            border-radius: 16px;
            padding: 20px 16px;
        ">
        <h3 style="
            color: white;
            font-family: Georgia, serif;
            letter-spacing: 2px;
            font-size: 30px;
        ">
            {t(selected_theme_data['heading_key'])}
        </h3>
        <p style="font-size: 17px;">
            {t(selected_theme_data['description_key'])}
        </p>
        <div style="font-size: 24px; margin-top: 22px;">
            ✨ {t("gallery_tagline")} ✨
        </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.subheader(f"🎨 {t('color_palette')}")

palette_columns = st.columns(len(selected_theme_data["colors"]))

for index, colour in enumerate(selected_theme_data["colors"]):
    with palette_columns[index]:
        st.markdown(
            f"""
            <div style="
                background-color: {colour};
                height: 85px;
                border-radius: 15px;
                border: 2px solid rgba(128,128,128,0.3);
            "></div>
            <p style="text-align:center; font-weight:bold;">
                {colour}
            </p>
            """,
            unsafe_allow_html=True
        )

st.success(
    t(
        "theme_selected",
        theme=t(selected_theme_data["name_key"]),
    )
)
st.divider()

st.header(f"📄 {t('professional_plan')}", anchor="professional-event-plan")
st.write(t("professional_plan_desc"))

pdf_event_name = st.text_input(
    f"🎉 {t('pdf_event_name')}",
    value=t("pdf_default_event_name"),
    key="pdf_event_name"
)

pdf_event_type = st.selectbox(
    f"🎊 {t('pdf_event_type')}",
    list(event_type_labels),
    format_func=lambda option: translate(
        event_type_labels[option], selected_language
    ),
    key="pdf_event_type"
)

pdf_event_date = st.date_input(
    f"📅 {t('pdf_event_date')}",
    key="pdf_event_date"
)

pdf_location = st.text_input(
    f"📍 {t('pdf_event_location')}",
    key="pdf_event_location"
)

pdf_guests = st.number_input(
    f"👥 {t('pdf_guest_count')}",
    min_value=1,
    max_value=100000,
    value=100,
    key="pdf_guest_count"
)

pdf_budget = st.number_input(
    f"💰 {t('pdf_budget')}",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="pdf_event_budget"
)

if st.button(
    f"✨ {t('create_pdf')}",
    width="stretch",
    key="generate_event_pdf"
):
    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CelebrAI_Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=32,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6336A5"),
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        "CelebrAI_Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=17,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20
    )

    section_style = ParagraphStyle(
        "CelebrAI_Section",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#6336A5"),
        spaceBefore=15,
        spaceAfter=10
    )

    story = []

    story.append(Paragraph("CelebrAI", title_style))
    story.append(
        Paragraph(
            t("pdf_subtitle"),
            subtitle_style
        )
    )

    story.append(Paragraph(t("pdf_overview"), section_style))

    event_details = [
        [t("event_name"), escape(pdf_event_name)],
        [t("event_type"), t(event_type_labels[pdf_event_type])],
        [t("pdf_event_date_label"), pdf_event_date.strftime("%d/%m/%Y")],
        [t("event_location"), escape(pdf_location) if pdf_location else t("not_specified")],
        [t("guest_count"), f"{pdf_guests:,}"],
        [t("total_budget"), f"₹{pdf_budget:,.2f}"]
    ]

    details_table = Table(
        event_details,
        colWidths=[145, 330]
    )

    details_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEE6FA")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#42236B")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6CBE8")),
            ("PADDING", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(details_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph(t("pdf_breakdown"), section_style))

    budget_allocations = [
        [t("pdf_expense_category"), t("pdf_allocation"), t("pdf_amount")],
        [t("budget_venue"), "25%", f"₹{pdf_budget * 0.25:,.2f}"],
        [t("budget_catering"), "30%", f"₹{pdf_budget * 0.30:,.2f}"],
        [t("budget_decoration"), "15%", f"₹{pdf_budget * 0.15:,.2f}"],
        [t("budget_photography"), "10%", f"₹{pdf_budget * 0.10:,.2f}"],
        [t("budget_entertainment"), "10%", f"₹{pdf_budget * 0.10:,.2f}"],
        [t("budget_miscellaneous"), "10%", f"₹{pdf_budget * 0.10:,.2f}"],
        [t("total_budget_metric"), "100%", f"₹{pdf_budget:,.2f}"]
    ]

    budget_table = Table(
        budget_allocations,
        colWidths=[180, 125, 170]
    )

    budget_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6336A5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6CBE8")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EEE6FA")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
    )

    story.append(budget_table)
    story.append(Spacer(1, 25))
    story.append(Spacer(1, 20))

    story.append(
        Paragraph(t("pdf_expense_report"), section_style)
    )

    # Read expenses from the interactive expense tracker
    expense_data = [[
        t("expense_name"),
        t("category"),
        t("estimated_cost"),
        t("actual_cost"),
    ]]

    if "event_expenses" in st.session_state:
        current_expenses = st.session_state.event_expenses

        expense_columns = [
            "Expense",
            "Category",
            "Estimated Cost (₹)",
            "Actual Cost (₹)",
        ]
        for expense, category, estimated, actual in current_expenses[
            expense_columns
        ].itertuples(index=False, name=None):
            expense_data.append([
                "" if pd.isna(expense) else str(expense),
                (
                    ""
                    if pd.isna(category)
                    else t(expense_category_labels[category])
                    if category in expense_category_labels
                    else str(category)
                ),
                f"{0 if pd.isna(estimated) else float(estimated):,.2f}",
                f"{0 if pd.isna(actual) else float(actual):,.2f}",
            ])
    else:
        expense_data.append([t("pdf_no_expenses"), "-", "-", "-"])

    expense_table = Table(
        expense_data,
        colWidths=[130, 100, 110, 110],
        repeatRows=1
    )

    expense_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6336A5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6CBE8")),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(expense_table)

    story.append(
        Paragraph(
            t("pdf_planning_tip"),
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            t("pdf_created"),
            subtitle_style
        )
    )

    document.build(story)

    pdf_buffer.seek(0)

    st.success(f"🎉 {t('pdf_ready')}")

    st.download_button(
        label=f"📥 {t('download_plan')}",
        data=pdf_buffer.getvalue(),
        file_name="CelebrAI_Event_Plan.pdf",
        mime="application/pdf",
        width="stretch",
        key="download_event_pdf"
    )
    st.divider()

st.header(
    f"🤖 {t('theme_recommendations')}",
    anchor="ai-theme-recommendations",
)

st.write(
    t("theme_recommendations_desc")
)

recommendation_event = st.selectbox(
    f"🎉 {t('event_type')}",
    [
        *event_type_labels,
    ],
    format_func=lambda option: translate(
        event_type_labels[option], selected_language
    ),
    key="recommendation_event"
)

recommendation_budget = st.number_input(
    f"💰 {t('budget')}",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="recommendation_budget"
)

recommendation_guests = st.number_input(
    f"👥 {t('guest_count')}",
    min_value=1,
    max_value=100000,
    value=100,
    key="recommendation_guests"
)

recommendation_vibe_labels = {
    "Royal and luxurious": "option_royal",
    "Traditional Indian": "option_traditional",
    "Elegant and minimal": "option_minimal",
    "Colorful and fun": "option_colorful",
    "Modern and futuristic": "option_futuristic",
    "Nature-inspired and peaceful": "option_nature",
}
recommendation_vibe = st.selectbox(
    f"✨ {t('preferred_atmosphere')}",
    [
        *recommendation_vibe_labels,
    ],
    format_func=lambda option: translate(
        recommendation_vibe_labels[option], selected_language
    ),
    key="recommendation_vibe"
)

if st.button(
    f"✨ {t('recommend_theme')}",
    width="stretch",
    key="recommend_theme_button"
):
    recommendation_prompt = f"""
    You are CelebrAI, a professional event planner.

    Recommend the best event theme using these details:

    Event type: {recommendation_event}
    Budget: ₹{recommendation_budget:,}
    Expected guests: {recommendation_guests}
    Preferred atmosphere: {recommendation_vibe}

    Provide:
    1. A creative theme name.
    2. A description of the decorations and atmosphere.
    3. A suitable colour palette.
    4. Decoration ideas that fit the budget.
    5. Lighting and photography suggestions.
    6. Three practical tips to make the event memorable.

    Keep the recommendations realistic for the stated budget.
    Use clear headings, friendly language, and attractive formatting.
    """

    try:
        client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
        with st.spinner(
            f"✨ {t('theme_loading')}"
        ):
            recommendation_response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=recommendation_prompt
            )

        if recommendation_response.text:
            recommendation_text = recommendation_response.text

            st.success(f"🎉 {t('ai_theme_ready')}")
            st.markdown(recommendation_text)
            st.caption(t("interface_translation_note"))

            st.download_button(
                f"📥 {t('download_theme_recommendation')}",
                data=recommendation_text,
                file_name="CelebrAI_Theme_Recommendation.txt",
                mime="text/plain",
                width="stretch",
                key="download_theme_recommendation"
            )

        else:
            st.warning(t("recommendation_empty"))

    except (KeyError, StreamlitSecretNotFoundError):
        st.error(t("ai_missing_key"))

    except Exception as e:
        error_message = str(e)

        if "503" in error_message or "UNAVAILABLE" in error_message:
            st.warning(t("ai_busy"))

        elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            st.warning(t("ai_quota"))

        else:
            st.error(t("ai_recommendation_failed"))

        st.divider()
