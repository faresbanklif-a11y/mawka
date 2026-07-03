import os
import sys
import json
import uuid
import shutil
import zipfile
import asyncio
import subprocess
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

import psutil
from fastapi import FastAPI, Request, Response, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, event
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
import bcrypt
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
import httpx
import aiofiles

import config

# تحميل الإعدادات من ملف .env
load_dotenv()

# ─── Database Setup ───
engine = create_engine(config.DATABASE_URL, connect_args=config.SQLALCHEMY_ENGINE_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# إعداد خاص لقاعدة بيانات SQLite
if "sqlite" in config.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

# دالة مساعدة للحصول على الوقت الحالي بصيغة UTC متوافقة مع الإصدارات الحديثة
def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ─── Models ───
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    hashed_password = Column(String(200))
    avatar = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(200), default="")
    reset_token = Column(String(200), default="")
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    last_login = Column(DateTime, nullable=True)
    provider = Column(String(50), default="email")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text, default="")
    path = Column(String(500))
    main_file = Column(String(200), default="main.py")
    language = Column(String(50), default="python")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    owner = relationship("User", back_populates="projects")

class ProcessLog(Base):
    __tablename__ = "process_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    pid = Column(Integer)
    output = Column(Text, default="")
    error = Column(Text, default="")
    status = Column(String(20), default="running")
    started_at = Column(DateTime, default=get_utc_now)
    stopped_at = Column(DateTime, nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(500))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=get_utc_now)
    expires_at = Column(DateTime)
    user = relationship("User", back_populates="sessions")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100))
    details = Column(Text, default="")
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=get_utc_now)

Base.metadata.create_all(bind=engine)

# ─── Auth Setup ───
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = get_utc_now() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

