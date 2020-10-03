from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker, relationship, aliased
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

SQLALCHEMY_DATABASE_URL = "sqlite:///./site.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session.configure(bind=engine)

class UserOrm(Base):
	__tablename__= 'users'
	id = Column(Integer, primary_key=True, nullable=False)
	username = Column(String(60), nullable=False, unique=True)
	email = Column(String(120), nullable=False, unique=True)
	password = Column(String(60), nullable=False)
	signup_dt = Column(DateTime, nullable=False, default=datetime.utcnow)
	applide_jobs = relationship("AppliedJobsOrm")

	def __repr__(self):
		return "<User(username='%s', email='%s')>" % (self.username, self.email)

class UserModel(BaseModel):
	id: int
	username: str
	email: str
	password: str
	signup_dt: Optional[datetime] = None

	class Config:
		orm_mode = True

class AppliedJobsOrm(Base):
	__tablename__ = 'applied_jobs'
	id = Column(Integer, primary_key=True, nullable=False)
	title = Column(String(120), nullable=False)
	desc = Column(Text, nullable=False)
	applStatus = Column(String(60), nullable=False, default='Applied')
	user_id = Column(Integer, ForeignKey('users.id'))

	def __repr__(self):
		return "<User(title='%s', desc='%s')>" % (self.title, self.desc)

class AppliedJobsModel(BaseModel):
	id: int
	title: str
	desc: str
	applStatus: str = 'Applied'
	user_id: int

	class Config:
		orm_mode = True				

class JobsOrm(Base):
	__tablename__ = 'jobs'
	id = Column(Integer, primary_key=True, nullable=False)
	title = Column(String(120), nullable=False)
	desc = Column(Text, nullable=False)
	job_posted = Column(DateTime, nullable=False, default=datetime.utcnow)

	def __repr__(self):
		return "<User(title='%s', desc='%s')>" % (self.title, self.desc)

class JobsModel(BaseModel):
	id: int
	title: str
	desc: str
	job_posted: Optional[datetime] = None

	class Config:
		orm_mode = True

# job = JobsModel(**job_1)

app = FastAPI()

templates = Jinja2Templates(directory='templates')

cur_session = session()

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
	return templates.TemplateResponse('home.html', {"request": request})


@app.get('/jobs')
async def get_jobs():
	jobs_mod = []
	json_out = {}
	jobs_orm = cur_session.query(JobsOrm).all()
	for job in jobs_orm:
		jobs_mod.append(JobsModel.from_orm(job))
	json_out['data'] = jobs_mod
	return jsonable_encoder(json_out)

@app.get('/jobs/{id}')
async def get_job(id: int):	
	json_out = {}
	job_orm = cur_session.query(JobsOrm).filter(JobsOrm.id==id).first()
	jobMod = JobsModel.from_orm(job_orm)
	json_out['data'] = jobMod
	return jsonable_encoder(json_out)

@app.post('/jobs/create_job/')
async def create_job(job: JobsModel):
	job_create = JobsOrm()
	if job.title:
		job_create.title = job.title
		job_create.desc = job.desc
	cur_session.add(job_create)
	cur_session.commit()
	return {"response_message": f"Job {job_create.title} Created Successfully"}

@app.delete('/jobs/delete_job/{id}')
async def delete_job(id: int):
	job_orm = cur_session.query(JobsOrm).filter(JobsOrm.id==id).first()
	job_title = job_orm.title
	if job_orm.title:
		cur_session.delete(job_orm)
		cur_session.commit()
	return {"response_message": f"Job {job_title} Deleted Successfully"}

@app.post('/jobs/{id}/apply')
async def apply_job(id):
	job_orm = cur_session.query(JobsOrm).filter(JobsOrm.id==id).first()
	# job = JobsModel.from_orm(job_orm)
	user_orm = cur_session.query(UserOrm).filter(UserOrm.username=='yuvi').first()
	# user = UserModel.from_orm(user_orm)
	applied_already_orm = cur_session.query(AppliedJobsOrm).filter(AppliedJobsOrm.user_id==user_orm.id)
	for applied_already in applied_already_orm:
		# applied = AppliedJobsModel.from_orm(applied_already)
		if applied_already.title.upper() == job_orm.title.upper():
			return {"response_message": f"Already Applied For This Job {job_orm.title}"}
		else:
			apply_job = AppliedJobsOrm()
			apply_job.title = job_orm.title
			apply_job.desc = job_orm.desc
			apply_job.user_id = user_orm.id
			cur_session.add(apply_job)
			cur_session.commit()
			return {"response_message": f"Your Application Submitted Successfully for {job_orm.title}"}