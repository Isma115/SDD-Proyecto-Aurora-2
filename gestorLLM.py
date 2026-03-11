import random
import os
import datetime
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
        # 1. Proceso de Recall (Recuperación de memoria y conocimiento en bruto)
        conocimiento_previo = []
        conocimiento_crudo = []
        
        # Decidimos si intentar recordar algo personal o de conversaciones pasadas
        if random.random() < 0.7: # Alta probabilidad de intentar recordar
            conocimiento_previo = self.memoria.buscar_recuerdos(mensaje_usuario)
            if conocimiento_previo:
                print("[Aurora recordando conversaciones pasadas...] (Recall Memoria)")
            
        # Siempre buscamos en los textos de conocimiento en bruto si la consulta lo requiere
        conocimiento_crudo = self.memoria.buscar_conocimiento(mensaje_usuario)
        if conocimiento_crudo:
            print("[Aurora consultando su base de conocimiento general...] (Recall Conocimiento)")
            
        contexto_adicional = ""
        if conocimiento_previo or conocimiento_crudo:
            contexto_adicional = "\n\nINFORMACIÓN DE CONTEXTO RELEVANTE PARA RESPONDER (Úsala si es pertinente):\n"
            if conocimiento_previo:
                contexto_adicional += "- Hechos y recuerdos pasados de conversaciones:\n" + "\n".join(f"  * {c}" for c in conocimiento_previo) + "\n"
            if conocimiento_crudo:
                contexto_adicional += "- Información externa de conocimiento general relacionada:\n" + "\n".join(f"  * {c}" for c in conocimiento_crudo) + "\n"
                contexto_adicional += "\n[DIRECTRIZ DE RESPUESTA]: Estás consultando tu base de conocimiento externo general para responder. Por lo tanto, debes actuar como una **EXPERTA** en el tema y dar una explicación **MUY EXTENSA, RICA EN DETALLES Y BIEN ESTRUCTURADA**, no te limites a una respuesta breve.\n"
        
        # 2. Añadimos el mensaje del usuario a la memoria a corto plazo
        self.memoria.agregar_mensaje_usuario(mensaje_usuario)
        
        # 3. Obtenemos el contexto reciente de la conversación
        historial = self.memoria.obtener_historial()
        
        # 4. Solicitamos respuesta al motor, inyectando los recuerdos en el system prompt
        print("Aurora está escribiendo...")
        prompt_enriquecido = self.system_prompt + contexto_adicional
        
        # Guardar log de contexto antes de generar respuesta
        self._guardar_log_contexto(prompt_enriquecido, historial)
        
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

    def _guardar_log_contexto(self, prompt, historial):
        directorio_logs = "logs"
        if not os.path.exists(directorio_logs):
            os.makedirs(directorio_logs, exist_ok=True)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"log_contexto_{timestamp}.txt"
        ruta_archivo = os.path.join(directorio_logs, nombre_archivo)
        
        try:
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write("=== SYSTEM PROMPT + CONTEXTO ADICIONAL ===\n\n")
                f.write(prompt)
                f.write("\n\n=== HISTORIAL DE CONVERSACIÓN PUESTO EN CONTEXTO ===\n\n")
                for msg in historial:
                    f.write(f"Rol: {msg['role']}\n")
                    f.write(f"Contenido: {msg['content']}\n")
                    f.write("-" * 40 + "\n")
                    
            # Mantener un máximo de 10 archivos de log
            archivos_log = [os.path.join(directorio_logs, f) for f in os.listdir(directorio_logs) if f.startswith("log_contexto_") and f.endswith(".txt")]
            archivos_log.sort(key=os.path.getmtime) # Ordenar del más antiguo al más reciente
            
            # Borrar los más antiguos si superan los 10
            while len(archivos_log) > 10:
                archivo_a_borrar = archivos_log.pop(0)
                os.remove(archivo_a_borrar)
                
        except Exception as e:
            print(f"Error al guardar log de contexto: {e}")

