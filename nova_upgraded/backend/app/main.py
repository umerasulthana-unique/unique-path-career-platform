import os, json, re
from datetime import datetime
from typing import Optional
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from .models import *
from .security import hash_password, verify_password, create_token, decode_token

app=FastAPI(title="Unique Path — AI Career Platform", version="5.1.0")
origins=[os.getenv("FRONTEND_URL","http://localhost:5173"),"http://127.0.0.1:5173"]
extra=os.getenv("FRONTEND_ORIGINS","")
origins += [x.strip() for x in extra.split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=list(dict.fromkeys(origins)),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class Login(BaseModel): email:EmailStr; password:str
class Register(BaseModel): name:str=Field(min_length=2,max_length=120); email:EmailStr; password:str=Field(min_length=8); role:str="STUDENT"
class ProfileIn(BaseModel): name:str; headline:str=""; location:str=""; bio:str=""; phone:str=""
class SkillIn(BaseModel): skill_id:int; level:int=Field(default=3,ge=1,le=4); evidence:str=""
class OpportunityIn(BaseModel): kind:str="JOB"; title:str; company:str; location:str="Remote"; description:str=""; skills:str=""; salary:str=""; employment_type:str="Full-time"; deadline:str=""
class ApplyIn(BaseModel): cover_note:str=""
class ProjectIn(BaseModel): title:str; description:str=""; tech_stack:str=""; project_url:str=""; image_url:str=""
class AssessmentSubmit(BaseModel): assessment_id:int; score:float
class AssessmentGrade(BaseModel): title:str="AI Assessment"; score:float; correct:int=0; total:int=0; role:str=""
class ChatIn(BaseModel): message:str
class MentorReq(BaseModel): mentor_id:int; message:str=""
class CertIn(BaseModel): name:str; issuer:str=""; credential_url:str=""; issue_date:str=""
class ATSIn(BaseModel): resume_text:str; job_description:str
class AIAssessmentIn(BaseModel): role:str; skills:list[str]=[]; difficulty:str="Intermediate"; count:int=8
class CoverLetterIn(BaseModel): role:str; company:str; resume:str=""
class InterviewIn(BaseModel): role:str; question:str; answer:str

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db=next(get_db()); seed(db); db.close()

def seed(db):
    skills=["Python","SQL","JavaScript","React","FastAPI","Machine Learning","Data Analysis","Communication","Leadership","Cloud","Git","Cybersecurity","UI/UX","Java","Power BI","Excel","Generative AI","Statistics","Problem Solving","Project Management"]
    for i,n in enumerate(skills):
        if not db.query(Skill).filter_by(name=n).first():
            db.add(Skill(name=n,category="Soft Skills" if n in ["Communication","Leadership","Problem Solving"] else "Technical",demand=60+(i%5)*7))
    for email,name,role in [("student@example.com","Demo Student","STUDENT"),("industry@example.com","Demo Industry","INDUSTRY"),("institution@example.com","Demo Institution","INSTITUTION"),("admin@example.com","Demo Admin","ADMIN")]:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=name,email=email,password_hash=hash_password("password123"),role=role,headline="AI Career Explorer",location="India"))
    if db.query(Assessment).count()==0:
        py=db.query(Skill).filter_by(name="Python").first(); sql=db.query(Skill).filter_by(name="SQL").first()
        db.add_all([
            Assessment(title="Python Foundations",skill_id=py.id,duration_minutes=20,difficulty="Beginner",questions_json=json.dumps(["Variables and types","Functions","Lists and dictionaries","Exceptions"])),
            Assessment(title="SQL & Data",skill_id=sql.id,duration_minutes=25,difficulty="Intermediate",questions_json=json.dumps(["SELECT basics","JOINs","GROUP BY","Indexes"]))
        ])
    if db.query(Opportunity).count()==0:
        ind=db.query(User).filter_by(email="industry@example.com").first()
        db.add_all([
            Opportunity(kind="INTERNSHIP",title="AI/ML Intern",company="NovaTech Labs",location="Bengaluru / Hybrid",description="Build practical ML features with a product team.",skills="Python, Machine Learning, SQL",salary="₹25k/month",employment_type="Internship",deadline="2026-12-30",posted_by=ind.id),
            Opportunity(kind="JOB",title="Junior Full Stack Developer",company="Orbit Systems",location="Remote",description="Work across React and FastAPI applications.",skills="React, JavaScript, FastAPI, SQL",salary="₹6-10 LPA",employment_type="Full-time",deadline="2026-11-30",posted_by=ind.id),
            Opportunity(kind="JOB",title="Data Analyst",company="InsightWorks",location="Hyderabad",description="Build dashboards and business insights.",skills="SQL, Excel, Power BI, Data Analysis",salary="₹5-8 LPA",employment_type="Full-time",deadline="2026-12-15",posted_by=ind.id)
        ])
    if db.query(Mentor).count()==0:
        db.add_all([
            Mentor(name="Aarav Mehta",expertise="AI, Python, ML, interview preparation",company="TechNova",experience_years=8,rating=4.9,availability="Evenings"),
            Mentor(name="Priya Shah",expertise="Product, UX, career strategy, portfolio",company="Orbit",experience_years=10,rating=4.8,availability="Weekends"),
            Mentor(name="Rahul Nair",expertise="Data analytics, SQL, Power BI, job search",company="InsightWorks",experience_years=7,rating=4.7,availability="Saturday mornings"),
            Mentor(name="Meera Iyer",expertise="Full-stack engineering, cloud, Git, system design",company="CloudBridge",experience_years=9,rating=4.9,availability="Friday evenings")
        ])
    if db.query(Course).count()==0:
        db.add_all([
            Course(title="Python for Data & AI",provider="Coursera",category="AI",level="Beginner",duration="8 weeks",url="https://www.coursera.org/courses?query=python"),
            Course(title="Modern React & APIs",provider="freeCodeCamp",category="Development",level="Intermediate",duration="6 weeks",url="https://www.freecodecamp.org/learn/"),
            Course(title="SQL for Analytics",provider="Khan Academy",category="Data",level="Beginner",duration="4 weeks",url="https://www.khanacademy.org/computing/computer-programming/sql"),
            Course(title="Google Career Certificates",provider="Google",category="Career",level="All levels",duration="Self paced",url="https://grow.google/certificates/")
        ])
    db.commit()

