from datetime import datetime
from sqlalchemy import Column,Integer,String,Text,DateTime,Float,Boolean,ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String(120),nullable=False)
    email=Column(String(180),unique=True,nullable=False,index=True)
    password_hash=Column(String(300),nullable=False)
    role=Column(String(40),default='STUDENT',nullable=False)
    avatar=Column(String(500),default='')
    headline=Column(String(250),default='')
    location=Column(String(150),default='')
    bio=Column(Text,default='')
    phone=Column(String(50),default='')
    created_at=Column(DateTime,default=datetime.utcnow)

class Skill(Base):
    __tablename__='skills'
    id=Column(Integer,primary_key=True)
    name=Column(String(100),unique=True,nullable=False)
    category=Column(String(80),default='Technical')
    demand=Column(Float,default=50)

class UserSkill(Base):
    __tablename__='user_skills'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    skill_id=Column(Integer,ForeignKey('skills.id'),nullable=False)
    level=Column(Integer,default=1)
    evidence=Column(String(300),default='')

class Assessment(Base):
    __tablename__='assessments'
    id=Column(Integer,primary_key=True)
    title=Column(String(200),nullable=False)
    skill_id=Column(Integer,ForeignKey('skills.id'))
    duration_minutes=Column(Integer,default=20)
    difficulty=Column(String(40),default='Intermediate')
    questions_json=Column(Text,default='[]')

class AssessmentResult(Base):
    __tablename__='assessment_results'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    assessment_id=Column(Integer,ForeignKey('assessments.id'))
    score=Column(Float,default=0)
    completed_at=Column(DateTime,default=datetime.utcnow)

class Opportunity(Base):
    __tablename__='opportunities'
    id=Column(Integer,primary_key=True)
    kind=Column(String(30),default='JOB')
    title=Column(String(200),nullable=False)
    company=Column(String(180),nullable=False)
    location=Column(String(150),default='Remote')
    description=Column(Text,default='')
    skills=Column(String(500),default='')
    salary=Column(String(120),default='')
    employment_type=Column(String(80),default='Full-time')
    deadline=Column(String(40),default='')
    posted_by=Column(Integer,ForeignKey('users.id'))
    status=Column(String(30),default='OPEN')
    created_at=Column(DateTime,default=datetime.utcnow)

class Application(Base):
    __tablename__='applications'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    opportunity_id=Column(Integer,ForeignKey('opportunities.id'))
    status=Column(String(50),default='APPLIED')
    cover_note=Column(Text,default='')
    applied_at=Column(DateTime,default=datetime.utcnow)

class PortfolioProject(Base):
    __tablename__='portfolio_projects'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    title=Column(String(200),nullable=False)
    description=Column(Text,default='')
    tech_stack=Column(String(400),default='')
    project_url=Column(String(500),default='')
    image_url=Column(String(500),default='')

class Mentor(Base):
    __tablename__='mentors'
    id=Column(Integer,primary_key=True)
    name=Column(String(150),nullable=False)
    expertise=Column(String(300),default='')
    company=Column(String(180),default='')
    experience_years=Column(Integer,default=5)
    rating=Column(Float,default=4.7)
    availability=Column(String(80),default='Weekends')

class MentorRequest(Base):
    __tablename__='mentor_requests'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    mentor_id=Column(Integer,ForeignKey('mentors.id'))
    message=Column(Text,default='')
    status=Column(String(40),default='PENDING')
    created_at=Column(DateTime,default=datetime.utcnow)

class Course(Base):
    __tablename__='courses'
    id=Column(Integer,primary_key=True)
    title=Column(String(200),nullable=False)
    provider=Column(String(150),default='Unique Path')
    category=Column(String(100),default='Career')
    level=Column(String(50),default='Beginner')
    duration=Column(String(80),default='6 weeks')
    url=Column(String(500),default='')

class Certification(Base):
    __tablename__='certifications'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    name=Column(String(200),nullable=False)
    issuer=Column(String(150),default='')
    credential_url=Column(String(500),default='')
    issue_date=Column(String(50),default='')

class Notification(Base):
    __tablename__='notifications'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    title=Column(String(200),nullable=False)
    message=Column(Text,default='')
    read=Column(Boolean,default=False)
    created_at=Column(DateTime,default=datetime.utcnow)
