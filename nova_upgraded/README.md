# Unique Path — AI Career Platform

Professional Academia ↔ Industry career platform with Student, Institution, Industry and Admin experiences.

## v5 signature modules
- Career DNA — evolving professional capability profile
- Future Self Simulator — compare career scenarios
- Career Experiment Lab — try realistic mini role tasks before choosing a path
- Project Builder Lab — portfolio-ready project blueprints
- Job Match AI — explainable role matching
- Opportunity Radar — prioritized opportunity stream
- Career Mirror — current profile vs target role
- Skill Dependency Graph — prerequisite-aware learning
- Digital Career Twin — evidence-based career questions
- Growth Simulator — model readiness improvements
- Institution Hub — student analytics, batch skill mapping, curriculum intelligence and placement intelligence
- Industry Hub — candidate/application workflow
- Admin analytics and platform control

## Existing modules
Career AI, AI assessments, skill gaps, jobs, internships, resume studio, portfolio studio, learning/quizzes, ATS, mentors, applications and profiles.

## Run locally
Backend:
```powershell
cd .\nova_upgraded\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Frontend:
```powershell
cd .\nova_upgraded\frontend
npm.cmd install
npm.cmd run dev
```

Set `VITE_API_URL` when the backend is hosted remotely.


## v5.1 Functional Intelligence Upgrade
The innovation modules now call real FastAPI endpoints backed by the production database and Ollama where appropriate: Career DNA, Future Self, Career Experiment Lab, Project Builder, Job Match AI, Opportunity Radar, Career Mirror, Skill Dependency Graph, Career Twin, Growth Simulator, Rejection-to-Learning, Institution analytics/curriculum translation, Industry talent finder, and Admin overview.

Demo accounts: student@example.com, industry@example.com, institution@example.com, admin@example.com — password123.
