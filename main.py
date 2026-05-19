from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Usuario, Juiz, Assessor
from auth import verificar_senha, criar_token
from schemas import LoginIn, LoginOut
from routers import usuarios, pessoas, processos, sorteio_router, conflitos
from scheduler import iniciar_scheduler
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Sorteio de Processos Judiciais")


@app.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.login == body.login,
                                 Usuario.ativo == True).first()
    if not u or not verificar_senha(body.senha, u.senha_hash):
        raise HTTPException(401, "Credenciais inválidas")
    token = criar_token(u.id)
    j = db.query(Juiz).filter(Juiz.usuario_id == u.id).first()
    a = db.query(Assessor).filter(Assessor.usuario_id == u.id).first()
    return LoginOut(
        token=token, perfil=u.perfil, nome=u.nome, usuario_id=u.id,
        juiz_id=j.id if j else None,
        assessor_id=a.id if a else None,
    )


app.include_router(usuarios.router)
app.include_router(pessoas.router)
app.include_router(processos.router)
app.include_router(sorteio_router.router)
app.include_router(conflitos.router)


@app.on_event("startup")
def _startup():
    if os.environ.get("DISABLE_SCHEDULER") != "1":
        iniciar_scheduler()


if os.path.isdir("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("frontend/login.html")


@app.get("/app")
def app_page():
    return FileResponse("frontend/app.html")
