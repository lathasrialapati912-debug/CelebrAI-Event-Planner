# 🎉 Celebration & Event Planner

### ✨ Plan Your Perfect Celebration with AI

Celebration & Event Planner is an interactive web application designed to make organizing special occasions easier, smarter, and more enjoyable. It uses Google's Gemini AI to help users generate personalized event plans through a visually engaging interface.

## 🌟 Features

* 🤖 **AI-Powered Event Planning** — Generate personalized event plans using Google Gemini AI.
* 🎨 **Interactive Themes** — Explore attractive designs and visual styles.
* 🎂 **Multiple Celebrations** — Plan special occasions according to your needs.
* 💰 **Budget-Friendly Planning** — Organize your event based on your budget and preferences.
* ✅ **Event Checklist** — Add and edit tasks, group them by planning stage, and track completion and overdue items.
* 💾 **Plan Backups** — Download and restore validated JSON backups for event details, preferences, expenses, invitations, and checklist progress.
* 🌐 **Multilingual Interface** — Switch the application interface among English, Telugu, Hindi, Tamil, Kannada, French, German, Spanish, Japanese, Korean, Chinese, and Arabic.
* ✨ **Interactive User Interface** — Enjoy a modern and user-friendly experience.
* ♿ **Accessibility support** — Keyboard-visible focus, reduced-motion support, and text alternatives for expense charts.
* 🌐 **Live Web Application** — Access the application online through Streamlit Community Cloud.

## 🛠️ Technologies Used

* Python
* Streamlit
* Google Gemini API
* Git
* GitHub

## 🚀 Live Demo

**Try the application:**

Add your deployed Streamlit application URL here.

## 💻 Installation and Setup

Follow these steps to run the application on your computer.

### 1. Clone the Repository

```bash
git clone https://github.com/lathasrialapati912-debug/CelebrAI-Event-Planner.git
```

### 2. Navigate to the Project Folder

```bash
cd "event planner"
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment

For Windows:

```bash
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Your Gemini API Key

For local development, create `.streamlit/secrets.toml` and add your key:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
```

For Streamlit Community Cloud, add `GEMINI_API_KEY` in the app's Secrets
settings. The non-AI planning tools remain available when the key is not
configured; AI planning and theme recommendations require it.

**Security reminder:** Never upload your API key, `.env` file, or other private credentials to GitHub.

### 7. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

The language selector is above the welcome title. Interface translations are
stored in `translations.py` and `translations_extra.json`; AI-generated plans
may still be returned in English.

Plan backups are downloaded to and restored from your device. They are not
persisted by the application between browser sessions. Imported backups are
UTF-8 JSON files limited to 1 MiB and are validated before the current plan is
changed. Backups do not include API keys or other application secrets.

## 📂 Project Structure

```text
event-planner/
├── app.py
├── app_resources.py
├── checklist_utils.py
├── expense_utils.py
├── plan_utils.py
├── translations.py
├── translations_extra.json
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    ├── test_app.py
    ├── test_checklist_utils.py
    └── test_plan_utils.py
```

*Note: Your actual project may contain additional files and folders.*

## 🔐 Security

* Keep API keys and credentials private.
* Never commit `.streamlit/secrets.toml`, `.env` files, or other credentials.
* Use Streamlit Secrets for local and deployed configuration.
* GitHub Actions runs the test suite, Python syntax compilation, Bandit, and pip-audit.

## 🎯 Project Objective

The objective of this project is to simplify event planning by combining artificial intelligence with an interactive web interface, helping users organize celebrations according to their preferences.

## 👩‍💻 Author

**Latha Sri**

B.Tech — Artificial Intelligence and Machine Learning

**Areas of Interest:** Artificial Intelligence, Data Analytics, Python Development, and Web Applications.

## ⭐ Acknowledgements

* Google Gemini API for AI-powered content generation.
* Streamlit for providing the web application framework.

---

✨ *Making every celebration easier to plan and more memorable!*
