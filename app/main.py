from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.api.endpoints import radar

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0"
)

# 1. Mount Static Files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Setup Templates (HTML)
templates = Jinja2Templates(directory="templates")

# 3. Include API Routes
app.include_router(radar.router, prefix="/api/v1/radar", tags=["Radar Control"])

# 4. The Main Dashboard Route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the Main Command Dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)