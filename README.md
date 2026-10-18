# 🎓 AI Student Study Planner

An intelligent, full-stack study planning application powered by **Retrieval-Augmented Generation (RAG)**, **Groq LLaMA 3.3 70B**, **pgvector**, and **React**.

The AI Student Study Planner analyzes a student's target subjects, specific topics, knowledge level, daily available hours, target exam date, and preferred study sessions to synthesize a realistic, day-by-day study roadmap.

---

## 🌟 Key Features

- **Personalized AI Study Schedules**: Generates day-by-day study schedules tailored to individual pace, knowledge level, and daily availability using **LLaMA 3.3 70B Versatile** via the **Groq API**.
- **Retrieval-Augmented Generation (RAG)**: Integrates contextual academic knowledge using local vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`) and **PostgreSQL with pgvector** (Cosine Distance similarity search).
- **Custom Document Upload & Knowledge Indexing**: Allows students to upload PDFs (`.pdf`) and text-based notes (`.txt`, `.md`, `.csv`, `.json`). Documents are automatically chunked, embedded into 384-dimensional vectors, and stored in pgvector for future retrieval.
- **JWT-Based Authentication**: Secure user registration, login, and session tokens via `djangorestframework-simplejwt`.
- **Interactive Modern UI**: Clean React + Vite interface with multi-subject selection, dynamic markdown plan rendering, day-by-day completion checklists, and plan downloads.
- **Pre-seeded Knowledge Base**: Includes a management command to populate foundational domain knowledge for DBMS, Python, Django, and DSA.
- **Automated Windows DB Setup Script**: Includes `setup_db.ps1` to easily provision a portable PostgreSQL 16 + pgvector environment on Windows.

---

## 🏗️ Architecture & Tech Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Modern CSS / Flexbox / Grid
- **State Management**: React Hooks (`useState`, `useEffect`) & LocalStorage token persistence

### Backend
- **Framework**: Django 4.2+ & Django REST Framework (DRF)
- **Auth**: SimpleJWT (Access & Refresh tokens)
- **Vector Database**: PostgreSQL 16 with `pgvector`
- **Embedding Model**: `sentence-transformers` (`all-MiniLM-L6-v2` - 384 dimensions, local execution)
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **PDF Extraction**: `pypdf`

```
┌─────────────────┐       HTTP / REST       ┌───────────────────────┐
│                 │ ──────────────────────> │  Django REST Backend  │
│   React + Vite  │                         │  - SimpleJWT Auth     │
│    (Frontend)   │ <────────────────────── │  - SentenceTransformer│
└─────────────────┘      JSON Payload       └───────────┬───────────┘
                                                        │
                         ┌──────────────────────────────┼──────────────────────────────┐
                         ▼                                                             ▼
              ┌─────────────────────┐                                       ┌─────────────────────┐
              │    PostgreSQL 16    │                                       │      Groq API       │
              │     + pgvector      │                                       │ (LLaMA 3.3 70B RAG) │
              └─────────────────────┘                                       └─────────────────────┘
```

---

## 📂 Project Structure

```
Ai-student-planner/
├── backend/
│   ├── accounts/             # Authentication & user registration endpoints
│   ├── config/               # Django root settings and URL routing
│   ├── studyplan/            # Study planner core logic, models, RAG services & views
│   │   ├── management/
│   │   │   └── commands/     # seed_knowledge.py for DB pre-population
│   │   ├── models.py         # StudyKnowledge (with VectorField) & StudyPlan models
│   │   ├── services.py       # EmbeddingService & GroqService
│   │   └── views.py          # Plan generation & Document upload views
│   ├── .env.example          # Environment variables template
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx           # Main study planner UI & state logic
│   │   ├── index.css         # Styling
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── setup_db.ps1              # Automated portable PostgreSQL + pgvector installer
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.10+ (Python 3.13 supported)
- **Node.js**: 18+ and npm
- **PostgreSQL 16** with `pgvector` extension
- **Groq API Key**: Obtainable from [console.groq.com](https://console.groq.com/)

---

### 2. Database Setup (Windows)

You can run the included PowerShell automation script to set up a portable PostgreSQL 16 instance with pgvector:

```powershell
.\setup_db.ps1
```

Or manually configure your existing PostgreSQL instance:
```sql
CREATE DATABASE studyplan;
\c studyplan;
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 3. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True

   DATABASE_NAME=studyplan
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_postgres_password
   DATABASE_HOST=127.0.0.1
   DATABASE_PORT=5432

   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Seed foundational study knowledge**:
   ```bash
   python manage.py seed_knowledge
   ```

7. **Start the Django server**:
   ```bash
   python manage.py runserver
   ```
   The backend will start at `http://127.0.0.1:8000/`.

---

### 4. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   Open your browser at `http://localhost:5173/`.

---

## 📡 API Endpoints

### Authentication (`/api/auth/`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/signup/` | Register a new student account | No |
| `POST` | `/api/auth/login/` | Obtain JWT access and refresh token | No |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token | No |

### Study Plan & Knowledge (`/api/studyplan/`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/studyplan/generate/` | Generate customized day-by-day study plan | Yes (`Bearer <token>`) |
| `POST` | `/api/studyplan/upload/` | Upload `.pdf`, `.txt`, `.md`, `.csv` document into RAG vector store | Yes (`Bearer <token>`) |

---

## 🧪 Running Tests

To run the backend test suite:
```bash
cd backend
python manage.py test
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
