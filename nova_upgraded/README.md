# Unique Path AI Career Hub — Full Local Edition

A no-Docker, MySQL-based full-stack career platform inspired by the Academia/Industry AI career architecture.

## Included modules
- Student / Industry / Admin login and role-aware dashboards
- Profile management
- Skills graph + skill-gap analysis
- Assessments and results
- Jobs + internships marketplace
- Industry job/internship posting
- Student applications + recruiter application pipeline
- Portfolio builder
- Learning paths / courses
- Mentor directory + mentor requests
- Certifications API
- Notifications API
- Platform analytics
- Local Ollama AI Career Copilot
- Responsive animated UI with CSS motion and glass/gradient cards

## Requirements
- Windows 10/11
- Python 3.12 or 3.13 recommended
- MySQL 8.x
- Node.js 20+ (your Node 24 also works with this frontend)
- Ollama optional for AI chat

## 1. Create MySQL database
Open MySQL Workbench or MySQL command line and run:

```sql
CREATE DATABASE academia_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 2. Backend
Open a VS Code terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set your real MySQL password:

`DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/academia_ai`

Then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Backend: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

## 3. Frontend
Open a SECOND VS Code terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints, normally:

http://localhost:5173

## 4. Demo accounts
- Student: `student@example.com` / `password123`
- Industry: `industry@example.com` / `password123`
- Admin: `admin@example.com` / `password123`

## 5. Ollama AI
Install Ollama separately and make sure the model in `.env` exists. Example:

```powershell
ollama pull llama3.2:3b
```

Keep Ollama running. The Career AI page calls the local Ollama API.

## If PowerShell blocks activation
You do NOT need to activate the environment. The commands above deliberately use:

`.\.venv\Scripts\python.exe`

so ExecutionPolicy is not a blocker.

## Production note
This is a complete local development/demo foundation. Before public deployment, add HTTPS, secure secret management, refresh-token rotation, CSRF strategy, rate limiting, object storage, migrations, background jobs, audit logs, email/SMS providers, real assessment grading, resume parsing, and a production database backup plan.


## v4 additions — external marketplaces + career studios

### Login
- Animated login/register screen with Student, Industry and Admin demo access.
- Session token is stored locally for this development build.

### Jobs
- Dedicated Jobs section.
- Local Unique Path recruiter jobs remain searchable and application tracking still works.
- **LinkedIn Jobs integration:** keyword + location search opens the official LinkedIn Jobs search in a new tab with the entered filters.
- The app does not scrape or copy LinkedIn listings; it deep-links users to LinkedIn's live marketplace.

### Internships
- Dedicated Internships section.
- Local internship listings and application tracking remain available.
- **Internshala integration:** role keyword is converted into an Internshala internship-search link.
- The app does not scrape or copy Internshala listings; it links users to the live external marketplace.

### Resume Studio
Four built-in templates:
1. ATS Classic — clean single-column layout
2. Modern Edge — modern recruiter-friendly layout
3. Executive — formal serif layout
4. Fresher Focus — student/graduate focused layout

Resume data is saved locally in the browser for this version and can be printed to PDF through the browser's Print dialog.

### Portfolio
The portfolio module is designed around project evidence: project title, context, technologies, links and outcomes. This follows common portfolio guidance to show strong work samples with context and clear links.

### Career Tools
- Cover-letter draft generator
- Interview practice question bank
- Career readiness checklist
- Career AI handoff for mock interview practice

### Design principles added
- Responsive mobile/desktop layouts
- Animated cards, glass/gradient panels and hover states
- Accessible external-link behavior
- Print-only resume layout for PDF export
- ATS-oriented resume structure and concise sections

### External integration note
LinkedIn and Internshala are third-party services. Their live listings, authentication and application flow remain on their own sites. This project intentionally uses official external search links instead of scraping or cloning their listings.


## New Learning & Career Intelligence

- Learning Center with official links to Coursera, edX, freeCodeCamp, MIT OpenCourseWare, Khan Academy, and Google Skillshop.
- In-platform career quizzes with instant scoring.
- ATS Score Checker that compares resume text with a target job description and reports matched/missing keywords.
- External Jobscan resume scanner link for an additional ATS match-rate check. Jobscan describes its score as a match-rate visualization, not an actual employer ATS score.
- Pink animated click interactions and Unique Path branding remain enabled.

Created by **Umera Sulthana**.
