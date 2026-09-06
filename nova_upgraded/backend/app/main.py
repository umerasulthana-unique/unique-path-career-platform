import os
import json
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, get_db
from .models import *
from .security import hash_password, verify_password, create_token, decode_token


app = FastAPI(
    title="Unique Path — AI Career Platform",
    version="3.0.0"
)


# ============================================================
# CORS
# ============================================================

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class Login(BaseModel):
    email: EmailStr
    password: str


class Register(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "STUDENT"


class ProfileIn(BaseModel):
    name: str
    headline: str = ""
    location: str = ""
    bio: str = ""
    phone: str = ""


class SkillIn(BaseModel):
    skill_id: int
    level: int = 3
    evidence: str = ""


class OpportunityIn(BaseModel):
    kind: str = "JOB"
    title: str
    company: str
    location: str = "Remote"
    description: str = ""
    skills: str = ""
    salary: str = ""
    employment_type: str = "Full-time"
    deadline: str = ""


class ApplyIn(BaseModel):
    cover_note: str = ""


class ProjectIn(BaseModel):
    title: str
    description: str = ""
    tech_stack: str = ""
    project_url: str = ""
    image_url: str = ""


class AssessmentSubmit(BaseModel):
    assessment_id: int
    score: float


class ChatIn(BaseModel):
    message: str


class MentorReq(BaseModel):
    mentor_id: int
    message: str = ""


class CertIn(BaseModel):
    name: str
    issuer: str = ""
    credential_url: str = ""
    issue_date: str = ""


class ATSIn(BaseModel):
    resume_text: str
    job_description: str


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    print("Starting Unique Path AI Career Platform...")

    # Create all MySQL tables
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    try:
        seed(db)
        print("Database seed completed successfully.")
    except Exception as e:
        db.rollback()
        print("Database seed error:", repr(e))
        raise
    finally:
        db.close()


# ============================================================
# DATABASE SEED
# ============================================================

def seed(db: Session):

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    skills = [
        "Python",
        "SQL",
        "JavaScript",
        "React",
        "FastAPI",
        "Machine Learning",
        "Data Analysis",
        "Communication",
        "Leadership",
        "Cloud",
        "Git",
        "Cybersecurity",
        "UI/UX",
        "Java",
        "Power BI",
    ]

    for i, name in enumerate(skills):

        existing_skill = (
            db.query(Skill)
            .filter_by(name=name)
            .first()
        )

        if not existing_skill:
            db.add(
                Skill(
                    name=name,
                    category=(
                        "Soft Skills"
                        if name in ["Communication", "Leadership"]
                        else "Technical"
                    ),
                    demand=60 + (i % 5) * 7,
                )
            )

    # Make sure newly added skills are available
    db.flush()


    # --------------------------------------------------------
    # DEMO USERS
    # --------------------------------------------------------

    demo_users = [
        (
            "student@example.com",
            "Demo Student",
            "STUDENT"
        ),
        (
            "industry@example.com",
            "Demo Industry",
            "INDUSTRY"
        ),
        (
            "admin@example.com",
            "Demo Admin",
            "ADMIN"
        ),
    ]

    for email, name, role in demo_users:

        existing_user = (
            db.query(User)
            .filter_by(email=email)
            .first()
        )

        if not existing_user:

            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password("password123"),
                    role=role,
                    headline="AI Career Explorer",
                    location="India",
                )
            )

    # VERY IMPORTANT:
    # Make sure demo users exist in MySQL before
    # we use their IDs below.
    db.flush()


    # --------------------------------------------------------
    # GET INDUSTRY USER SAFELY
    # --------------------------------------------------------

    industry_user = (
        db.query(User)
        .filter_by(email="industry@example.com")
        .first()
    )

    if industry_user is None:

        industry_user = User(
            name="Demo Industry",
            email="industry@example.com",
            password_hash=hash_password("password123"),
            role="INDUSTRY",
            headline="Industry Recruiter",
            location="India",
        )

        db.add(industry_user)
        db.flush()


    # --------------------------------------------------------
    # ASSESSMENTS
    # --------------------------------------------------------

    if db.query(Assessment).count() == 0:

        python_skill = (
            db.query(Skill)
            .filter_by(name="Python")
            .first()
        )

        sql_skill = (
            db.query(Skill)
            .filter_by(name="SQL")
            .first()
        )

        if python_skill and sql_skill:

            db.add_all(
                [
                    Assessment(
                        title="Python Foundations",
                        skill_id=python_skill.id,
                        duration_minutes=20,
                        difficulty="Beginner",
                        questions_json=json.dumps(
                            [
                                "Variables and types",
                                "Functions",
                                "Lists and dictionaries",
                                "Exceptions",
                            ]
                        ),
                    ),

                    Assessment(
                        title="SQL & Data",
                        skill_id=sql_skill.id,
                        duration_minutes=25,
                        difficulty="Intermediate",
                        questions_json=json.dumps(
                            [
                                "SELECT basics",
                                "JOINs",
                                "GROUP BY",
                                "Indexes",
                            ]
                        ),
                    ),
                ]
            )


    # --------------------------------------------------------
    # OPPORTUNITIES
    # --------------------------------------------------------

    if db.query(Opportunity).count() == 0:

        db.add_all(
            [
                Opportunity(
                    kind="INTERNSHIP",
                    title="AI/ML Intern",
                    company="NovaTech Labs",
                    location="Bengaluru / Hybrid",
                    description=(
                        "Build practical ML features with a "
                        "product team."
                    ),
                    skills="Python, Machine Learning, SQL",
                    salary="₹25k/month",
                    employment_type="Internship",
                    deadline="2026-12-30",
                    posted_by=industry_user.id,
                ),

                Opportunity(
                    kind="JOB",
                    title="Junior Full Stack Developer",
                    company="Orbit Systems",
                    location="Remote",
                    description=(
                        "Work across React and FastAPI "
                        "applications."
                    ),
                    skills="React, JavaScript, FastAPI, SQL",
                    salary="₹6-10 LPA",
                    employment_type="Full-time",
                    deadline="2026-11-30",
                    posted_by=industry_user.id,
                ),
            ]
        )


    # --------------------------------------------------------
    # MENTORS
    # --------------------------------------------------------

    if db.query(Mentor).count() == 0:

        db.add_all(
            [
                Mentor(
                    name="Aarav Mehta",
                    expertise="AI, Python, ML",
                    company="TechNova",
                    experience_years=8,
                    rating=4.9,
                    availability="Evenings",
                ),

                Mentor(
                    name="Priya Shah",
                    expertise="Product, UX, Career Strategy",
                    company="Orbit",
                    experience_years=10,
                    rating=4.8,
                    availability="Weekends",
                ),
            ]
        )


    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    course_urls = {
        "Python for Data & AI":
            "https://www.coursera.org/courses?query=python",

        "Modern React & APIs":
            "https://www.freecodecamp.org/learn/",

        "SQL for Analytics":
            "https://www.khanacademy.org/computing/computer-programming/sql",
    }

    if db.query(Course).count() == 0:

        db.add_all(
            [
                Course(
                    title="Python for Data & AI",
                    provider="Unique Path",
                    category="AI",
                    level="Beginner",
                    duration="8 weeks",
                    url=course_urls["Python for Data & AI"],
                ),

                Course(
                    title="Modern React & APIs",
                    provider="Unique Path",
                    category="Development",
                    level="Intermediate",
                    duration="6 weeks",
                    url=course_urls["Modern React & APIs"],
                ),

                Course(
                    title="SQL for Analytics",
                    provider="Unique Path",
                    category="Data",
                    level="Beginner",
                    duration="4 weeks",
                    url=course_urls["SQL for Analytics"],
                ),
            ]
        )

    else:

        for course in db.query(Course).all():

            if not course.url and course.title in course_urls:
                course.url = course_urls[course.title]


    # --------------------------------------------------------
    # COMMIT EVERYTHING
    # --------------------------------------------------------

    db.commit()


