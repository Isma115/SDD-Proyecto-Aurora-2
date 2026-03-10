import random
from motorLLM import MotorLLM
from recursos import GestorRecursos

class GestorLLM:
    def __init__(self):
        print("Iniciando GestorLLM...")
        self.motor = MotorLLM()
        self.memoria = GestorRecursos()
        
        # System prompt para otorgar personalidad amigable y datos de usuario
        system_base = ""
        user_info = ""
        
        # 1. Cargar personalidad base
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_base = f.read().strip()
            print("System prompt cargado desde system_prompt.txt")
        except FileNotFoundError:
            print("Advertencia: No se encontró system_prompt.txt, usando personalidad por defecto.")
            system_base = (
                "Eres Aurora, un asistente de IA amigable, empático y servicial. "
                "Responde de forma clara, cálida y en español."
            )
            
        # 2. Cargar información crucial del usuario
        try:
            with open("user_system_prompt.txt", "r", encoding="utf-8") as f:
                user_info = f.read().strip()
            print("Información de usuario cargada desde user_system_prompt.txt")
        except FileNotFoundError:
            print("Nota: No se encontró user_system_prompt.txt")
            user_info = ""

        # 3. Concatenar ambos prompts
        self.system_prompt = system_base + "\n\nINFORMACIÓN SOBRE EL USUARIO:\n" + user_info


    def obtener_respuesta(self, mensaje_usuario):
        # 1. Proceso de Recall (Recuperación de memoria)
        # Decidimos si intentar recordar algo antes de responder
        conocimiento_previo = []
        if random.random() < 0.7: # Alta probabilidad de intentar recordar
            print("[Aurora buscando en su memoria...] (Recall)")
            conocimiento_previo = self.memoria.buscar_recuerdos(mensaje_usuario)
            
        contexto_adicional = ""
        if conocimiento_previo:
            contexto_adicional = "\n\nRecuerdos pasados que pueden ser útiles:\n" + "\n".join(conocimiento_previo)
        
        # 2. Añadimos el mensaje del usuario a la memoria a corto plazo
        self.memoria.agregar_mensaje_usuario(mensaje_usuario)
        
        # 3. Obtenemos el contexto reciente de la conversación
        historial = self.memoria.obtener_historial()
        
        # 4. Solicitamos respuesta al motor, inyectando los recuerdos en el system prompt
        print("Aurora está escribiendo...")
        prompt_enriquecido = self.system_prompt + contexto_adicional
        respuesta = self.motor.generate_response(prompt_enriquecido, historial)
        
        # 5. Guardamos la respuesta del asistente en memoria a corto plazo
        self.memoria.agregar_mensaje_asistente(respuesta)
        
        # 6. Proceso de Memorización (Pensamiento interno post-respuesta)
        self._proceso_pensamiento_interno()
        
        return respuesta

    def _proceso_pensamiento_interno(self):
        # Decide aleatoriamente si extraer y guardar un nuevo recuerdo
        if random.random() < 0.5: 
            print("[Aurora reflexionando para memorizar...] (Thought Generation)")
            
            # Obtener el texto del último par de turnos
            historial_reciente = self.memoria.obtener_historial_completo_texto(max_turnos=2)
            
            prompt_pensamiento = f"""
        Analiza el siguiente fragmento de conversación entre un Usuario y tú (Aurora).
        Extrae UNA única frase concisa con información importante sobre el Usuario (gustos, detalles, nombre) o sobre la conversación que sea digna de recordar.
        Si no hay información relevante, escribe "NADA". Escribe SOLO el hecho a recordar, sin preámbulos.
        
        Conversación:
        {historial_reciente}
        """
            
            pensamiento = self.motor.generate_thought(prompt_pensamiento, max_tokens=100)
            pensamiento_limpio = pensamiento.strip()
            
            if "NADA" not in pensamiento_limpio.upper() and len(pensamiento_limpio) > 5:
                print(f"[Nuevo recuerdo almacenado]: {pensamiento_limpio}")
                self.memoria.guardar_recuerdo(pensamiento_limpio)
