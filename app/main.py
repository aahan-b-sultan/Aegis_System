from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.models.user import User
from app.api.endpoints import radar, auth
from app.models.scan import ScanLog

# --- DATABASE IMPORTS ---
from app.db.session import engine
from app.models.scan import Base

# CREATE TABLES ON STARTUP
Base.metadata.create_all(bind=engine)
# ------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(radar.router, prefix="/api/v1/radar", tags=["Radar Control"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(radar.router, prefix="/api/v1/radar", tags=["Radar Control"])


# 1. NEW ROOT ROUTE (Landing Page)
# 1. NEW ROOT ROUTE (Landing Page)
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="welcome.html")

# 2. LOGIN ROUTE (Already exists, ensure it's there)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# 3. CHANGED DASHBOARD ROUTE (Now at /dashboard)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)