# 🛠️ تصحيح دالة التحقق لتفادي تعارض مكتبة passlib
def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# 🛠️ تصحيح دالة التشفير لتفادي تعارض مكتبة passlib والـ 72 بايت
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("access_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except (JWTError, ValueError):
        return None

async def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = await get_current_user(request, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = await require_auth(request, db)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ─── Pydantic Schemas ───
class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

class ChangeEmailSchema(BaseModel):
    new_email: str
    password: str

class ProjectCreateSchema(BaseModel):
    name: str
    description: str = ""

class FileCreateSchema(BaseModel):
    name: str
    content: str = ""
    is_folder: bool = False

class FileUpdateSchema(BaseModel):
    content: str

class FileRenameSchema(BaseModel):
    new_name: str

class TerminalCommandSchema(BaseModel):
    command: str

class PipInstallSchema(BaseModel):
    package: str

# ─── Process Manager ───
class ProcessManager:
    def __init__(self):
        self.processes = {}

    def start(self, project_path: str, main_file: str, project_id: int, db: Session) -> int:
        full_path = os.path.join(project_path, main_file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {main_file}")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        proc = subprocess.Popen(
            [sys.executable, "-u", main_file],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        log = ProcessLog(project_id=project_id, pid=proc.pid, status="running")
        db.add(log)
        db.commit()
        db.refresh(log)
        self.processes[log.id] = {"process": proc, "log_id": log.id, "project_id": project_id}
        return log.id

    def stop(self, log_id: int):
        if log_id in self.processes:
            info = self.processes[log_id]
            proc = info["process"]
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            del self.processes[log_id]

    def get_output(self, log_id: int) -> tuple:
        if log_id not in self.processes:
            return "", "", "stopped"
        info = self.processes[log_id]
        proc = info["process"]
        stdout_data = ""
        stderr_data = ""
        try:
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                stdout_data += line.decode("utf-8", errors="replace")
        except:
            pass
        try:
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                stderr_data += line.decode("utf-8", errors="replace")
        except:
            pass
        status = "running" if proc.poll() is None else "stopped"
        return stdout_data, stderr_data, status

    def is_running(self, log_id: int) -> bool:
        if log_id not in self.processes:
            return False
        return self.processes[log_id]["process"].poll() is None

    def get_project_processes(self, project_id: int) -> list:
        result = []
        for lid, info in self.processes.items():
            if info["project_id"] == project_id:
                proc = info["process"]
                result.append({
                    "log_id": lid,
                    "pid": proc.pid,
                    "running": proc.poll() is None
                })
        return result

process_manager = ProcessManager()

# ─── App Setup ───
app = FastAPI(title="PyHost - Python Hosting Platform", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ─── Helper Functions ───
def get_project_path(user_id: int, project_name: str) -> str:
    p = os.path.join(config.PROJECTS_DIR, str(user_id), project_name)
    os.makedirs(p, exist_ok=True)
    return p

def log_activity(db: Session, user_id: int, action: str, details: str, ip: str):
    log = ActivityLog(user_id=user_id, action=action, details=details, ip_address=ip)
    db.add(log)
    db.commit()

def get_system_stats():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    try:
        temps = psutil.sensors_temperatures()
        cpu_temp = None
        for name, entries in temps.items():
            if entries:
                cpu_temp = entries[0].current
                break
    except:
        cpu_temp = None
    return {
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(),
        "cpu_temp": cpu_temp,
        "ram_total": memory.total,
        "ram_used": memory.used,
        "ram_percent": memory.percent,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_percent": disk.percent,
        "net_sent": net.bytes_sent,
        "net_recv": net.bytes_recv,
        "threads": psutil.cpu_count(logical=True),
        "processes": len(psutil.pids()),
        "boot_time": psutil.boot_time()
    }

def ensure_admin(db: Session):
    admin = db.query(User).filter(User.email == config.ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            username="admin",
            email=config.ADMIN_EMAIL,
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin

def clean_old_logs(db: Session):
    cutoff = get_utc_now() - timedelta(days=7)
    db.query(ProcessLog).filter(ProcessLog.stopped_at < cutoff).delete()
    db.commit()

# ─── API Routes ───

@app.route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Please login to access dashboard"})

    projects = db.query(Project).filter(Project.owner_id == user.id).all()
    stats = get_system_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "projects": projects,
        "stats": stats
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/api/auth/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    user.last_login = get_utc_now()
    db.commit()

    log_activity(db, user.id, "login", f"User logged in from {request.client.host}", request.client.host)

    response = JSONResponse({"message": "Login successful", "access_token": access_token})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        expires=get_utc_now() + timedelta(days=7),
        samesite="lax"
    )
    return response

@app.post("/api/auth/register")
async def register(request: Request, user_data: RegisterSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user_data.password)
    verification_token = secrets.token_urlsafe(32)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(db, new_user.id, "register", f"User registered from {request.client.host}", request.client.host)

    return {"message": "Registration successful. Please check your email for verification."}

@app.post("/api/auth/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if user:
        log_activity(db, user.id, "logout", f"User logged out from {request.client.host}", request.client.host)

    response = JSONResponse({"message": "Logout successful"})
    response.delete_cookie("access_token")
    return response

@app.post("/api/auth/change-password")
async def change_password(request: Request, data: ChangePasswordSchema, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    user.hashed_password = get_password_hash(data.new_password)
    db.commit()

    log_activity(db, user.id, "change_password", "Password changed successfully", request.client.host)
    return {"message": "Password changed successfully"}

@app.post("/api/auth/change-email")
async def change_email(request: Request, data: ChangeEmailSchema, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    existing_user = db.query(User).filter(User.email == data.new_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    user.email = data.new_email
    db.commit()

    log_activity(db, user.id, "change_email", f"Email changed to {data.new_email}", request.client.host)
    return {"message": "Email changed successfully"}

@app.post("/api/auth/google")
async def google_login(request: Request, token: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token")

        user_data = response.json()
        email = user_data["email"]

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                username=email.split("@")[0],
                email=email,
                hashed_password="",
                provider="google",
                is_verified=True,
                avatar=user_data.get("picture", "")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.avatar = user_data.get("picture", user.avatar)
            db.commit()

        access_token = create_access_token(data={"sub": str(user.id)})
        user.last_login = get_utc_now()
        db.commit()

        log_activity(db, user.id, "login", f"Google login from {request.client.host}", request.client.host)

        response = JSONResponse({"message": "Login successful", "access_token": access_token})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            expires=get_utc_now() + timedelta(days=7),
            samesite="lax"
        )
        return response

@app.post("/api/auth/github")
async def github_login(request: Request, token: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid GitHub token")

        user_data = response.json()
        email = user_data.get("email", f"{user_data['id']}@github.local")
        login = user_data["login"]

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                username=login,
                email=email,
                hashed_password="",
                provider="github",
                is_verified=True,
                avatar=user_data.get("avatar_url", "")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.avatar = user_data.get("avatar_url", user.avatar)
            db.commit()

        access_token = create_access_token(data={"sub": str(user.id)})
        user.last_login = get_utc_now()
        db.commit()

        log_activity(db, user.id, "login", f"GitHub login from {request.client.host}", request.client.host)

        response = JSONResponse({"message": "Login successful", "access_token": access_token})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            expires=get_utc_now() + timedelta(days=7),
            samesite="lax"
        )
        return response

@app.get("/api/user/profile")
async def get_profile(request: Request, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "is_admin": user.is_admin
    }

@app.get("/api/projects")
async def get_projects(request: Request, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    projects = db.query(Project).filter(Project.owner_id == user.id).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "path": p.path, "created_at": p.created_at} for p in projects]

@app.post("/api/projects")
async def create_project(request: Request, data: ProjectCreateSchema, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project_count = db.query(Project).filter(Project.owner_id == user.id).count()
    if project_count >= config.MAX_PROJECTS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum {config.MAX_PROJECTS_PER_USER} projects allowed per user")

    project_path = get_project_path(user.id, data.name)
    project = Project(
        name=data.name,
        description=data.description,
        path=project_path,
        owner_id=user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_activity(db, user.id, "create_project", f"Created project {data.name}", request.client.host)
    return {"id": project.id, "name": project.name, "message": "Project created successfully"}

@app.get("/api/projects/{project_id}")
async def get_project(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "path": project.path,
        "main_file": project.main_file,
        "language": project.language,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }

@app.delete("/api/projects/{project_id}")
async def delete_project(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = db.query(ProcessLog).filter(ProcessLog.project_id == project_id, ProcessLog.status == "running").all()
    for log in logs:
        process_manager.stop(log.id)
    if os.path.exists(project.path):
        shutil.rmtree(project.path)
    db.delete(project)
    db.commit()
    log_activity(db, user.id, "delete_project", f"Deleted project {project.name}", request.client.host)
    return {"message": "Project deleted successfully"}

@app.post("/api/projects/{project_id}/upload")
async def upload_files(request: Request, project_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    os.makedirs(project.path, exist_ok=True)
    for file in files:
        if not any(file.filename.lower().endswith(ext) for ext in config.ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail=f"File type {file.filename.split('.')[-1]} not allowed")
        file_path = os.path.join(project.path, file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    log_activity(db, user.id, "upload_files", f"Uploaded {len(files)} files to project {project.name}", request.client.host)
    return {"message": f"Successfully uploaded {len(files)} files"}

@app.post("/api/projects/{project_id}/upload-zip")
async def upload_zip(request: Request, project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    os.makedirs(project.path, exist_ok=True)
    zip_path = os.path.join(project.path, file.filename)
    async with aiofiles.open(zip_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(project.path)
    os.remove(zip_path)
    log_activity(db, user.id, "upload_zip", f"Extracted ZIP file to project {project.name}", request.client.host)
    return {"message": "ZIP file uploaded and extracted successfully"}

@app.post("/api/projects/{project_id}/run")
async def run_project(request: Request, project_id: int, data: dict = {"main_file": "main.py"}, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    main_file = data.get("main_file", project.main_file)
    if not main_file:
        raise HTTPException(status_code=400, detail="Main file not specified")
    if not os.path.exists(os.path.join(project.path, main_file)):
        raise HTTPException(status_code=404, detail=f"File {main_file} not found")
    project.main_file = main_file
    db.commit()
    log_id = process_manager.start(project.path, main_file, project_id, db)
    log_activity(db, user.id, "run_project", f"Started project {project.name} with {main_file}", request.client.host)
    return {"log_id": log_id, "message": "Project started successfully"}

@app.post("/api/projects/{project_id}/stop/{log_id}")
async def stop_project(request: Request, project_id: int, log_id: int, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    log = db.query(ProcessLog).filter(ProcessLog.id == log_id, ProcessLog.project_id == project_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Process not found")
    process_manager.stop(log_id)
    log.status = "stopped"
    log.stopped_at = get_utc_now()
    db.commit()
    log_activity(db, user.id, "stop_project", f"Stopped project {project.name}", request.client.host)
    return {"message": "Project stopped successfully"}

@app.get("/api/projects/{project_id}/output/{log_id}")
async def get_project_output(request: Request, project_id: int, log_id: int, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    log = db.query(ProcessLog).filter(ProcessLog.id == log_id, ProcessLog.project_id == project_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Process not found")
    stdout, stderr, status = process_manager.get_output(log_id)
    if status != log.status:
        log.status = status
        if status == "stopped":
            log.stopped_at = get_utc_now()
        db.commit()
    return {
        "stdout": stdout,
        "stderr": stderr,
        "status": status,
        "pid": log.pid,
        "started_at": log.started_at.isoformat(),
        "stopped_at": log.stopped_at.isoformat() if log.stopped_at else None
    }

@app.get("/api/projects/{project_id}/processes")
async def get_project_processes(request: Request, project_id: int, db: Session = Depends(get_db)):
    user = await require_auth(request, db)
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    processes = process_manager.get_project_processes(project_id)
    logs = db.query(ProcessLog).filter(ProcessLog.project_id == project_id).all()
    result = []
    for log in logs:
        proc = next((p for p in processes if p["log_id"] == log.id), None)
        if proc:
            result.append({
                "id": log.id,
                "pid": log.pid,
                "status": log.status,
                "running": proc["running"],
                "started_at": log.started_at.isoformat(),
                "stopped_at": log.stopped_at.isoformat() if log.stopped_at else None
            })
    return result

# ─── Application Lifecycle ───
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        ensure_admin(db)
        clean_old_logs(db)
        print(f"Starting application in {config.ENVIRONMENT} mode")
        print(f"Debug mode: {config.DEBUG}")
        print(f"Database URL: {config.DATABASE_URL}")
        print(f"Using database: {'PostgreSQL' if 'postgresql' in config.DATABASE_URL else 'SQLite'}")
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        raise
    finally:
        db.close()

@app.on_event("startup")
async def init_directories():
    try:
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        os.makedirs(config.PROJECTS_DIR, exist_ok=True)
        print(f"Directories created/verified: {config.UPLOAD_DIR}, {config.PROJECTS_DIR}")
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    for log_id in list(process_manager.processes.keys()):
        process_manager.stop(log_id)

# ─── Main Execution ───
if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = config.DEBUG and os.environ.get("RELOAD", "true").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
