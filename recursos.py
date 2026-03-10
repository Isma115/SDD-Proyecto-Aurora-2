import json
import os

class GestorRecursos:
    def __init__(self):
        self.historial_conversacion = []
        self.archivo_memoria = "Recursos/memoria.json"
        self.conocimiento = self._cargar_memoria()
        
    def _cargar_memoria(self):
        if os.path.exists(self.archivo_memoria):
            try:
                with open(self.archivo_memoria, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    if isinstance(datos, list):
                        # Limpiar duplicados existentes al cargar
                        vistos = set()
                        limpios = []
                        for r in datos:
                            norm = self._normalizar_texto(r)
                            if norm not in vistos:
                                vistos.add(norm)
                                limpios.append(r)
                        return limpios
                    return []
            except json.JSONDecodeError:
                return []
        return []

    def _normalizar_texto(self, texto):
        # Normaliza para comparación: minúsculas, sin espacios extra, sin punto final
        if not texto:
            return ""
        t = str(texto).lower().strip()
        if t.endswith('.'):
            t = t[:-1].strip()
        return t

    def guardar_recuerdo(self, recuerdo):
        nuevo_norm = self._normalizar_texto(recuerdo)
        # Verificar si ya existe un recuerdo similar
        for r in self.conocimiento:
            if self._normalizar_texto(r) == nuevo_norm:
                return
        
        self.conocimiento.append(recuerdo)
        with open(self.archivo_memoria, "w", encoding="utf-8") as f:
            json.dump(self.conocimiento, f, ensure_ascii=False, indent=4)
            
    def buscar_recuerdos(self, contexto, limite=3):
        # Por ahora, una simple búsqueda por palabras clave o devolviendo los últimos recuerdos
        # En el futuro, podría integrarse con embeddings o una petición de evaluación al LLM
        if not self.conocimiento:
            return []
            
        # Retorna los últimos N recuerdos (LIFO) temporalmente hasta que el modelo evalue mejor
        return self.conocimiento[-limite:]
        
    def agregar_mensaje_usuario(self, mensaje):
        self.historial_conversacion.append({"role": "user", "content": mensaje})
        
    def agregar_mensaje_asistente(self, mensaje):
        self.historial_conversacion.append({"role": "assistant", "content": mensaje})
        
    def obtener_historial_completo_texto(self, max_turnos=3):
        # Utilidad para que el motorLLM pueda resumir la conversación en texto plano
        mensajes = self.obtener_historial(max_turnos)
        texto = ""
        for msg in mensajes:
            rol = "Usuario" if msg["role"] == "user" else "Aurora"
            texto += f"{rol}: {msg['content']}\n"
        return texto

    def obtener_historial(self, max_turnos=10):
        # Devuelve los últimos N mensajes para no exceder la ventana de contexto
        # Multiplicamos por 2 porque un turno = mensaje de usuario + mensaje de asistente
        limite = max_turnos * 2 
        return self.historial_conversacion[-limite:]
