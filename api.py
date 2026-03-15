from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gestorLLM import GestorLLM
import uvicorn
import socket

app = FastAPI(title="Aurora API")

# Configurar CORS por si fuera necesario en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Aurora al arranque
gestor = None

@app.on_event("startup")
async def startup_event():
    global gestor
    print("Iniciando GestorLLM para la API...")
    gestor = GestorLLM()
    # Identificar la IP local orientativa (depende de la red, pero ayuda en consola)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"\n==========================================")
        print(f"Aurora API conectable en red local en: http://{ip}:8000")
        print(f"==========================================\n")
    except:
        pass

@app.on_event("shutdown")
async def shutdown_event():
    global gestor
    if gestor:
        print("Guardando sesión de Aurora API...")
        gestor.guardar_sesion()

class ChatRequest(BaseModel):
    mensaje: str

class ChatResponse(BaseModel):
    respuesta: str
    
class HistoryResponse(BaseModel):
    mensajes: list[dict]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    global gestor
    if not gestor:
        raise HTTPException(status_code=500, detail="GestorLLM no inicializado")
    
    # Si la petición está vacía, ignoramos
    if not req.mensaje.strip():
        raise HTTPException(status_code=400, detail="Mensaje vacío")
        
    try:
        respuesta = gestor.obtener_respuesta(req.mensaje)
        return ChatResponse(respuesta=respuesta)
    except Exception as e:
        print(f"[API Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=HistoryResponse)
async def history_endpoint():
    global gestor
    if not gestor:
         raise HTTPException(status_code=500, detail="GestorLLM no inicializado")
    
    # Devolver el historial actual (la sesión anterior cargada o la actual)
    historial = gestor.memoria.obtener_historial()
    return HistoryResponse(mensajes=historial)

@app.get("/")
def read_root():
    return {"status": "Aurora API is running"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
