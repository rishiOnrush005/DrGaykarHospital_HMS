<div align="center">

# 🏥 Dr. Gaykar Hospital Management System

**A bilingual, offline-first patient management system built for a real village clinic in rural Maharashtra, India.**

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare_Tunnel-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)

</div>

---

## 📌 The Real Problem I Solved

Dr. Gaykar's clinic in a small village in Maharashtra was running entirely on **paper notebooks** — patient records, visit histories, prescriptions, everything handwritten. This created serious operational risks:

- A lost or damaged notebook meant **permanent loss of patient history**
- Finding a patient's past records during emergencies took **minutes of manual searching**
- The doctor had **no way to access records remotely** — he had to be physically present
- Staff had no system in a language they were comfortable with — **all tools were English-only**
- There was **zero data backup**, making years of records vulnerable to a single accident

This project replaces that notebook with a purpose-built, offline software system that runs on the clinic's existing laptop — no internet subscription, no cloud fees, no IT team required.

---

## 📊 Quantitative Impact

| Metric | Before (Paper) | After (This System) |
|---|---|---|
| Patient lookup time | ~3–5 minutes (manual search) | **< 2 seconds** (indexed DB search) |
| Patient record fields | ~4 (name, age, basic notes) | **9 structured fields** per patient |
| Visit data captured | Unstructured notes | **8 clinical fields** per visit |
| Languages supported | English only | **2 (English + Marathi)** |
| Remote doctor access | ❌ Not possible | ✅ Via Cloudflare Tunnel |
| Data backup | ❌ Never | ✅ Auto every 10 days + manual |
| Internet dependency | N/A | **Zero — 100% offline** |
| Devices supported | Paper | **Laptop + any phone on WiFi** |
| Prescription photos | Not stored | ✅ Stored & accessible remotely |
| Access security | None | **Role-based + PIN-protected backup** |

---

## ✨ Key Features

### 👥 Role-Based Access Control
- **3 roles:** Doctor, Receptionist, Staff
- Each role gets a different dashboard and permission level
- Doctor has full access including remote access, backup, and patient history
- Staff can register patients and record vitals — nothing more

### 🌐 Bilingual Interface (English + Marathi)
- Language **auto-assigned on login** based on role (Doctor → English, Staff → Marathi)
- Users can **toggle language anytime** from the navbar
- Preference is saved per user — persists across sessions
- Powered by **Django i18n** with compiled `.po` / `.mo` translation files

### 🩺 OPD Queue System
- Staff records patient vitals → patient enters the queue
- Doctor sees a **live queue** on dashboard, examines patients in order
- Visit status: `Pending → Completed` (auto-expires to `Unexamined` after 12 hours)

### 📷 Handwritten Prescription Photo Upload
- Doctor can photograph a handwritten prescription and attach it to a visit
- Photos stored on the **local machine** (`/media/prescriptions/`)
- Accessible remotely via Cloudflare Tunnel URL — doctor can view from home

### 🔒 Secure Backup System
- **Auto backup** every 10 days triggered on doctor's dashboard load
- **Manual "Backup Now"** button for on-demand backups
- Backup path configurable (defaults to local `/backups/` folder — works on Windows)
- **PIN-protected** backup manager (4-digit PIN, timing-attack resistant)
- **Restore** validates SQLite magic bytes before overwriting live database
- Safety copy (`.before_restore`) created before every restore

### 📡 Dual Access Architecture
- **Local WiFi:** Staff access via `192.168.1.x:8000` — no internet needed
- **Remote:** Doctor accesses via **free Cloudflare Tunnel** from anywhere
- Static IP on the hospital laptop ensures the address never changes
- App starts automatically on PC boot via **NSSM Windows Service**

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python 3.12 + Django 5.2 | Mature, batteries-included, i18n support |
| Database | SQLite | Zero-config, single file, easy to back up |
| Frontend | Django Templates + Tailwind CSS | No build step, mobile-responsive |
| Icons | Bootstrap Icons | Lightweight, CDN-served |
| Translations | Django i18n (gettext) | Built-in, production-grade |
| Static files | WhiteNoise | Serves static files without a web server |
| Remote access | Cloudflare Tunnel | Free, permanent URL, HTTPS automatic |
| Windows service | NSSM | Runs Django silently on PC boot |
| Image handling | Pillow | Prescription photo upload & validation |
| Config | python-decouple | `.env`-based config, no hardcoded secrets |