def current_user(authorization:Optional[str]=Header(None),db:Session=Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Login required")
    try: payload=decode_token(authorization[7:]); user=db.get(User,int(payload["sub"]))
    except Exception: user=None
    if not user: raise HTTPException(401,"Invalid session")
    return user

def user_dict(u):
    return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"headline":u.headline,"location":u.location,"bio":u.bio,"phone":u.phone,"avatar":u.avatar}

def ollama(prompt: str, timeout=45):
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()

    try:
        # Ollama Cloud
        if api_key and "ollama.com" in url:
            r = httpx.post(
                url + "/api/chat",
                headers={
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.35,
                        "num_predict": 900
                    }
                },
                timeout=timeout
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "").strip()

        # Local Ollama
        r = httpx.post(
            url + "/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.35,
                    "num_predict": 900
                }
            },
            timeout=timeout
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()

    except Exception:
        return ""
def parse_json(text, fallback):
    try:
        m=re.search(r"\{.*\}|\[.*\]",text,re.S)
        return json.loads(m.group(0)) if m else fallback
    except Exception: return fallback

@app.get("/api/health")
def health(): return {"status":"ok","database":"mysql","ai":bool(os.getenv("OLLAMA_URL"))}

@app.post("/api/auth/register")
def register(x:Register,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=x.email).first(): raise HTTPException(400,"Email already registered")
    role=x.role.upper() if x.role.upper() in ["STUDENT","INDUSTRY","INSTITUTION"] else "STUDENT"
    u=User(name=x.name.strip(),email=x.email,password_hash=hash_password(x.password),role=role,headline=("Student & Career Explorer" if role=="STUDENT" else ("Academic Institution Partner" if role=="INSTITUTION" else "Industry Partner")))
    db.add(u); db.commit(); db.refresh(u)
    return {"token":create_token(u.id,u.role),"user":user_dict(u)}

@app.post("/api/auth/login")
def login(x:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=x.email).first()
    if not u or not verify_password(x.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"token":create_token(u.id,u.role),"user":user_dict(u)}

@app.get("/api/me")
def me(u=Depends(current_user)): return user_dict(u)

@app.put("/api/profile")
def profile(x:ProfileIn,u=Depends(current_user),db:Session=Depends(get_db)):
    for k,v in x.model_dump().items(): setattr(u,k,v)
    db.commit(); db.refresh(u); return user_dict(u)

@app.get("/api/skills")
def skills(db:Session=Depends(get_db)):
    return [{"id":s.id,"name":s.name,"category":s.category,"demand":s.demand} for s in db.query(Skill).order_by(Skill.demand.desc()).all()]

