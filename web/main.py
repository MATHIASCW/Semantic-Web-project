from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Dossier des templates HTML
templates = Jinja2Templates(directory="web/templates")

@app.get("/test/page1", response_class=HTMLResponse)
async def page1(request: Request):
    return templates.TemplateResponse(
        "page1.html",
        {"request": request}
    )

@app.get("/test/page2", response_class=HTMLResponse)
async def page2(request: Request):
    return templates.TemplateResponse(
        "page2.html",
        {"request": request}
    )