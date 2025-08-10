from fastapi import FastAPI, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import json

app = FastAPI(title="NewsFrontier API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)  # Don't auto-error if no header
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

fake_users_db = {
    "testuser": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": pwd_context.hash("password123"),
        "is_admin": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    expires: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class RegisterResponse(BaseModel):
    user_id: int
    message: str

class TodayResponse(BaseModel):
    date: str
    total_articles: int
    clusters_count: int
    top_topics: List[str]
    summary: str
    trending_keywords: List[str]

class Topic(BaseModel):
    id: int
    name: str
    keywords: List[str]
    active: bool

class TopicsResponse(BaseModel):
    topics: List[Topic]

class TopicRequest(BaseModel):
    name: str
    keywords: List[str]

class TopicCreateResponse(BaseModel):
    id: int
    message: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: str
    updated_at: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: str
    updated_at: str

class Cluster(BaseModel):
    id: int
    title: str
    article_count: int
    summary: str

class TopicDetailResponse(BaseModel):
    topic: Topic
    clusters: List[Cluster]

class Article(BaseModel):
    id: int
    title: str
    source: str
    timestamp: str

class ClusterDetail(BaseModel):
    id: int
    title: str
    summary: str
    articles: List[Article]

class ClusterDetailResponse(BaseModel):
    cluster: ClusterDetail

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    token = None
    
    # First try to get token from Authorization header
    if credentials:
        token = credentials.credentials
    else:
        # If no Authorization header, try to get token from cookie
        token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    user = fake_users_db.get(request.username)
    if not user or not pwd_context.verify(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": request.username})
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )
    
    return LoginResponse(
        token=access_token,
        user_id=user["id"],
        expires=expires.isoformat() + "Z"
    )

@app.post("/api/logout")
async def logout(response: Response, username: str = Depends(verify_token)):
    # Clear the auth cookie
    response.delete_cookie(key="auth_token", samesite="lax")
    return {"message": "Logged out successfully"}

@app.get("/api/user/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token)):
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
        updated_at=user["updated_at"]
    )

@app.post("/api/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    if request.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user_id = len(fake_users_db) + 1
    current_time = datetime.utcnow().isoformat() + "Z"
    fake_users_db[request.username] = {
        "id": new_user_id,
        "username": request.username,
        "email": request.email,
        "password_hash": pwd_context.hash(request.password),
        "is_admin": False,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    return RegisterResponse(
        user_id=new_user_id,
        message="Registration successful"
    )

@app.get("/api/today", response_model=TodayResponse)
async def get_today(username: str = Depends(verify_token)):
    return TodayResponse(
        date="2024-01-01",
        total_articles=247,
        clusters_count=15,
        top_topics=["Technology", "Politics", "Sports"],
        summary="AI-generated overview of today's major news trends...",
        trending_keywords=["AI", "election", "climate"]
    )

@app.get("/api/topics", response_model=TopicsResponse)
async def get_topics(username: str = Depends(verify_token)):
    fake_topics = [
        Topic(id=1, name="Technology", keywords=["AI", "tech", "software"], active=True),
        Topic(id=2, name="Politics", keywords=["election", "government"], active=False),
        Topic(id=3, name="Sports", keywords=["football", "basketball", "soccer"], active=True)
    ]
    
    return TopicsResponse(topics=fake_topics)

@app.post("/api/topics", response_model=TopicCreateResponse)
async def create_topic(request: TopicRequest, username: str = Depends(verify_token)):
    new_topic_id = 4
    return TopicCreateResponse(
        id=new_topic_id,
        message="Topic created successfully"
    )

@app.get("/api/topic/{topic_id}", response_model=TopicDetailResponse)
async def get_topic_detail(topic_id: int, username: str = Depends(verify_token)):
    fake_topic = Topic(id=topic_id, name="Technology", keywords=["AI", "tech", "software"], active=True)
    fake_clusters = [
        Cluster(id=101, title="AI Breakthrough", article_count=5, summary="Major AI developments..."),
        Cluster(id=102, title="Tech Earnings", article_count=8, summary="Quarterly results...")
    ]
    
    return TopicDetailResponse(
        topic=fake_topic,
        clusters=fake_clusters
    )

@app.get("/api/cluster/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster_detail(cluster_id: int, username: str = Depends(verify_token)):
    fake_articles = [
        Article(id=1001, title="OpenAI Announces...", source="TechNews", timestamp="2024-01-01T10:00:00Z"),
        Article(id=1002, title="Google Responds...", source="Reuters", timestamp="2024-01-01T11:00:00Z")
    ]
    
    fake_cluster = ClusterDetail(
        id=cluster_id,
        title="AI Breakthrough",
        summary="Comprehensive cluster summary...",
        articles=fake_articles
    )
    
    return ClusterDetailResponse(cluster=fake_cluster)

@app.get("/")
async def root():
    return {"message": "NewsFrontier API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)