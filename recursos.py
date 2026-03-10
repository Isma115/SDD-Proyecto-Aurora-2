class GestorRecursos:
    def __init__(self):
        self.historial_conversacion = []
        
    def agregar_mensaje_usuario(self, mensaje):
        self.historial_conversacion.append({"role": "user", "content": mensaje})
        
    def agregar_mensaje_asistente(self, mensaje):
        self.historial_conversacion.append({"role": "assistant", "content": mensaje})
        
    def obtener_historial(self, max_turnos=10):
        # Devuelve los últimos N mensajes para no exceder la ventana de contexto
        # Multiplicamos por 2 porque un turno = mensaje de usuario + mensaje de asistente
        limite = max_turnos * 2 
        return self.historial_conversacion[-limite:]