# ============================================================
# AUTHENTICATION
# ============================================================

def current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )

    try:

        token = authorization[7:]
        payload = decode_token(token)

        user_id = int(payload["sub"])

        user = db.get(User, user_id)

    except Exception:

        user = None

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid session"
        )

    return user


def user_dict(user):

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "headline": user.headline,
        "location": user.location,
        "bio": user.bio,
        "phone": user.phone,
        "avatar": user.avatar,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "database": "mysql",
        "ai": bool(os.getenv("OLLAMA_URL")),
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/api/auth/register")
def register(
    x: Register,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(User)
        .filter_by(email=x.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    requested_role = x.role.upper()

    if requested_role in ["STUDENT", "INDUSTRY", "ADMIN"]:
        role = requested_role
    else:
        role = "STUDENT"

    user = User(
        name=x.name,
        email=x.email,
        password_hash=hash_password(x.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_token(user.id, user.role),
        "user": user_dict(user),
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(
    x: Login,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter_by(email=x.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        x.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "token": create_token(user.id, user.role),
        "user": user_dict(user),
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/api/me")
def me(
    user=Depends(current_user)
):

    return user_dict(user)


# ============================================================
# PROFILE
# ============================================================

@app.put("/api/profile")
def profile(
    x: ProfileIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    for key, value in x.model_dump().items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user_dict(user)


# ============================================================
# SKILLS
# ============================================================

@app.get("/api/skills")
def skills(
    db: Session = Depends(get_db)
):

    rows = (
        db.query(Skill)
        .order_by(Skill.demand.desc())
        .all()
    )

    return [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category,
            "demand": skill.demand,
        }
        for skill in rows
    ]


@app.get("/api/my-skills")
def myskills(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    rows = (
        db.query(UserSkill, Skill)
        .join(
            Skill,
            UserSkill.skill_id == Skill.id
        )
        .filter(UserSkill.user_id == user.id)
        .all()
    )

    return [
        {
            "id": row.Skill.id,
            "name": row.Skill.name,
            "category": row.Skill.category,
            "level": row.UserSkill.level,
            "evidence": row.UserSkill.evidence,
        }
        for row in rows
    ]


@app.post("/api/my-skills")
def addskill(
    x: SkillIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    row = (
        db.query(UserSkill)
        .filter_by(
            user_id=user.id,
            skill_id=x.skill_id
        )
        .first()
    )

    if row:

        row.level = x.level
        row.evidence = x.evidence

    else:

        db.add(
            UserSkill(
                user_id=user.id,
                skill_id=x.skill_id,
                level=x.level,
                evidence=x.evidence,
            )
        )

    db.commit()

    return {
        "ok": True
    }


@app.delete("/api/my-skills/{skill_id}")
def delskill(
    skill_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    row = (
        db.query(UserSkill)
        .filter_by(
            user_id=user.id,
            skill_id=skill_id
        )
        .first()
    )

    if row:

        db.delete(row)
        db.commit()

    return {
        "ok": True
    }


# ============================================================
# ASSESSMENTS
# ============================================================

@app.get("/api/assessments")
def assessments(
    db: Session = Depends(get_db)
):

    rows = db.query(Assessment).all()

    return [
        {
            "id": assessment.id,
            "title": assessment.title,
            "duration": assessment.duration_minutes,
            "difficulty": assessment.difficulty,
            "questions": json.loads(
                assessment.questions_json
            ),
        }
        for assessment in rows
    ]


@app.post("/api/assessments/submit")
def submit_assessment(
    x: AssessmentSubmit,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    result = AssessmentResult(
        user_id=user.id,
        assessment_id=x.assessment_id,
        score=x.score,
    )

    db.add(result)
    db.commit()

    return {
        "ok": True,
        "score": x.score,
    }


# ============================================================
# SKILL GAP
# ============================================================

@app.get("/api/skill-gap")
def skill_gap(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    user_skills = {
        row.skill_id: row.level
        for row in (
            db.query(UserSkill)
            .filter_by(user_id=user.id)
            .all()
        )
    }

    jobs = (
        db.query(Opportunity)
        .filter_by(status="OPEN")
        .all()
    )

    needed = {}

    for job in jobs:

        for name in [
            item.strip()
            for item in job.skills.split(",")
            if item.strip()
        ]:

            skill = (
                db.query(Skill)
                .filter(
                    func.lower(Skill.name)
                    == name.lower()
                )
                .first()
            )

            if skill:

                needed[skill.id] = max(
                    needed.get(skill.id, 0),
                    4
                )

    result = []

    for skill_id, target in needed.items():

        skill = db.get(Skill, skill_id)

        if not skill:
            continue

        current = user_skills.get(
            skill_id,
            0
        )

        result.append(
            {
                "skill": skill.name,
                "current": current,
                "target": target,
                "gap": max(
                    0,
                    target - current
                ),
                "demand": skill.demand,
            }
        )

    return sorted(
        result,
        key=lambda item: item["gap"],
        reverse=True
    )


# ============================================================
# OPPORTUNITIES
# ============================================================

def opp_dict(opportunity):

    return {
        "id": opportunity.id,
        "kind": opportunity.kind,
        "title": opportunity.title,
        "company": opportunity.company,
        "location": opportunity.location,
        "description": opportunity.description,
        "skills": opportunity.skills,
        "salary": opportunity.salary,
        "employment_type": opportunity.employment_type,
        "deadline": opportunity.deadline,
        "created_at": (
            opportunity.created_at.isoformat()
            if opportunity.created_at
            else ""
        ),
    }


@app.get("/api/opportunities")
def opportunities(
    kind: Optional[str] = None,
    db: Session = Depends(get_db),
):

    query = (
        db.query(Opportunity)
        .filter_by(status="OPEN")
    )

    if kind:

        query = query.filter_by(
            kind=kind.upper()
        )

    rows = (
        query
        .order_by(
            Opportunity.created_at.desc()
        )
        .all()
    )

    return [
        opp_dict(opportunity)
        for opportunity in rows
    ]


@app.post("/api/opportunities")
def create_opp(
    x: OpportunityIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    if user.role not in ["INDUSTRY", "ADMIN"]:

        raise HTTPException(
            status_code=403,
            detail="Industry/Admin access required"
        )

    opportunity = Opportunity(
        **x.model_dump(),
        posted_by=user.id
    )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    return opp_dict(opportunity)


@app.delete("/api/opportunities/{oid}")
def delete_opp(
    oid: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    opportunity = db.get(
        Opportunity,
        oid
    )

    if not opportunity:

        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    if (
        user.role != "ADMIN"
        and opportunity.posted_by != user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    opportunity.status = "CLOSED"

    db.commit()

    return {
        "ok": True
    }


# ============================================================
# APPLICATIONS
# ============================================================

@app.post("/api/opportunities/{oid}/apply")
def apply(
    oid: int,
    x: ApplyIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    existing = (
        db.query(Application)
        .filter_by(
            user_id=user.id,
            opportunity_id=oid
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Already applied"
        )

    opportunity = db.get(
        Opportunity,
        oid
    )

    if not opportunity:

        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    application = Application(
        user_id=user.id,
        opportunity_id=oid,
        cover_note=x.cover_note,
    )

    db.add(application)

    db.add(
        Notification(
            user_id=user.id,
            title="Application submitted",
            message=(
                "Your application was submitted "
                "successfully."
            ),
        )
    )

    db.commit()

    return {
        "ok": True
    }


@app.get("/api/applications")
def applications(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    rows = (
        db.query(Application, Opportunity)
        .join(
            Opportunity,
            Application.opportunity_id
            == Opportunity.id
        )
        .filter(
            Application.user_id == user.id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )

    return [
        {
            "id": row.Application.id,
            "status": row.Application.status,
            "title": row.Opportunity.title,
            "company": row.Opportunity.company,
            "kind": row.Opportunity.kind,
            "applied_at": (
                row.Application.applied_at.isoformat()
            ),
        }
        for row in rows
    ]


# ============================================================
# RECRUITER APPLICATIONS
# ============================================================

@app.get("/api/recruiter/applications")
def recruiter_apps(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    if user.role not in ["INDUSTRY", "ADMIN"]:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    query = (
        db.query(
            Application,
            Opportunity,
            User
        )
        .join(
            Opportunity,
            Application.opportunity_id
            == Opportunity.id
        )
        .join(
            User,
            Application.user_id
            == User.id
        )
    )

    if user.role != "ADMIN":

        query = query.filter(
            Opportunity.posted_by == user.id
        )

    rows = query.all()

    return [
        {
            "id": row.Application.id,
            "status": row.Application.status,
            "student": row.User.name,
            "email": row.User.email,
            "title": row.Opportunity.title,
            "company": row.Opportunity.company,
            "applied_at": (
                row.Application.applied_at.isoformat()
            ),
        }
        for row in rows
    ]


@app.put("/api/applications/{aid}/{status}")
def update_application(
    aid: int,
    status: str,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    if user.role not in ["INDUSTRY", "ADMIN"]:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    application = db.get(
        Application,
        aid
    )

    if not application:

        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    opportunity = db.get(
        Opportunity,
        application.opportunity_id
    )

    if (
        user.role != "ADMIN"
        and opportunity.posted_by != user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    application.status = status.upper()

    db.add(
        Notification(
            user_id=application.user_id,
            title="Application update",
            message=(
                f"Application status: "
                f"{application.status}"
            ),
        )
    )

    db.commit()

    return {
        "ok": True
    }


# ============================================================
# PORTFOLIO
# ============================================================

@app.get("/api/portfolio")
def portfolio(
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    rows = (
        db.query(PortfolioProject)
        .filter_by(user_id=user.id)
        .all()
    )

    return [
        {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "tech_stack": project.tech_stack,
            "project_url": project.project_url,
            "image_url": project.image_url,
        }
        for project in rows
    ]


@app.post("/api/portfolio")
def addproject(
    x: ProjectIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    project = PortfolioProject(
        user_id=user.id,
        **x.model_dump()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        **x.model_dump()
    }


@app.delete("/api/portfolio/{pid}")
def delproject(
    pid: int,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    project = db.get(
        PortfolioProject,
        pid
    )

    if project and project.user_id == user.id:

        db.delete(project)
        db.commit()

    return {
        "ok": True
    }


# ============================================================
# MENTORS
# ============================================================

@app.get("/api/mentors")
def mentors(
    db: Session = Depends(get_db)
):

    rows = db.query(Mentor).all()

    return [
        {
            "id": mentor.id,
            "name": mentor.name,
            "expertise": mentor.expertise,
            "company": mentor.company,
            "experience_years": mentor.experience_years,
            "rating": mentor.rating,
            "availability": mentor.availability,
        }
        for mentor in rows
    ]


@app.post("/api/mentors/request")
def mentor_request(
    x: MentorReq,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):

    request = MentorRequest(
        user_id=user.id,
        **x.model_dump()
    )

    db.add(request)
    db.commit()

    return {
        "ok": True
    }


# ============================================================
# ATS RESUME SCORER
# ============================================================

@app.post("/api/ats/score")
def ats_score(
    x: ATSIn,
    user=Depends(current_user)
):

    import re

    resume = " ".join(
        x.resume_text.lower().split()
    )

    job_description = " ".join(
        x.job_description.lower().split()
    )

    stop_words = set(
        """
        the and for with from that this your you are
        our their have has will can job role work team
        into using use years year
        """.split()
    )

    words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}",
        job_description
    )

    keywords = []
    seen = set()

    for word in words:

        if (
            word not in stop_words
            and word not in seen
        ):

            seen.add(word)
            keywords.append(word)

    matched = [
        word
        for word in keywords
        if word in resume
    ]

    missing = [
        word
        for word in keywords
        if word not in resume
    ][:12]

    keyword_score = round(
        (
            len(matched)
            / max(
                1,
                min(len(keywords), 25)
            )
        ) * 100
    )

    sections = sum(
        bool(
            re.search(
                r"\b" + heading + r"\b",
                resume
            )
        )
        for heading in [
            "summary",
            "experience",
            "education",
            "skills",
            "projects",
            "certifications",
        ]
    )

    format_score = (
        100
        if len(resume) < 9000
        else 85
    )

    score = round(
        keyword_score * 0.65
        + (sections / 6) * 25
        + format_score * 0.10
    )

    return {
        "score": min(100, score),
        "matched_keywords": matched[:15],
        "missing_keywords": missing,
        "sections_found": sections,
        "tip": (
            "Use a clean single-column resume, "
            "standard headings, and keywords that "
            "genuinely match the job description."
        ),
    }


# ============================================================
# COURSES
# ============================================================

@app.get("/api/courses")
def courses(
    db: Session = Depends(get_db)
):

    rows = db.query(Course).all()

    return [
        {
            "id": course.id,
            "title": course.title,
            "provider": course.provider,
            "category": course.category,
            "level": course.level,
            "duration": course.duration,
            "url": course.url,
        }
        for course in rows
    ]


# ============================================================
# CERTIFICATIONS
# ============================================================

@app.get("/api/certifications")
def certs(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    rows = (
        db.query(Certification)
        .filter_by(user_id=user.id)
        .all()
    )

    return [
        {
            "id": cert.id,
            "name": cert.name,
            "issuer": cert.issuer,
            "credential_url": cert.credential_url,
            "issue_date": cert.issue_date,
        }
        for cert in rows
    ]


@app.post("/api/certifications")
def addcert(
    x: CertIn,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    cert = Certification(
        user_id=user.id,
        **x.model_dump()
    )

    db.add(cert)
    db.commit()
    db.refresh(cert)

    return {
        "id": cert.id,
        **x.model_dump()
    }


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.get("/api/notifications")
def notifications(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    rows = (
        db.query(Notification)
        .filter_by(user_id=user.id)
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "read": notification.read,
            "created_at": (
                notification.created_at.isoformat()
            ),
        }
        for notification in rows
    ]


@app.put("/api/notifications/read")
def read_notifications(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    (
        db.query(Notification)
        .filter_by(user_id=user.id)
        .update({"read": True})
    )

    db.commit()

    return {
        "ok": True
    }


# ============================================================
# ADMIN ANALYTICS
# ============================================================

@app.get("/api/analytics")
def analytics(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    if user.role != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return {
        "users": db.query(User).count(),

        "students": (
            db.query(User)
            .filter_by(role="STUDENT")
            .count()
        ),

        "opportunities": (
            db.query(Opportunity)
            .filter_by(status="OPEN")
            .count()
        ),

        "applications": (
            db.query(Application)
            .count()
        ),

        "skills": (
            db.query(Skill)
            .count()
        ),

        "assessments": (
            db.query(Assessment)
            .count()
        ),
    }


# ============================================================
# OLLAMA AI CAREER ASSISTANT
# ============================================================

@app.post("/api/ai/chat")
async def ai_chat(
    x: ChatIn,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):

    base_prompt = (
        f"You are a practical AI career copilot "
        f"for {user.name}. "
        f"Give concise, actionable career advice. "
        f"User says: {x.message}"
    )

    ollama_url = (
        os.getenv(
            "OLLAMA_URL",
            "http://127.0.0.1:11434"
        )
        .rstrip("/")
    )

    model = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b"
    )

    url = ollama_url + "/api/chat"

    try:

        async with httpx.AsyncClient(
            timeout=90
        ) as client:

            response = await client.post(
                url,
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": base_prompt,
                        }
                    ],
                    "stream": False,
                },
            )

            response.raise_for_status()

            data = response.json()

            return {
                "reply": (
                    data
                    .get("message", {})
                    .get("content", "")
                )
            }

    except Exception as error:

        print(
            "Ollama connection error:",
            repr(error)
        )

        return {
            "reply": (
                "AI service is not reachable right now. "
                "Make sure Ollama is running and the "
                "configured model is installed. "
                "I can still help with your career plan "
                "using the platform data."
            )
        }


# ============================================================
# MANUAL DATABASE SEED
# ============================================================

@app.post("/api/seed")
def reseed(
    db: Session = Depends(get_db)
):

    seed(db)

    return {
        "ok": True
    }