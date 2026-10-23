import streamlit as st
import pandas as pd
from google import genai
import os
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
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

api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)

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
    }
    </style>

    <div class="celebrai-welcome">
        <h1>✨ Welcome to CelebrAI ✨</h1>
        <p>Your celebration. Your imagination. Our AI.</p>
        <p>
            Plan beautiful events, manage your budget,
            create invitations and discover unforgettable themes.
        </p>
        <div style="font-size: 30px; margin-top: 15px;">
            🎉 💜 🎂 💐 🎊
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.subheader("🌟 Explore Your Celebration Studio")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown(
        """
        <div class="celebrai-feature">
            <div style="font-size:32px;">🤖</div>
            <h4>AI Event Planner</h4>
            <p>Discover personalized event ideas.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature_col2:
    st.markdown(
        """
        <div class="celebrai-feature">
            <div style="font-size:32px;">💰</div>
            <h4>Smart Budget</h4>
            <p>Track expenses and manage costs.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature_col3:
    st.markdown(
        """
        <div class="celebrai-feature">
            <div style="font-size:32px;">💌</div>
            <h4>Invitation Studio</h4>
            <p>Create personalized invitations.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.info(
    "💡 Tip: Scroll through CelebrAI to explore the AI planner, "
    "event checklist, countdown, invitation designer, "
    "expense tracker and theme gallery."
)

st.set_page_config(
    page_title="CelebrAI | Smart Event Planner",
    page_icon="✨",
    layout="wide"
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
    content: "✦     ✧        ✦        ✧     ✦";
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
    background-color: rgba(255,255,255,.07);
    border: 1px solid var(--border);
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
</style>
""", unsafe_allow_html=True)
# Visual theme selector
st.sidebar.title("🎨 Customize Your Experience")

selected_theme = st.sidebar.selectbox(
    "Choose your theme",
    [
        "Royal Purple",
        "Rose Gold",
        "Ocean Dream",
        "Emerald Elegance",
        "Midnight Galaxy"
    ]
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
    }}
    h1, h2, h3 {{
        color: {accent_color} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
font_choice = st.sidebar.selectbox(
    "Choose your typography",
    [
        "Modern",
        "Elegant",
        "Playful",
        "Futuristic"
    ]
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
st.markdown("""
<div class="hero">
    <div class="hero-title">✨ CelebrAI</div>
    <h3>Every Celebration Deserves a Little Magic</h3>
    <p>Design unforgettable moments with your personal AI event planner.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

st.subheader("🎊 Choose Your Celebration")

col1, col2, col3, col4 = st.columns(4)

events = [
    ("💍", "Wedding"),
    ("🎂", "Birthday"),
    ("🎓", "College Fest"),
    ("🎉", "Anniversary")
]

for col, (emoji, name) in zip(
    [col1, col2, col3, col4], events
):
    with col:
        st.markdown(
            f'<div class="event-card">'
            f'<h2>{emoji}</h2><b>{name}</b></div>',
            unsafe_allow_html=True
        )

st.write("")
st.divider()

st.subheader("💫 Design Your Dream Event")

event_type = st.selectbox(
    "What are you celebrating?",
    ["Wedding", "Birthday", "College Fest", "Anniversary",
     "Community Celebration"]
)

event_name = st.text_input(
    "Event name",
    placeholder="e.g. My Dream Birthday"
)

location = st.text_input(
    "Event location",
    placeholder="e.g. Chennai"
)

budget = st.slider(
    "💰 Your budget (₹)",
    min_value=5000,
    max_value=500000,
    value=50000,
    step=5000
)

guests = st.number_input(
    "👥 Number of guests",
    min_value=1,
    max_value=10000,
    value=100
)

theme = st.selectbox(
    "🎨 Choose your vibe",
    ["Royal & Luxurious", "Traditional Indian",
     "Elegant & Minimal", "Colorful & Fun",
     "Modern & Futuristic"]
)

st.metric("💎 Budget per guest", f"₹{budget / guests:,.0f}")

st.write("### 💰 Live Budget Preview")

allocations = {
    "Venue": 0.25,
    "Catering": 0.30,
    "Decoration": 0.15,
    "Photography": 0.10,
    "Entertainment": 0.10,
    "Miscellaneous": 0.10
}

for category, percentage in allocations.items():
    amount = budget * percentage
    st.write(f"**{category}** — ₹{amount:,.0f}")
    st.progress(percentage)

if st.button("✨ Generate My Dream Event", use_container_width=True):
    st.balloons()

    st.success("Your celebration concept is ready!")

    st.markdown("## 👑 Your Event Preview")

    st.write(f"**Event:** {event_name or event_type}")
    st.write(f"**Type:** {event_type}")
    st.write(f"**Location:** {location or 'Not specified'}")
    st.write(f"**Guests:** {guests}")
    st.write(f"**Theme:** {theme}")
    st.write(f"**Total budget:** ₹{budget:,.0f}")

    st.info(
        "This is your initial event preview. "
        "Next, we'll connect Gemini AI to generate "
        "personalized ideas, schedules and recommendations."
    )
st.divider()

st.header("🎨 Your Celebration Preview")

theme_visuals = {
    "Royal & Luxurious": {
        "emoji": "👑",
        "description": "Elegant gold decorations and luxurious details",
        "color": "#b8860b"
    },
    "Traditional Indian": {
        "emoji": "🪷",
        "description": "Traditional decorations, flowers, and cultural charm",
        "color": "#c2410c"
    },
    "Elegant & Minimal": {
        "emoji": "🤍",
        "description": "Minimal decorations with timeless elegance",
        "color": "#64748b"
    },
    "Colorful & Fun": {
        "emoji": "🎊",
        "description": "Bright colors, playful decorations, and joyful energy",
        "color": "#db2777"
    },
    "Modern & Futuristic": {
        "emoji": "🚀",
        "description": "Modern lighting and futuristic decorative elements",
        "color": "#7c3aed"
    }
}

visual = theme_visuals[theme]

st.markdown(
    f"""
    <div style="
        background: linear-gradient(135deg, {visual['color']}55, #211137);
        border: 1px solid {visual['color']};
        border-radius: 24px;
        padding: 30px;
        text-align: center;
    ">
        <div style="font-size: 55px;">{visual['emoji']}</div>
        <h2>{event_name or event_type}</h2>
        <p>{visual['description']}</p>
        <p>📍 {location or 'Location not specified'}</p>
        <p>👥 {guests:,} guests</p>
        <h3>₹{budget:,.0f}</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "✨ Your preview updates automatically when you change your event details."
)
st.divider()

st.markdown(
    "<center>✨ CelebrAI | Crafted for unforgettable moments ✨</center>",
    unsafe_allow_html=True
)
st.divider()

st.header("📅 Event Preparation Timeline")

timeline = [
    ("4 weeks before", "Finalize the budget and book the venue"),
    ("3 weeks before", "Confirm catering and decorations"),
    ("2 weeks before", "Arrange photography and entertainment"),
    ("1 week before", "Confirm guest list and invitations"),
    ("2 days before", "Reconfirm vendors and arrangements"),
    ("Event day", "Enjoy your celebration! 🎉")
]

for timing, task in timeline:
    with st.expander(f"🗓️ {timing}"):
        st.write(task)
        st.divider()

st.header("📄 Download Your Event Plan")

report = f"""
CELEBRAI — CELEBRATION & EVENT PLANNER
======================================

EVENT DETAILS

Event Name: {event_name or event_type}
Event Type: {event_type}
Location: {location or 'Not specified'}
Number of Guests: {guests}
Theme: {theme}
Total Budget: Rs. {budget:,.0f}
Budget Per Guest: Rs. {budget / guests:,.0f}

SUGGESTED BUDGET BREAKDOWN
"""

for category, percentage in allocations.items():
    amount = budget * percentage
    report += f"\n{category}: Rs. {amount:,.0f}"

report += "\n\nEVENT PREPARATION TIMELINE\n"

for timing, task in timeline:
    report += f"\n{timing}: {task}"

report += "\n\nCreated with CelebrAI — Every Celebration Deserves a Little Magic!"

st.download_button(
    label="📥 Download My Event Plan",
    data=report,
    file_name="CelebrAI_Event_Plan.txt",
    mime="text/plain",
    use_container_width=True
)


st.divider()

st.header("🤖 Your Personal AI Event Planner")

st.write(
    "Let Gemini AI create a personalised celebration plan "
    "based on your event details!"
)

if st.button("✨ Generate My AI Event Plan", use_container_width=True):

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
        with st.spinner("✨ Gemini is planning your celebration..."):

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

        if response.text:
            st.success("🎉 Your AI event plan is ready!")
            st.markdown(response.text)

            st.download_button(
                label="📥 Download My AI Event Plan",
                data=response.text,
                file_name="CelebrAI_AI_Event_Plan.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.warning("Gemini returned an empty response. Try again.")

    except Exception as e:
        error_message = str(e)

        if "503" in error_message or "UNAVAILABLE" in error_message:
            st.warning(
                "🌟 Gemini is temporarily busy. Wait a few minutes "
                "and try again."
            )

        elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            st.warning(
                "⏳ API quota or rate limit reached. "
                "Check your Gemini API usage."
            )

        else:
            st.error("We couldn't generate your AI event plan.")
            st.caption(f"Technical details: {error_message}")

# =====================================
# EVENT COUNTDOWN
# =====================================

st.divider()

st.header("⏳ Your Celebration Countdown")

st.write(
    "Every unforgettable moment begins with a countdown! ✨"
)

event_date = st.date_input(
    "📅 When is your celebration?",
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

    st.markdown(
        f"""
        <div class="countdown-card">
            <div style="font-size:45px;">🎊✨🎉</div>
            <div class="countdown-number">{days_left}</div>
            <div class="countdown-caption">
                DAYS UNTIL YOUR CELEBRATION!
            </div>
            <p style="color:#ffd782;">
                Your special moment is getting closer!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

elif days_left == 0:

    st.balloons()

    st.success(
        "🎉🎂 TODAY IS YOUR SPECIAL DAY! "
        "Enjoy every magical moment!"
    )

else:

    st.info(
        f"✨ Your selected event date was {-days_left} "
        "days ago. Choose a future date to start a new countdown."
    )

st.caption(
    f"📅 Selected event date: {event_date.strftime('%d %B %Y')}"
)
st.divider()

st.header("💌 Digital Invitation Designer")

st.write(
    "Create a beautiful personalised invitation "
    "for your unforgettable celebration!"
)

# Invitation customisation
invite_title = st.text_input(
    "Invitation title",
    value=event_name or f"My {event_type}"
)

invite_date = st.date_input(
    "Invitation date",
    key="invitation_date"
)

invite_location = st.text_input(
    "Invitation venue",
    value=location,
    key="invitation_location"
)

invite_message = st.text_area(
    "Your invitation message",
    value="Join us for a beautiful celebration filled with "
          "happiness, laughter and unforgettable memories!"
)

invite_style = st.selectbox(
    "Choose invitation design",
    [
        "Royal Gold",
        "Rose Romance",
        "Midnight Purple",
        "Emerald Elegance"
    ]
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
    "✨ Create My Invitation",
    use_container_width=True
):

    colors = invitation_themes[invite_style]

    width, height = 1000, 1200

    image = Image.new(
        "RGB",
        (width, height),
        colors["background"]
    )

    draw = ImageDraw.Draw(image)

    # Decorative border
    draw.rounded_rectangle(
        (35, 35, 965, 1165),
        radius=35,
        outline=colors["accent"],
        width=5
    )

    draw.rounded_rectangle(
        (55, 55, 945, 1145),
        radius=30,
        outline=colors["accent"],
        width=2
    )

    # Load fonts
    try:
        title_font = ImageFont.truetype(
            r"C:\Windows\Fonts\georgia.ttf", 64
        )

        heading_font = ImageFont.truetype(
            r"C:\Windows\Fonts\georgiab.ttf", 40
        )

        body_font = ImageFont.truetype(
            r"C:\Windows\Fonts\arial.ttf", 30
        )

        small_font = ImageFont.truetype(
            r"C:\Windows\Fonts\arial.ttf", 25
        )

    except OSError:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Helper: centre text horizontally
    def draw_centered(text, y, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        draw.text(
            ((width - text_width) / 2, y),
            text,
            font=font,
            fill=fill
        )

    # Decorative symbols
    draw_centered("*  *  *  *  *", 100, heading_font,
                  colors["accent"])

    draw_centered(
        "YOU ARE INVITED",
        200,
        body_font,
        colors["text"]
    )

    draw_centered(
        invite_title[:35],
        300,
        title_font,
        colors["accent"]
    )

    draw_centered(
        "A SPECIAL CELEBRATION",
        420,
        small_font,
        colors["text"]
    )

    draw.line(
        (200, 485, 800, 485),
        fill=colors["accent"],
        width=3
    )

    # Invitation message
    message_lines = textwrap.wrap(
        invite_message,
        width=42
    )[:5]

    y = 530

    for line in message_lines:
        draw_centered(
            line,
            y,
            body_font,
            colors["text"]
        )
        y += 48

    # Event details
    y += 45

    draw_centered(
        "DATE",
        y,
        heading_font,
        colors["accent"]
    )

    draw_centered(
        invite_date.strftime("%d %B %Y"),
        y + 55,
        body_font,
        colors["text"]
    )

    draw_centered(
        "VENUE",
        y + 125,
        heading_font,
        colors["accent"]
    )

    venue_lines = textwrap.wrap(
        invite_location or "Venue to be announced",
        width=40
    )[:2]

    venue_y = y + 180

    for line in venue_lines:
        draw_centered(
            line,
            venue_y,
            body_font,
            colors["text"]
        )
        venue_y += 45

    draw_centered(
        "WE LOOK FORWARD TO CELEBRATING WITH YOU!",
        1020,
        small_font,
        colors["accent"]
    )

    draw_centered(
        "MADE WITH CELEBRAI",
        1080,
        small_font,
        colors["text"]
    )

    # Convert image to PNG bytes
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")

    png_data = image_bytes.getvalue()

    st.success("Your invitation is ready!")

    st.image(
        png_data,
        caption="Your personalised CelebrAI invitation",
        use_container_width=True
    )

    st.download_button(
        label="📥 Download Invitation as PNG",
        data=png_data,
        file_name="CelebrAI_Invitation.png",
        mime="image/png",
        use_container_width=True
    )
    st.divider()

st.header("💰 Smart Event Expense Tracker")
st.write("Track your event spending and keep your celebration within budget! ✨")

if "event_expenses" not in st.session_state:
    st.session_state.event_expenses = pd.DataFrame({
        "Expense": ["Venue", "Food & Catering", "Decoration"],
        "Category": ["Venue", "Food", "Decoration"],
        "Estimated Cost (₹)": [10000, 15000, 5000],
        "Actual Cost (₹)": [10000, 14000, 4500]
    })

expense_budget = st.number_input(
    "🎯 Set your total event budget (₹)",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="expense_tracker_budget"
)

st.subheader("📝 Manage Your Expenses")

edited_expenses = st.data_editor(
    st.session_state.event_expenses,
    num_rows="dynamic",
    use_container_width=True,
    key="expense_editor",
    column_config={
        "Expense": st.column_config.TextColumn(
            "Expense Name",
            required=True
        ),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=[
                "Venue",
                "Food",
                "Decoration",
                "Photography",
                "Entertainment",
                "Transport",
                "Gifts",
                "Other"
            ],
            required=True
        ),
        "Estimated Cost (₹)": st.column_config.NumberColumn(
            "Estimated Cost (₹)",
            min_value=0,
            format="₹%.2f"
        ),
        "Actual Cost (₹)": st.column_config.NumberColumn(
            "Actual Cost (₹)",
            min_value=0,
            format="₹%.2f"
        )
    }
)

st.session_state.event_expenses = edited_expenses

estimated_total = edited_expenses["Estimated Cost (₹)"].fillna(0).sum()
actual_total = edited_expenses["Actual Cost (₹)"].fillna(0).sum()

remaining_budget = expense_budget - actual_total

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        "🎯 Total Budget",
        f"₹{expense_budget:,.0f}"
    )

with metric2:
    st.metric(
        "💸 Actual Spending",
        f"₹{actual_total:,.0f}",
        delta=f"₹{actual_total - estimated_total:,.0f} vs estimate",
        delta_color="inverse"
    )

with metric3:
    st.metric(
        "💚 Budget Remaining",
        f"₹{remaining_budget:,.0f}"
    )

if actual_total > expense_budget:
    st.error("🚨 Budget exceeded! Consider reducing some expenses.")
else:
    st.success("🎉 Great! Your spending is within your budget.")

progress = min(actual_total / expense_budget, 1.0)
st.progress(progress, text=f"{progress * 100:.1f}% of your budget used")

st.subheader("📊 Expense Analytics")

if not edited_expenses.empty:
    chart_data = edited_expenses.copy()

    chart_data["Actual Cost (₹)"] = (
        chart_data["Actual Cost (₹)"].fillna(0)
    )

    category_totals = chart_data.groupby("Category")[
        "Actual Cost (₹)"
    ].sum()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("**Spending by Category**")
        st.bar_chart(category_totals)

    with chart_col2:
        st.write("**Estimated vs Actual Costs**")
        comparison = chart_data.set_index("Expense")[
            ["Estimated Cost (₹)", "Actual Cost (₹)"]
        ].fillna(0)

        st.bar_chart(comparison)

st.caption(
    "✨ CelebrAI helps you plan beautiful celebrations without losing track of your budget."
)
st.divider()

st.header("🎨 Discover Your Dream Event Theme")
st.write(
    "Explore beautiful celebration styles and find the perfect "
    "atmosphere for your special day! ✨"
)

event_gallery = {
    "👑 Royal Luxury": {
        "background": "linear-gradient(135deg, #1a103d, #5b238a, #d4af37)",
        "heading": "A ROYAL CELEBRATION",
        "description": "Golden elegance, grand decorations and luxurious details.",
        "colors": ["#2D1555", "#D4AF37", "#FFF4D6"],
        "decor": "👑 ✨ 🏰 🥂 💎"
    },
    "🌸 Rose Gold Romance": {
        "background": "linear-gradient(135deg, #f7c5cc, #c77986, #7c3f58)",
        "heading": "LOVE IN EVERY DETAIL",
        "description": "Romantic flowers, soft lighting and rose-gold elegance.",
        "colors": ["#C77986", "#F7C5CC", "#FFF0E8"],
        "decor": "🌸 💐 💗 🕯️ 🌹"
    },
    "🌊 Ocean Dream": {
        "background": "linear-gradient(135deg, #042f40, #087e8b, #65d6ce)",
        "heading": "A BREATHTAKING ESCAPE",
        "description": "Refreshing ocean colours and a cool, contemporary vibe.",
        "colors": ["#042F40", "#087E8B", "#65D6CE"],
        "decor": "🌊 🐚 🐬 🫧 🪸"
    },
    "🌿 Emerald Elegance": {
        "background": "linear-gradient(135deg, #092b23, #176b4d, #b6c77b)",
        "heading": "NATURE MEETS ELEGANCE",
        "description": "Lush greenery, natural beauty and peaceful celebrations.",
        "colors": ["#092B23", "#176B4D", "#B6C77B"],
        "decor": "🌿 🌱 🌳 🌼 🍃"
    },
    "🎉 Colorful Carnival": {
        "background": "linear-gradient(135deg, #ff416c, #ff9a44, #7b2ff7)",
        "heading": "LET THE PARTY BEGIN!",
        "description": "Vibrant colours, joyful decorations and energetic fun.",
        "colors": ["#FF416C", "#FF9A44", "#7B2FF7"],
        "decor": "🎈 🎊 🎉 🎂 🪩"
    },
    "🌌 Midnight Galaxy": {
        "background": "linear-gradient(135deg, #080820, #302b63, #7f53ac)",
        "heading": "A NIGHT AMONG THE STARS",
        "description": "Magical lighting, cosmic colours and a futuristic atmosphere.",
        "colors": ["#080820", "#302B63", "#7F53AC"],
        "decor": "🌌 🌙 ⭐ ✨ 🪐"
    }
}

selected_gallery_theme = st.selectbox(
    "✨ Choose a celebration style",
    list(event_gallery.keys()),
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
        <div style="font-size: 38px; margin-bottom: 18px;">
            {selected_theme_data['decor']}
        </div>
        <h1 style="
            color: white;
            font-family: Georgia, serif;
            letter-spacing: 2px;
            font-size: 30px;
        ">
            {selected_theme_data['heading']}
        </h1>
        <p style="font-size: 17px;">
            {selected_theme_data['description']}
        </p>
        <div style="font-size: 24px; margin-top: 22px;">
            ✨ YOUR SPECIAL MOMENT STARTS HERE ✨
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.subheader("🎨 Your Theme Colour Palette")

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
    f"Your selected style is **{selected_gallery_theme}**. "
    "Try another theme to preview a different celebration atmosphere!"
)
st.divider()

st.header("📄 Your Professional Event Plan")
st.write(
    "Create a shareable PDF report for your celebration "
    "and keep all your important details together."
)

pdf_event_name = st.text_input(
    "🎉 Event name for PDF",
    value="My Dream Celebration",
    key="pdf_event_name"
)

pdf_event_type = st.selectbox(
    "🎊 Event type for PDF",
    [
        "Wedding",
        "Birthday",
        "College Fest",
        "Anniversary",
        "Community Celebration"
    ],
    key="pdf_event_type"
)

pdf_event_date = st.date_input(
    "📅 Event date for PDF",
    key="pdf_event_date"
)

pdf_location = st.text_input(
    "📍 Event location for PDF",
    key="pdf_event_location"
)

pdf_guests = st.number_input(
    "👥 Expected number of guests",
    min_value=1,
    max_value=100000,
    value=100,
    key="pdf_guest_count"
)

pdf_budget = st.number_input(
    "💰 Total event budget (₹)",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="pdf_event_budget"
)

if st.button(
    "✨ Generate My Event Plan PDF",
    use_container_width=True,
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
            "YOUR PERSONAL CELEBRATION PLANNER",
            subtitle_style
        )
    )

    story.append(Paragraph("Event Overview", section_style))

    event_details = [
        ["Event Name", pdf_event_name],
        ["Event Type", pdf_event_type],
        ["Event Date", pdf_event_date.strftime("%d %B %Y")],
        ["Location", pdf_location if pdf_location else "Not specified"],
        ["Expected Guests", f"{pdf_guests:,}"],
        ["Total Budget", f"Rs. {pdf_budget:,.2f}"]
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

    story.append(Paragraph("Suggested Budget Breakdown", section_style))

    budget_allocations = [
        ["Expense Category", "Suggested Allocation", "Amount"],
        ["Venue", "25%", f"Rs. {pdf_budget * 0.25:,.2f}"],
        ["Food & Catering", "30%", f"Rs. {pdf_budget * 0.30:,.2f}"],
        ["Decoration", "15%", f"Rs. {pdf_budget * 0.15:,.2f}"],
        ["Photography", "10%", f"Rs. {pdf_budget * 0.10:,.2f}"],
        ["Entertainment", "10%", f"Rs. {pdf_budget * 0.10:,.2f}"],
        ["Miscellaneous", "10%", f"Rs. {pdf_budget * 0.10:,.2f}"],
        ["TOTAL", "100%", f"Rs. {pdf_budget:,.2f}"]
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
        Paragraph("Actual Expense Tracker Report", section_style)
    )

    # Read expenses from the interactive expense tracker
    expense_data = [["Expense", "Category", "Estimated (Rs.)", "Actual (Rs.)"]]

    if "event_expenses" in st.session_state:
        current_expenses = st.session_state.event_expenses

        for _, row in current_expenses.iterrows():
            expense_data.append([
                str(row.get("Expense", "")),
                str(row.get("Category", "")),
                f"{float(row.get('Estimated Cost (₹)', 0) or 0):,.2f}",
                f"{float(row.get('Actual Cost (₹)', 0) or 0):,.2f}"
            ])
    else:
        expense_data.append(["No expenses entered", "-", "-", "-"])

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
            "Planning tip: Keep a small emergency fund for unexpected expenses "
            "and update your spending as bookings are confirmed.",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "Created with CelebrAI | Make every celebration unforgettable!",
            subtitle_style
        )
    )

    document.build(story)

    pdf_buffer.seek(0)

    st.success("🎉 Your event plan PDF is ready!")

    st.download_button(
        label="📥 Download Your Event Plan",
        data=pdf_buffer.getvalue(),
        file_name="CelebrAI_Event_Plan.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="download_event_pdf"
    )
    st.divider()

st.header("🤖 AI-Powered Theme Recommendations")

st.write(
    "Let CelebrAI suggest a celebration theme tailored to your event, "
    "budget, and guests!"
)

recommendation_event = st.selectbox(
    "🎉 What are you celebrating?",
    [
        "Wedding",
        "Birthday",
        "College Fest",
        "Anniversary",
        "Community Celebration"
    ],
    key="recommendation_event"
)

recommendation_budget = st.number_input(
    "💰 Your budget (₹)",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000,
    key="recommendation_budget"
)

recommendation_guests = st.number_input(
    "👥 Number of guests",
    min_value=1,
    max_value=100000,
    value=100,
    key="recommendation_guests"
)

recommendation_vibe = st.selectbox(
    "✨ Choose your preferred atmosphere",
    [
        "Royal and luxurious",
        "Traditional Indian",
        "Elegant and minimal",
        "Colorful and fun",
        "Modern and futuristic",
        "Nature-inspired and peaceful"
    ],
    key="recommendation_vibe"
)

if st.button(
    "✨ Recommend My Perfect Theme",
    use_container_width=True,
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
        with st.spinner(
            "✨ CelebrAI is designing your perfect celebration..."
        ):
            recommendation_response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=recommendation_prompt
            )
            result = st.write_stream(
        chunk.text
        for chunk in response
        if chunk.text
    )

        if recommendation_response.text:
            st.success("🎉 Your personalized theme recommendation is ready!")

            st.markdown(recommendation_response.text)

            st.download_button(
                "📥 Download Theme Recommendation",
                data=recommendation_response.text,
                file_name="CelebrAI_Theme_Recommendation.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_theme_recommendation"
            )
        else:
            st.warning(
                "The AI returned an empty response. Please try again."
            )

    except Exception as e:
        error_message = str(e)

        if "503" in error_message or "UNAVAILABLE" in error_message:
            st.warning(
                "Gemini is temporarily busy. Please wait a little and retry."
            )
        elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            st.warning(
                "The AI request limit may have been reached. "
                "Please try again later."
            )
        else:
            st.error("Unable to generate a recommendation.")
            st.caption(f"Technical details: {error_message}")
            st.divider()