---

## 🗄️ Data Models

```
CustomUser
├── role: doctor | staff | receptionist
└── language_preference: en | mr

Patient
├── patient_id: PAT-0001 (auto-generated)
├── name, age, gender, phone
├── village, blood_group
└── registered_on (auto)

Visit (linked to Patient)
├── vitals: weight, bp, temp, sugar
├── clinical: symptoms, diagnosis, prescription_text
├── prescription_photo (ImageField)
├── follow_up_date
├── status: pending | completed | unexamined
└── attended_by (FK → Doctor)
```

---

## 🖼️ Screenshots

> _Screenshots will be added here_

| Doctor Dashboard | Staff Dashboard |
|---|---|
| ![Doctor Dashboard](screenshots/doctor_dashboard.png) | ![Staff Dashboard](screenshots/staff_dashboard.png) |

| Patient Profile | OPD Queue |
|---|---|
| ![Patient Profile](screenshots/patient_detail.png) | ![OPD Queue](screenshots/opd_queue.png) |

| Bilingual UI (Marathi) | Backup Manager |
|---|---|
| ![Marathi UI](screenshots/marathi_ui.png) | ![Backup Manager](screenshots/backup_manager.png) |

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/DrGaykarHospital.git
cd DrGaykarHospital

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Edit .env with your SECRET_KEY and settings

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser (Doctor account)
python manage.py createsuperuser

# 7. Compile Marathi translations
python manage.py compilemessages

# 8. Start the server
python manage.py runserver 0.0.0.0:8000
```

App is now accessible at `http://localhost:8000`

---

### Hospital Deployment (Windows + NSSM)

```bash
# 1. Install NSSM from https://nssm.cc

# 2. Register Django as a Windows Service
nssm install DrGaykarHospital
# Path: C:\Python312\python.exe
# Arguments: C:\DrGaykarHospital\manage.py runserver 0.0.0.0:8000

# 3. Start the service
nssm start DrGaykarHospital

# 4. Set static IP on the laptop (192.168.1.100)
# Staff access: http://192.168.1.100:8000
```

### Remote Access (Cloudflare Tunnel — Free)

```bash
# 1. Install cloudflared.exe
# 2. Authenticate
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create gaykar-hospital

# 4. Register as Windows Service
cloudflared service install

# Doctor remote access: https://gaykar-hospital.trycloudflare.com
```

---

## 📁 Project Structure

```
DrGaykarHospital/
├── hospital_project/     # Django settings, URLs
├── accounts/             # Auth, roles, user management
├── patients/             # Patient registration & search
├── visits/               # OPD visits, prescriptions
├── dashboard/            # Role-based dashboards
├── backup/               # Backup & restore system
├── templates/            # All HTML templates
├── locale/               # en + mr translations (.po/.mo)
├── static/               # CSS, JS assets
├── media/                # Uploaded prescription photos
└── backups/              # Auto-generated DB backups
```

---

## 🔐 Security Highlights

- All views protected with `@login_required`
- Role checks on every sensitive action (export, import, backup, delete)
- Backup manager requires 4-digit PIN (timing-attack resistant via `hmac.compare_digest`)
- Restore validates SQLite magic bytes before overwriting live database
- CSRF protection on all POST forms
- Cloudflare Tunnel provides HTTPS automatically — no SSL cert management needed
- `.env` file keeps secrets out of source code

---

## 👤 Author

**Rushikesh** — Final Year BCA Student  
📍 Pimpri, Pune, Maharashtra, India  
Building real solutions for real problems.

> *"The best way to learn software engineering is to ship something that actually runs in the real world."*

---

## 📄 License

This project is built for a specific clinic and is not a generic product. Feel free to fork and adapt for your own use case.
