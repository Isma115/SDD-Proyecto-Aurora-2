import socket
import threading
import time

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.src.controllers.llm_controller import GestorLLM
from backend.src.models.estadisticas_model import GestorEstadisticas
from pydantic import BaseModel

class ChatRequest(BaseModel):
    mensaje: str


class ChatResponse(BaseModel):
    respuesta: str


class HistoryResponse(BaseModel):
    mensajes: list[dict]


def obtener_ip_local():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def crear_app(gestor_inicial=None, gestor_factory=GestorLLM, gestor_estadisticas=None):
    app = FastAPI(title="Aurora API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.gestor = gestor_inicial
    app.state.gestor_estadisticas = gestor_estadisticas
    app.state.gestor_compartido = gestor_inicial is not None
    app.state.gestor_lock = threading.RLock()

    @app.on_event("startup")
    async def startup_event():
        if app.state.gestor is None:
            print("Iniciando GestorLLM para la API...")
            app.state.gestor = gestor_factory()
            ip = obtener_ip_local()
            print("\n==========================================")
            print(f"Aurora API conectable en red local en: http://{ip}:8000")
            print("==========================================\n")

    @app.on_event("shutdown")
    async def shutdown_event():
        gestor = app.state.gestor
        if gestor and not app.state.gestor_compartido:
            print("Guardando sesión de Aurora API...")
            gestor.guardar_sesion()

    def obtener_gestor():
        gestor = app.state.gestor
        if not gestor:
            raise HTTPException(status_code=500, detail="GestorLLM no inicializado")
        return gestor

    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(req: ChatRequest):
        gestor = obtener_gestor()
        if not req.mensaje.strip():
            raise HTTPException(status_code=400, detail="Mensaje vacío")

        try:
            with app.state.gestor_lock:
                respuesta = gestor.obtener_respuesta(req.mensaje)
            return ChatResponse(respuesta=respuesta)
        except Exception as exc:
            print(f"[API Error]: {exc}")
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/history", response_model=HistoryResponse)
    async def history_endpoint():
        gestor = obtener_gestor()
        with app.state.gestor_lock:
            historial = gestor.memoria.obtener_historial()
        return HistoryResponse(mensajes=historial)

    @app.get("/stats")
    async def stats_endpoint():
        ge = app.state.gestor_estadisticas
        if not ge:
            raise HTTPException(status_code=503, detail="Estadísticas no disponibles")
        return ge.obtener_resumen()

    @app.get("/")
    def read_root():
        return {
            "status": "Aurora API is running",
            "server_ip": obtener_ip_local(),
        }

    return app


class AuroraEmbeddedAPIServer:
    def __init__(self, gestor, host="0.0.0.0", port=8000, gestor_estadisticas=None):
        self.gestor = gestor
        self.gestor_estadisticas = gestor_estadisticas
        self.host = host
        self.port = port
        self.ip_local = obtener_ip_local()
        self.url_local = f"http://{self.ip_local}:{self.port}"
        self.server = None
        self.thread = None

    def start(self, wait_timeout=10):
        if self.thread and self.thread.is_alive():
            return

        app = crear_app(gestor_inicial=self.gestor, gestor_estadisticas=self.gestor_estadisticas)
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            reload=False,
            access_log=False,
            log_level="warning",
        )
        self.server = uvicorn.Server(config)
        self.server.install_signal_handlers = lambda: None
        self.thread = threading.Thread(target=self.server.run, daemon=True, name="aurora-api")
        self.thread.start()

        inicio = time.time()
        while time.time() - inicio < wait_timeout:
            if self.server.started:
                return
            if not self.thread.is_alive():
                break
            time.sleep(0.05)

        raise RuntimeError(
            f"No se pudo iniciar el servidor API embebido en el puerto {self.port}."
        )

    def stop(self, wait_timeout=5):
        if not self.server:
            return

        self.server.should_exit = True
        if self.thread and self.thread.is_alive():
            self.thread.join(wait_timeout)
        self.server = None
        self.thread = None


app = crear_app()

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