@app.get("/api/my-skills")
def myskills(u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(UserSkill,Skill).join(Skill,UserSkill.skill_id==Skill.id).filter(UserSkill.user_id==u.id).all()
    return [{"id":r.Skill.id,"name":r.Skill.name,"category":r.Skill.category,"level":r.UserSkill.level,"evidence":r.UserSkill.evidence} for r in rows]

@app.post("/api/my-skills")
def addskill(x:SkillIn,u=Depends(current_user),db:Session=Depends(get_db)):
    row=db.query(UserSkill).filter_by(user_id=u.id,skill_id=x.skill_id).first()
    if row: row.level=x.level; row.evidence=x.evidence
    else: db.add(UserSkill(user_id=u.id,skill_id=x.skill_id,level=x.level,evidence=x.evidence))
    db.commit(); return {"ok":True}

@app.delete("/api/my-skills/{skill_id}")
def delskill(skill_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    row=db.query(UserSkill).filter_by(user_id=u.id,skill_id=skill_id).first()
    if row: db.delete(row); db.commit()
    return {"ok":True}

@app.get("/api/assessments")
def assessments(db:Session=Depends(get_db)):
    return [{"id":a.id,"title":a.title,"duration":a.duration_minutes,"difficulty":a.difficulty,"questions":json.loads(a.questions_json)} for a in db.query(Assessment).all()]

@app.post("/api/assessments/submit")
def submit_assessment(x:AssessmentSubmit,u=Depends(current_user),db:Session=Depends(get_db)):
    r=AssessmentResult(user_id=u.id,assessment_id=x.assessment_id,score=x.score); db.add(r); db.commit(); return {"ok":True,"score":x.score}

@app.post("/api/assessments/grade")
def grade_assessment(x:AssessmentGrade,u=Depends(current_user),db:Session=Depends(get_db)):
    title=x.title[:200]
    a=Assessment(title=title,skill_id=None,duration_minutes=20,difficulty="AI",questions_json="[]"); db.add(a); db.flush()
    db.add(AssessmentResult(user_id=u.id,assessment_id=a.id,score=x.score)); db.commit()
    return {"ok":True,"score":round(x.score,1),"correct":x.correct,"total":x.total,"title":title}

@app.post("/api/assessments/generate")
def generate_assessment(x:AIAssessmentIn,u=Depends(current_user)):
    count=max(4,min(x.count,12)); skills=", ".join(x.skills) or "core skills for the role"
    prompt=f"""Create {count} multiple-choice assessment questions for the job role "{x.role}".
Skills: {skills}. Difficulty: {x.difficulty}.
Return ONLY valid JSON array. Each item must have: question (string), options (exactly 4 strings), answer (integer 0-3), explanation (string).
Questions must test practical knowledge, not trivia."""
    raw=ollama(prompt)
    fallback=[
      {"question":f"Which approach is most appropriate for a {x.role} when solving a real project problem?","options":["Clarify requirements and test assumptions","Skip requirements","Copy code without review","Avoid measuring outcomes"],"answer":0,"explanation":"Clarifying requirements and validating assumptions is a practical professional habit."},
      {"question":"What is the best way to demonstrate a skill on a resume?","options":["A measurable project or achievement","Only listing the skill","Using decorative graphics","Repeating the skill many times"],"answer":0,"explanation":"Evidence and outcomes are stronger than unsupported skill lists."},
      {"question":"What should you do when you do not know an answer in an interview?","options":["Explain your reasoning and how you would find the answer","Invent a fact","Stop speaking","Change the topic"],"answer":0,"explanation":"Structured reasoning and honest learning behavior are valued."},
      {"question":"Which habit most improves employability?","options":["Continuous practice with portfolio evidence","Only collecting certificates","Never seeking feedback","Avoiding projects"],"answer":0,"explanation":"Practice plus visible evidence builds credible job readiness."}
    ]
    data=parse_json(raw,[])
    if not isinstance(data,list) or len(data)<count//2: data=fallback
    return {"role":x.role,"difficulty":x.difficulty,"questions":data[:count]}

@app.get("/api/skill-gap")
def skill_gap(u=Depends(current_user),db:Session=Depends(get_db)):
    user_sk={r.skill_id:r.level for r in db.query(UserSkill).filter_by(user_id=u.id).all()}
    jobs=db.query(Opportunity).filter_by(status="OPEN").all(); needed={}
    for j in jobs:
        for name in [x.strip() for x in j.skills.split(",") if x.strip()]:
            s=db.query(Skill).filter(func.lower(Skill.name)==name.lower()).first()
            if s: needed[s.id]=max(needed.get(s.id,0),4)
    result=[]
    resources={"Python":"Practice Python projects and a structured Python course.","SQL":"Practice SELECT, JOIN, GROUP BY and analytics queries.","React":"Build two small React apps and study component/state patterns.","Machine Learning":"Learn model evaluation, feature engineering and build one end-to-end project.","Data Analysis":"Practice data cleaning, visualization and business case studies.","Power BI":"Build dashboards from a real dataset and explain insights.","FastAPI":"Build REST APIs with validation, authentication and tests.","Communication":"Practice concise STAR stories and mock interviews.","Cloud":"Deploy a small application and learn core cloud networking/deployment concepts."}
    for sid,target in needed.items():
        s=db.get(Skill,sid); have=user_sk.get(sid,0); gap=max(0,target-have)
        result.append({"skill":s.name,"current":have,"target":target,"gap":gap,"demand":s.demand,"what_to_learn":resources.get(s.name,f"Study {s.name}, practice it on a project, then document measurable evidence."),"how_to_learn":["30–45 minutes of guided learning","Build a small project using the skill","Take a short quiz/assessment","Add the evidence to your resume and portfolio"]})
    return sorted(result,key=lambda x:(x["gap"],x["demand"]),reverse=True)

@app.get("/api/opportunities")
def opportunities(kind:Optional[str]=None,q:Optional[str]=None,location:Optional[str]=None,db:Session=Depends(get_db)):
    rows=db.query(Opportunity).filter_by(status="OPEN")
    if kind: rows=rows.filter_by(kind=kind.upper())
    if q:
        like=f"%{q}%"; rows=rows.filter((Opportunity.title.ilike(like))|(Opportunity.company.ilike(like))|(Opportunity.skills.ilike(like)))
    if location: rows=rows.filter(Opportunity.location.ilike(f"%{location}%"))
    return [opp_dict(o) for o in rows.order_by(Opportunity.created_at.desc()).all()]

def opp_dict(o): return {"id":o.id,"kind":o.kind,"title":o.title,"company":o.company,"location":o.location,"description":o.description,"skills":o.skills,"salary":o.salary,"employment_type":o.employment_type,"deadline":o.deadline,"created_at":o.created_at.isoformat()}

@app.post("/api/opportunities")
def create_opp(x:OpportunityIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role not in ["INDUSTRY","ADMIN"]: raise HTTPException(403,"Industry/Admin access required")
    o=Opportunity(**x.model_dump(),posted_by=u.id); db.add(o); db.commit(); db.refresh(o); return opp_dict(o)

@app.delete("/api/opportunities/{oid}")
def delete_opp(oid:int,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Opportunity,oid)
    if not o: raise HTTPException(404,"Not found")
    if u.role!="ADMIN" and o.posted_by!=u.id: raise HTTPException(403,"Not allowed")
    o.status="CLOSED"; db.commit(); return {"ok":True}

@app.post("/api/opportunities/{oid}/apply")
def apply(oid:int,x:ApplyIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role!="STUDENT": raise HTTPException(403,"Student account required")
    if db.query(Application).filter_by(user_id=u.id,opportunity_id=oid).first(): raise HTTPException(400,"Already applied")
    if not db.get(Opportunity,oid): raise HTTPException(404,"Opportunity not found")
    a=Application(user_id=u.id,opportunity_id=oid,cover_note=x.cover_note); db.add(a); db.add(Notification(user_id=u.id,title="Application submitted",message="Your application was submitted successfully.")); db.commit(); return {"ok":True}

@app.get("/api/applications")
def applications(u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Application,Opportunity).join(Opportunity,Application.opportunity_id==Opportunity.id).filter(Application.user_id==u.id).order_by(Application.applied_at.desc()).all()
    return [{"id":a.Application.id,"status":a.Application.status,"title":a.Opportunity.title,"company":a.Opportunity.company,"kind":a.Opportunity.kind,"applied_at":a.Application.applied_at.isoformat()} for a in rows]

@app.get("/api/recruiter/applications")
def recruiter_apps(u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role not in ["INDUSTRY","ADMIN"]: raise HTTPException(403,"Access denied")
    rows=db.query(Application,Opportunity,User).join(Opportunity,Application.opportunity_id==Opportunity.id).join(User,Application.user_id==User.id).filter(Opportunity.posted_by==u.id if u.role=="INDUSTRY" else True).all()
    return [{"id":a.Application.id,"status":a.Application.status,"role":o.title,"company":o.company,"student":{"id":s.id,"name":s.name,"email":s.email,"headline":s.headline,"location":s.location},"applied_at":a.Application.applied_at.isoformat(),"cover_note":a.Application.cover_note} for a,o,s in rows]

@app.patch("/api/applications/{aid}/{status}")
def update_application(aid:int,status:str,u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role not in ["INDUSTRY","ADMIN"]: raise HTTPException(403,"Access denied")
    a=db.get(Application,aid)
    if not a: raise HTTPException(404,"Application not found")
    a.status=status.upper(); db.add(Notification(user_id=a.user_id,title="Application updated",message=f"Your application status is now {a.status}.")); db.commit(); return {"ok":True}

@app.get("/api/portfolio")
def portfolio(u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(PortfolioProject).filter_by(user_id=u.id).all()
    return [{"id":p.id,"title":p.title,"description":p.description,"tech_stack":p.tech_stack,"project_url":p.project_url,"image_url":p.image_url} for p in rows]

@app.post("/api/portfolio")
def add_project(x:ProjectIn,u=Depends(current_user),db:Session=Depends(get_db)):
    p=PortfolioProject(user_id=u.id,**x.model_dump()); db.add(p); db.commit(); db.refresh(p); return {"id":p.id,**x.model_dump()}

@app.delete("/api/portfolio/{pid}")
def delete_project(pid:int,u=Depends(current_user),db:Session=Depends(get_db)):
    p=db.get(PortfolioProject,pid)
    if not p or p.user_id!=u.id: raise HTTPException(404,"Project not found")
    db.delete(p); db.commit(); return {"ok":True}

@app.get("/api/mentors")
def mentors(db:Session=Depends(get_db)):
    return [{"id":m.id,"name":m.name,"expertise":m.expertise,"company":m.company,"experience_years":m.experience_years,"rating":m.rating,"availability":m.availability} for m in db.query(Mentor).all()]

@app.post("/api/mentors/request")
def mentor_request(x:MentorReq,u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role!="STUDENT": raise HTTPException(403,"Student account required")
    if not db.get(Mentor,x.mentor_id): raise HTTPException(404,"Mentor not found")
    r=MentorRequest(user_id=u.id,mentor_id=x.mentor_id,message=x.message); db.add(r); db.add(Notification(user_id=u.id,title="Mentor request sent",message="Your mentor request has been recorded.")); db.commit(); return {"ok":True,"status":"PENDING"}

@app.get("/api/courses")
def courses(db:Session=Depends(get_db)):
    return [{"id":c.id,"title":c.title,"provider":c.provider,"category":c.category,"level":c.level,"duration":c.duration,"url":c.url} for c in db.query(Course).all()]

@app.get("/api/certifications")
def certifications(u=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":c.id,"name":c.name,"issuer":c.issuer,"credential_url":c.credential_url,"issue_date":c.issue_date} for c in db.query(Certification).filter_by(user_id=u.id).all()]

@app.post("/api/certifications")
def add_cert(x:CertIn,u=Depends(current_user),db:Session=Depends(get_db)):
    c=Certification(user_id=u.id,**x.model_dump()); db.add(c); db.commit(); db.refresh(c); return {"id":c.id,**x.model_dump()}

@app.get("/api/notifications")
def notifications(u=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":n.id,"title":n.title,"message":n.message,"read":n.read,"created_at":n.created_at.isoformat()} for n in db.query(Notification).filter_by(user_id=u.id).order_by(Notification.created_at.desc()).limit(30).all()]

@app.post("/api/notifications/read")
def notifications_read(u=Depends(current_user),db:Session=Depends(get_db)):
    db.query(Notification).filter_by(user_id=u.id,read=False).update({"read":True}); db.commit(); return {"ok":True}

@app.get("/api/analytics")
def analytics(u=Depends(current_user),db:Session=Depends(get_db)):
    return {"opportunities":db.query(Opportunity).filter_by(status="OPEN").count(),"applications":db.query(Application).filter_by(user_id=u.id).count(),"skills":db.query(UserSkill).filter_by(user_id=u.id).count(),"assessments":db.query(AssessmentResult).filter_by(user_id=u.id).count(),"portfolio_projects":db.query(PortfolioProject).filter_by(user_id=u.id).count(),"mentor_requests":db.query(MentorRequest).filter_by(user_id=u.id).count()}

@app.post("/api/ai/chat")
def ai_chat(x:ChatIn,u=Depends(current_user),db:Session=Depends(get_db)):
    mine=myskills(u,db)
    gaps=skill_gap(u,db)[:6]
    context=f"User: {u.name}. Role: {u.role}. Headline: {u.headline}. Location: {u.location}. Skills: {', '.join(s['name'] for s in mine)}. Priority gaps: {', '.join(g['skill'] for g in gaps)}."
    prompt=f"""You are Unique Path Career Copilot. Give concise, practical, personalized career guidance.
{context}
User asks: {x.message}
Answer in 6-10 useful bullets or short sections. Include concrete next actions, tools/resources, and measurable outcomes when relevant. Never claim to have applied for jobs or contacted people."""
    reply=ollama(prompt)
    if not reply:
        reply=f"I can help with that. Based on your current profile, start with your highest-priority skill gaps ({', '.join(g['skill'] for g in gaps[:3]) or 'add skills first'}), build one evidence-based project, and tailor your resume to the target role. For your question: {x.message}"
    return {"reply":reply}

@app.post("/api/ai/cover-letter")
def cover_letter(x:CoverLetterIn,u=Depends(current_user)):
    prompt=f"""Write a concise, natural cover letter for {u.name} applying for {x.role} at {x.company}. Resume/profile notes: {x.resume or u.bio}. Use specific evidence where available. Do not invent employers or degrees. 250 words maximum."""
    reply=ollama(prompt)
    if not reply: reply=f"Dear Hiring Team,\n\nI am excited to apply for the {x.role} role at {x.company}. My experience and project work have helped me build practical problem-solving skills, and I am eager to contribute while continuing to learn.\n\nI would welcome the opportunity to discuss how I can contribute to your team.\n\nSincerely,\n{u.name}"
    return {"reply":reply}

@app.post("/api/ai/interview-feedback")
def interview_feedback(x:InterviewIn,u=Depends(current_user)):
    prompt=f"""Act as a strict but supportive interview coach. Role: {x.role}. Question: {x.question}. Candidate answer: {x.answer}
Return: score out of 100, strengths, missing points, improved answer, and one follow-up question. Be concise."""
    reply=ollama(prompt)
    return {"reply":reply or "Good start. Use a STAR structure, add a measurable result, and connect your example directly to the target role."}

def extract_resume_bytes(filename,data):
    name=(filename or "").lower()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            r=PdfReader(io.BytesIO(data)); return "\n".join((p.extract_text() or "") for p in r.pages)
        except Exception: return ""
    if name.endswith(".docx"):
        try:
            from docx import Document
            import io
            d=Document(io.BytesIO(data)); return "\n".join(p.text for p in d.paragraphs)
        except Exception: return ""
    return data.decode("utf-8","ignore")

@app.post("/api/ats/upload")
async def ats_upload(file:UploadFile=File(...),u=Depends(current_user)):
    data=await file.read()
    if len(data)>8*1024*1024: raise HTTPException(413,"Resume must be 8 MB or smaller")
    text=extract_resume_bytes(file.filename,data)
    if not text.strip(): raise HTTPException(400,"Could not extract text. Try PDF, DOCX or TXT.")
    return {"filename":file.filename,"resume_text":text[:50000],"characters":len(text)}

@app.post("/api/ats/score")
def ats_score(x:ATSIn,u=Depends(current_user)):
    resume=x.resume_text.lower(); jd=x.job_description.lower()
    words=re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}",jd)
    stop={"the","and","for","with","from","this","that","you","your","are","will","have","has","our","job","role","work","team","who","what","into","their","they","using","about","years","year","also","more","than","not"}
    kws=[]
    for w in words:
        if w not in stop and w not in kws: kws.append(w)
    matched=[w for w in kws if w in resume]; missing=[w for w in kws if w not in resume]
    base=round(100*len(matched)/max(1,len(kws)))
    result={"score":min(100,base),"matched_keywords":matched[:25],"missing_keywords":missing[:25],"tip":"Add missing high-value keywords naturally, strengthen quantified achievements, and keep formatting simple."}
    prompt=f"""Evaluate this resume against this job description. Resume: {x.resume_text[:12000]}. Job: {x.job_description[:12000]}.
Return JSON with score 0-100, strengths array, missing_keywords array, improvements array, summary string. Be conservative and evidence-based."""
    ai=parse_json(ollama(prompt),{})
    if isinstance(ai,dict):
        result["score"]=max(0,min(100,int(ai.get("score",result["score"]))))
        result["missing_keywords"]=list(dict.fromkeys((ai.get("missing_keywords") or [])+result["missing_keywords"]))[:30]
        result["strengths"]=ai.get("strengths",[])
        result["improvements"]=ai.get("improvements",[])
        result["summary"]=ai.get("summary","")
    return result



# ---- Innovation / role intelligence APIs (v5.1) ----
def profile_snapshot(u, db):
    skills=myskills(u,db)
    projects=db.query(PortfolioProject).filter_by(user_id=u.id).all()
    results=db.query(AssessmentResult).filter_by(user_id=u.id).all()
    apps=db.query(Application).filter_by(user_id=u.id).all()
    return {
        "name":u.name,"role":u.role,"headline":u.headline,"location":u.location,"bio":u.bio,
        "skills":[{"name":s["name"],"level":s["level"]} for s in skills],
        "projects":[p.title for p in projects],"assessment_scores":[round(r.score,1) for r in results],
        "applications":[a.status for a in apps]
    }

def require_role(u, roles):
    if u.role not in roles: raise HTTPException(403, "Access restricted to: "+", ".join(roles))

class InnovationRole(BaseModel): role:str="Data Analyst"
class InnovationYears(BaseModel): years:int=3
class ExperimentIn(BaseModel): role:str; answer:str
class ProjectBuilderIn(BaseModel): role:str; idea:str=""
class TwinIn(BaseModel): question:str
class GrowthIn(BaseModel): projects:int=0; internships:int=0; interviews:int=0

@app.get("/api/innovation/career-dna")
def career_dna(u=Depends(current_user),db:Session=Depends(get_db)):
    skills=myskills(u,db); scores={"Technical Depth":50,"Analytical Thinking":50,"Communication":50,"Execution":50,"Adaptability":50}
    for s in skills:
        n=s["name"].lower(); v=s["level"]*7
        scores["Technical Depth"]+=v if n not in ["communication","leadership"] else 0
        scores["Analytical Thinking"]+=v if any(k in n for k in ["sql","data","statistics","machine","python","excel","power bi"]) else 0
        scores["Communication"]+=v if n in ["communication","leadership"] else 0
        scores["Execution"]+=v
    projects=db.query(PortfolioProject).filter_by(user_id=u.id).count(); results=db.query(AssessmentResult).filter_by(user_id=u.id).all()
    scores["Execution"]+=projects*8; scores["Adaptability"]+=len(results)*6
    scores={k:min(99,int(v)) for k,v in scores.items()}
    prompt=f"You are a career profiler. Given this evidence: {json.dumps(profile_snapshot(u,db))}. Return JSON with keys archetype, strengths (array 3), risks (array 3), next_actions (array 3). Be evidence-based and do not invent credentials."
    ai=parse_json(ollama(prompt),{})
    if not isinstance(ai,dict): ai={}
    return {"scores":scores,"archetype":ai.get("archetype","Evidence Builder"),"strengths":ai.get("strengths",["Practical learning","Problem solving","Growth mindset"]),"risks":ai.get("risks",["Limited evidence in weaker skills"]),"next_actions":ai.get("next_actions",["Build one measurable project","Complete a role-specific assessment","Practice a mock interview"]) }

@app.post("/api/innovation/future-self")
def future_self(x:InnovationYears,u=Depends(current_user),db:Session=Depends(get_db)):
    years=max(1,min(5,x.years)); prompt=f"Create 3 realistic {years}-year career scenarios for this user. Evidence: {json.dumps(profile_snapshot(u,db))}. Return JSON array of objects with title, fit_score 0-100, milestones array, risks array. No invented credentials."
    data=parse_json(ollama(prompt),[])
    if not isinstance(data,list) or len(data)<3:
        data=[{"title":"Data Analyst","fit_score":86,"milestones":["SQL + BI","Analytics project","Interview readiness"],"risks":["Needs stronger portfolio evidence"]},{"title":"AI Product Analyst","fit_score":82,"milestones":["Analytics","GenAI workflows","Product case studies"],"risks":["Needs product evidence"]},{"title":"Data Scientist","fit_score":74,"milestones":["Statistics","ML","End-to-end model"],"risks":["Higher technical depth required"]}]
    return {"years":years,"paths":data[:3]}

@app.post("/api/innovation/career-lab")
def career_lab(x:ExperimentIn,u=Depends(current_user),db:Session=Depends(get_db)):
    prompt=f"Act as a career experiment evaluator. Role: {x.role}. Candidate answer: {x.answer}. Profile: {json.dumps(profile_snapshot(u,db))}. Return JSON with score 0-100, strengths array, improvements array, feedback string, next_challenge string."
    data=parse_json(ollama(prompt),{})
    if not isinstance(data,dict): data={}
    return {"role":x.role,"score":int(data.get("score",88)),"strengths":data.get("strengths",["Structured reasoning"]),"improvements":data.get("improvements",["Add measurable evidence"]),"feedback":data.get("feedback","Good analytical instinct. Explain the decision and expected business impact."),"next_challenge":data.get("next_challenge","Explain your recommendation to a non-technical stakeholder.")}

@app.post("/api/innovation/project-builder")
def project_builder(x:ProjectBuilderIn,u=Depends(current_user),db:Session=Depends(get_db)):
    prompt=f"Create a portfolio-ready project blueprint for {x.role}. Idea: {x.idea or 'choose a useful real-world project'}. Candidate evidence: {json.dumps(profile_snapshot(u,db))}. Return JSON with title, problem, stack array, milestones array, metrics array, portfolio_evidence array."
    data=parse_json(ollama(prompt),{})
    if not isinstance(data,dict): data={}
    return data or {"title":x.idea or "Career Evidence Project","problem":"Solve a measurable real-world problem","stack":["Python","SQL","Git"],"milestones":["Define problem","Build MVP","Test","Deploy"],"metrics":["Accuracy","Time saved","User adoption"],"portfolio_evidence":["README","screenshots","demo","results"]}

@app.get("/api/innovation/job-match")
def job_match(u=Depends(current_user),db:Session=Depends(get_db)):
    mine={s["name"].lower():s["level"] for s in myskills(u,db)}; out=[]
    for o in db.query(Opportunity).filter_by(status="OPEN").order_by(Opportunity.created_at.desc()).all():
        req=[x.strip() for x in o.skills.split(",") if x.strip()]; matched=[r for r in req if r.lower() in mine]; score=round(100*len(matched)/max(1,len(req)))
        out.append({"id":o.id,"title":o.title,"company":o.company,"kind":o.kind,"score":score,"matched":matched,"missing":[r for r in req if r.lower() not in mine],"location":o.location})
    return sorted(out,key=lambda x:x["score"],reverse=True)[:12]

@app.get("/api/innovation/radar")
def radar(u=Depends(current_user),db:Session=Depends(get_db)):
    matches=job_match(u,db); return {"alerts":[{"priority":"HIGH" if x["score"]>=80 else "MEDIUM","reason":("Strong skill match" if x["score"]>=80 else "Close the listed skill gaps"),**x} for x in matches[:8]]}

@app.get("/api/innovation/career-mirror")
def career_mirror(target_role:str="Data Analyst",u=Depends(current_user),db:Session=Depends(get_db)):
    matches=job_match(u,db); relevant=[x for x in matches if target_role.lower() in x["title"].lower()]
    req=set();
    for x in relevant[:3]: req.update(x["missing"]+x["matched"])
    if not req: req={"SQL","Python","Data Analysis","Communication","Power BI"}
    mine={s["name"].lower():s["level"] for s in myskills(u,db)}
    rows=[]
    for r in sorted(req): rows.append({"skill":r,"current":mine.get(r.lower(),0),"target":4,"gap":max(0,4-mine.get(r.lower(),0))})
    return {"target_role":target_role,"skills":rows}

@app.get("/api/innovation/skill-graph")
def skill_graph(target_role:str="Data Analyst",u=Depends(current_user),db:Session=Depends(get_db)):
    base={"Data Analyst":["Python","SQL","Statistics","Data Analysis","Visualization","Power BI"],"Software Developer":["Git","JavaScript","React","FastAPI","SQL","Cloud"],"AI Engineer":["Python","Statistics","Machine Learning","Generative AI","FastAPI","Cloud"]}
    nodes=base.get(target_role,base["Data Analyst"]); mine={s["name"].lower():s["level"] for s in myskills(u,db)}
    return {"target_role":target_role,"nodes":[{"name":n,"level":mine.get(n.lower(),0),"status":"ready" if mine.get(n.lower(),0)>=3 else ("started" if mine.get(n.lower(),0)>0 else "next")} for n in nodes]}

@app.post("/api/innovation/career-twin")
def career_twin(x:TwinIn,u=Depends(current_user),db:Session=Depends(get_db)):
    prompt=f"You are the user's Digital Career Twin. Answer the question using only evidence in this profile: {json.dumps(profile_snapshot(u,db))}. Question: {x.question}. Return JSON with readiness 0-100, answer, evidence array, actions array."
    data=parse_json(ollama(prompt),{})
    if not isinstance(data,dict): data={}
    return {"readiness":int(data.get("readiness",82)),"answer":data.get("answer","Your strongest evidence is your current skill profile and completed work. Add one role-specific project to strengthen readiness."),"evidence":data.get("evidence",[]),"actions":data.get("actions",["Build one role-specific project","Complete a targeted assessment"])}

@app.post("/api/innovation/growth-simulator")
def growth_simulator(x:GrowthIn,u=Depends(current_user),db:Session=Depends(get_db)):
    base=50+min(20,db.query(UserSkill).filter_by(user_id=u.id).count()*3)+min(15,db.query(PortfolioProject).filter_by(user_id=u.id).count()*5)+min(15,db.query(AssessmentResult).filter_by(user_id=u.id).count()*3)
    score=min(99,base+x.projects*6+x.internships*12+x.interviews*4)
    return {"current":min(99,base),"simulated":score,"delta":score-min(99,base),"recommendation":"Prioritize portfolio evidence" if x.projects<2 else "Prioritize interview practice" if x.interviews<2 else "Keep building targeted evidence"}

@app.post("/api/innovation/rejection-learning/{application_id}")
def rejection_learning(application_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    a=db.get(Application,application_id)
    if not a or a.user_id!=u.id: raise HTTPException(404,"Application not found")
    o=db.get(Opportunity,a.opportunity_id)
    missing=[x.strip() for x in (o.skills or '').split(',') if x.strip()]
    mine={s["name"].lower() for s in myskills(u,db)}; gaps=[x for x in missing if x.lower() not in mine]
    prompt=f"Explain a rejection as a learning plan. Role: {o.title}. Required skills: {o.skills}. Candidate skills: {', '.join(mine)}. Return JSON with likely_reasons, learning_actions, evidence_to_add arrays. Do not claim the employer's private reasoning."
    data=parse_json(ollama(prompt),{})
    if not isinstance(data,dict): data={}
    return {"application_id":application_id,"status":a.status,"likely_reasons":data.get("likely_reasons",["Some required skills may not have enough visible evidence"]),"learning_actions":data.get("learning_actions",[f"Strengthen: {', '.join(gaps[:4]) or 'role-specific evidence'}"]),"evidence_to_add":data.get("evidence_to_add",["One measurable project","A stronger role-targeted resume bullet"]) }

@app.get("/api/institution/overview")
def institution_overview(u=Depends(current_user),db:Session=Depends(get_db)):
    require_role(u,["INSTITUTION","ADMIN"]); students=db.query(User).filter_by(role="STUDENT").all();
    return {"students":len(students),"applications":db.query(Application).count(),"open_opportunities":db.query(Opportunity).filter_by(status="OPEN").count(),"assessment_attempts":db.query(AssessmentResult).count(),"top_skills":[{"skill":s.name,"demand":s.demand,"holders":db.query(UserSkill).filter_by(skill_id=s.id).count()} for s in db.query(Skill).order_by(Skill.demand.desc()).limit(8).all()]}

@app.get("/api/institution/curriculum-translator")
def curriculum_translator(u=Depends(current_user),db:Session=Depends(get_db)):
    require_role(u,["INSTITUTION","ADMIN"]); skills={}
    for o in db.query(Opportunity).filter_by(status="OPEN").all():
        for s in [x.strip() for x in o.skills.split(',') if x.strip()]: skills[s]=skills.get(s,0)+1
    prompt=f"Translate industry demand into an academic curriculum plan. Demand: {json.dumps(skills)}. Return JSON with priority_skills array and modules array; each module has name, reason, activities, assessment."
    data=parse_json(ollama(prompt),{})
    if not isinstance(data,dict): data={}
    return {"demand":sorted([{"skill":k,"open_roles":v} for k,v in skills.items()],key=lambda x:x["open_roles"],reverse=True),"priority_skills":data.get("priority_skills",sorted(skills,key=skills.get,reverse=True)[:6]),"modules":data.get("modules",[])}

@app.get("/api/industry/talent")
def industry_talent(q:Optional[str]=None,u=Depends(current_user),db:Session=Depends(get_db)):
    require_role(u,["INDUSTRY","ADMIN"]); students=db.query(User).filter_by(role="STUDENT").all(); out=[]
    for s in students:
        skills=myskills(s,db); names=[x["name"] for x in skills]; score=0
        if q: score=sum(1 for n in names if q.lower() in n.lower())*20
        else: score=sum(x["level"] for x in skills)*5
        out.append({"id":s.id,"name":s.name,"headline":s.headline,"location":s.location,"score":min(99,score),"skills":names[:10],"projects":db.query(PortfolioProject).filter_by(user_id=s.id).count()})
    return sorted(out,key=lambda x:x["score"],reverse=True)[:30]

@app.get("/api/admin/overview")
def admin_overview(u=Depends(current_user),db:Session=Depends(get_db)):
    require_role(u,["ADMIN"]); return {"users":db.query(User).count(),"students":db.query(User).filter_by(role="STUDENT").count(),"institutions":db.query(User).filter_by(role="INSTITUTION").count(),"industry":db.query(User).filter_by(role="INDUSTRY").count(),"opportunities":db.query(Opportunity).count(),"applications":db.query(Application).count(),"assessments":db.query(AssessmentResult).count()}

@app.post("/api/seed")
def reseed(db:Session=Depends(get_db)):
    seed(db); return {"ok":True}
