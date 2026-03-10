from motorLLM import MotorLLM
from recursos import GestorRecursos

class GestorLLM:
    def __init__(self):
        print("Iniciando GestorLLM...")
        self.motor = MotorLLM()
        self.memoria = GestorRecursos()
        
        # System prompt para otorgar personalidad amigable
        self.system_prompt = (
            "Eres Aurora, un asistente de IA amigable, empático y servicial. "
            "Tu objetivo es conversar con el usuario de manera natural, como si fueras humano. "
            "Responde de forma clara, cálida y en español."
        )

    def obtener_respuesta(self, mensaje_usuario):
        # 1. Añadimos el mensaje del usuario a la memoria
        self.memoria.agregar_mensaje_usuario(mensaje_usuario)
        
        # 2. Obtenemos el contexto reciente de la conversación
        historial = self.memoria.obtener_historial()
        
        # 3. Solicitamos respuesta al motor
        print("Aurora está escribiendo...")
        respuesta = self.motor.generate_response(self.system_prompt, historial)
        
        # 4. Guardamos la respuesta del asistente en memoria
        self.memoria.agregar_mensaje_asistente(respuesta)
        
        return respuesta
