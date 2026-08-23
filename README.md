<div align="center">
  <img src="app/static/img/favicon.png" alt="MedRipple Logo" width="120" />
  <h1>MedRipple</h1>
  <p><em>Every visit starts a smarter care journey.</em></p>
  <p>
    An AI-powered longitudinal healthcare orchestration platform designed to seamlessly connect patient intake, AI pre-visit clinical briefs, real-time consultation management, and proactive healthcare tracking.
  </p>
</div>

---

## 🌟 Core Features

- **🧠 Adaptive AI Symptom Intake:** Patients chat with the *MedRipple Health Assistant* before their visit. The AI dynamically adapts its questions based on their evolving symptoms and stores insights directly into vector memory.
- **👨‍⚕️ Clinical Copilot:** Doctors get an instant, AI-generated pre-visit brief synthesizing the patient's entire medical history, past medications, and the current symptom intake—saving crucial diagnostic time.
- **📅 Smart Booking & Auto-Rescheduling:** Real-time appointment booking with Google Calendar synchronization. If a doctor applies for emergency leave, the system intelligently auto-reschedules affected patients.
- **📈 Longitudinal Care Timeline:** A unified patient memory graph tracing diagnoses, prescriptions, and lifestyle changes across years of visits.
- **🚀 Fully Containerized & Cloud Ready:** Built on FastAPI and deployed on Render with PostgreSQL Vector DBs.

---

## 🏗️ Application Architecture

The platform runs on a robust modern stack:
* **Backend:** FastAPI (Python 3.10+)
* **Frontend:** Jinja2 Templates + Vanilla JS + Vanilla CSS (Glassmorphism UI)
* **Database:** PostgreSQL with `pgvector` for AI embeddings
* **AI Engine:** Groq API (`gpt-oss-120b` & `gpt-oss-20b`) for lightning-fast inference
* **Task Queue:** Celery & Redis for async automated follow-ups

### Key Web Routes
| Route | Role | Description |
|---|---|---|
| `/login` | Public | Secure JWT-based authentication |
| `/patient/dashboard` | Patient | View appointment history & connect Google Calendar |
| `/patient/doctors` | Patient | Find doctors & book real-time held slots |
| `/patient/intake/{id}` | Patient | AI Adaptive Symptom Intake Copilot |
| `/doctor/dashboard` | Doctor | Doctor appointment queue, metrics & deletions |
| `/doctor/copilot/{id}`| Doctor | Pre-visit AI Clinical Brief & consultation notes |
| `/doctor/leave` | Doctor | Apply for leave with auto-rescheduling |

---

## 🚀 How to Run MedRipple Locally

The platform is designed to be fully testable on your local machine.

### 1. Prerequisites
- **Python 3.10+**
- **Redis** (optional, required if running Celery background workers)
- **PostgreSQL / Neon DB**

### 2. Installation
```bash
git clone https://github.com/your-username/MedRipple.git
cd MedRipple

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (`.env`)
Create a `.env` file in the root directory:
```env
APP_ENV=development
PORT=8000
SECRET_KEY=your-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/medripple
GROQ_API_KEY=your-groq-key

# Google Calendar OAuth (See local vs prod notes below)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/callback

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

### 4. Database Setup & Start
```bash
# Run database migrations
alembic upgrade head

# Start the web server
python main.py
```
Access the portal at **http://127.0.0.1:8000**.

---

## ⚠️ CRITICAL: Local Development vs. Cloud Deployment (Render)

When transitioning this application from `localhost` to a public cloud provider like Render (`*.onrender.com`), you will encounter strict third-party security firewalls. **This is expected behavior.**

### 📧 1. Email Notifications (SMTP vs API & DMARC)
* **Localhost (`development`):** You can easily send emails using Python's built-in `smtplib` via Gmail's SMTP port 465 using an App Password.
* **Render Free Tier (`production`):** Render completely blocks all outbound SMTP traffic (Ports 25, 465, 587) to prevent spam. 
  * **The MedRipple Fix:** The backend automatically detects the environment. If you supply a SendGrid API key (`SG....`) as the `EMAIL_PASSWORD`, the app bypasses SMTP and uses SendGrid's HTTPS REST API.
  * **The DMARC Catch:** Even if SendGrid successfully accepts the API request, if your `EMAIL_FROM` is a `@gmail.com` address, Google's receiving servers will flag it as spoofing and silently drop it or send it to Spam.
  * **Production Solution:** To achieve 100% inbox deliverability in production, you must buy a custom domain (e.g., `medripple.com`) and verify it on SendGrid as a Single Sender.

### 📅 2. Google Calendar OAuth 2.0 (Public Suffix Block)
* **Localhost (`development`):** Google completely drops its security policies for developers testing on `http://localhost`. Calendar OAuth works flawlessly out of the box.
* **Render Free Tier (`production`):** If you attempt to connect a Google Calendar from `https://medripple.onrender.com`, Google will throw an `Error 400: invalid_request (doesn't comply with Google's OAuth 2.0 policy)`.
  * **Why?** Google classifies the Calendar API as a "Highly Sensitive Scope". They maintain a strict internal blacklist against "Public Suffix Domains" like `.onrender.com`, `.herokuapp.com`, and `.ngrok.io` because these domains are heavily abused by phishing campaigns. Google requires domain verification via Search Console, which is impossible since you don't own the root `onrender.com` domain.
  * **Production Solution:** To enable Calendar sync in the cloud, you **must** purchase a custom domain, point it to your Render server via DNS, and verify that domain in the Google Cloud OAuth Consent Screen. 

*Until a custom domain is purchased, all Calendar OAuth testing must be done locally on `http://localhost:8000`.*
