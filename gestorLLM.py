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

        # 4. Cargar la última sesión de conversación (si existe)
        sesion_previa = self.memoria.cargar_ultima_conversacion()
        if sesion_previa:
            self.memoria.historial_conversacion = list(sesion_previa)
        # Exponemos la sesión cargada para que main.py la muestre en terminal
        self.sesion_anterior = sesion_previa


    def obtener_respuesta(self, mensaje_usuario):
        # ── 1. Clasificar la intención del usuario ────────────────────────────
        historial_actual = self.memoria.obtener_historial()
        intencion = self._clasificar_intencion(mensaje_usuario, historial_actual)
        print(f"[Intención detectada]: {intencion}")

        # ── 2. Búsqueda de memoria según intención ────────────────────────────
        conocimiento_previo = []
        conocimiento_crudo   = []

        if intencion in ("recuerdo_personal", "charla", "tarea"):
            # Para recordar cosas personales, siempre intentamos el recall
            if random.random() < 0.8:
                conocimiento_previo = self.memoria.buscar_recuerdos(
                    contexto=mensaje_usuario,
                    historial=historial_actual,
                    limite=4
                )
                if conocimiento_previo:
                    print("[Aurora recordando conversaciones pasadas...] (Recall Memoria)")

        if intencion in ("conocimiento_general", "tarea"):
            # Para conocimiento o tareas complejas, buscar también en textos brutos
            conocimiento_crudo = self.memoria.buscar_conocimiento(
                consulta=mensaje_usuario,
                historial=historial_actual,
                limite=2
            )
            if conocimiento_crudo:
                print("[Aurora consultando su base de conocimiento general...] (Recall Conocimiento)")

        if intencion == "charla" and not conocimiento_previo:
            # En charla sin recuerdos claros, probabilidad de no buscar conocimiento bruto
            conocimiento_crudo = []

        # ── 3. Filtrado LLM de candidatos (si hay muchos) ────────────────────
        if len(conocimiento_previo) > 3:
            conocimiento_previo = self._filtrar_candidatos_llm(
                candidatos=conocimiento_previo,
                tipo="recuerdos",
                mensaje=mensaje_usuario,
                historial=historial_actual
            )

        # ── 4. Construir contexto adicional ───────────────────────────────────
        contexto_adicional = ""
        if conocimiento_previo or conocimiento_crudo:
            contexto_adicional = "\n\nINFORMACIÓN DE CONTEXTO RELEVANTE PARA RESPONDER (Úsala si es pertinente):\n"
            if conocimiento_previo:
                contexto_adicional += "- Hechos y recuerdos de conversaciones pasadas:\n"
                contexto_adicional += "\n".join(f"  * {c}" for c in conocimiento_previo) + "\n"
            if conocimiento_crudo:
                contexto_adicional += "- Información de tu base de conocimiento general:\n"
                contexto_adicional += "\n".join(f"  * {c}" for c in conocimiento_crudo) + "\n"
                contexto_adicional += (
                    "\n[DIRECTRIZ DE RESPUESTA]: Estás consultando tu base de conocimiento externo general "
                    "para responder. Por lo tanto, debes actuar como una **EXPERTA** en el tema y dar una "
                    "explicación **MUY EXTENSA, RICA EN DETALLES Y BIEN ESTRUCTURADA**, no te limites a una respuesta breve.\n"
                )

        # ── 5. Añadir mensaje del usuario al historial a corto plazo ─────────
        self.memoria.agregar_mensaje_usuario(mensaje_usuario)

        # ── 6. Obtener historial actualizado ──────────────────────────────────
        historial = self.memoria.obtener_historial()

        # ── 7. Solicitar respuesta al motor ───────────────────────────────────
        print("Aurora está escribiendo...")
        prompt_enriquecido = self.system_prompt + contexto_adicional

        self._guardar_log_contexto(prompt_enriquecido, historial)
        respuesta = self.motor.generate_response(prompt_enriquecido, historial)

        # ── 8. Guardar respuesta en memoria a corto plazo ─────────────────────
        self.memoria.agregar_mensaje_asistente(respuesta)

        # ── 9. Proceso de pensamiento interno post-respuesta ──────────────────
        self._proceso_pensamiento_interno()

        return respuesta

    def guardar_sesion(self):
        """Guarda la conversación actual en disco. Llamar al salir del programa."""
        self.memoria.guardar_conversacion()


    # ──────────────────────────────────────────────────────────────────────────
    # CLASIFICACIÓN DE INTENCIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def _clasificar_intencion(self, mensaje, historial):
        """
        Usa el motor de pensamiento para clasificar la intención del usuario.
        Categorías posibles:
          - recuerdo_personal : El usuario pregunta por algo que Aurora debería recordar
          - conocimiento_general : Pregunta de tipo factual/enciclopédico/técnico
          - tarea : Petición de ayuda con una tarea específica
          - charla : Conversación casual sin necesidad de recuperar memoria
        Devuelve la categoría como string. Si el LLM falla, devuelve 'charla'.
        """
        historial_texto = ""
        for msg in historial[-4:]:
            rol = "Usuario" if msg["role"] == "user" else "Aurora"
            historial_texto += f"{rol}: {msg['content']}\n"

        prompt = f"""Clasifica el siguiente mensaje de usuario en UNA de estas categorías exactas:
- recuerdo_personal (el usuario pregunta algo que Aurora debería recordar de él o de conversaciones pasadas)
- conocimiento_general (pregunta factual, técnica, histórica o enciclopédica)
- tarea (pide ayuda con una tarea, problema o petición concreta)
- charla (conversación casual, saludo, comentario sin búsqueda necesaria)

Conversación reciente:
{historial_texto}
Nuevo mensaje del usuario: "{mensaje}"

Responde SOLO con una de estas palabras exactas: recuerdo_personal, conocimiento_general, tarea, charla"""

        try:
            resultado = self.motor.generate_thought(prompt, max_tokens=20).strip().lower()
            # Extraer la primera palabra válida de la respuesta
            for categoria in ["recuerdo_personal", "conocimiento_general", "tarea", "charla"]:
                if categoria in resultado:
                    return categoria
        except Exception as e:
            print(f"[Error en clasificación de intención]: {e}")

        return "charla"  # Fallback seguro


    # ──────────────────────────────────────────────────────────────────────────
    # FILTRADO LLM DE CANDIDATOS
    # ──────────────────────────────────────────────────────────────────────────

    def _filtrar_candidatos_llm(self, candidatos, tipo, mensaje, historial):
        """
        Dado un conjunto de candidatos recuperados, usa el LLM para seleccionar
        solo los que son realmente relevantes para el mensaje y contexto actual.
        Devuelve una lista filtrada (máximo 3 elementos).
        """
        if not candidatos:
            return []

        historial_texto = ""
        for msg in historial[-4:]:
            rol = "Usuario" if msg["role"] == "user" else "Aurora"
            historial_texto += f"{rol}: {msg['content']}\n"

        lista_candidatos = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidatos))

        prompt = f"""Tengo estos {tipo} recuperados de memoria:
{lista_candidatos}

Conversación actual:
{historial_texto}
Mensaje del usuario: "{mensaje}"

¿Cuáles de estos {tipo} son REALMENTE relevantes para responder al mensaje actual?
Responde SOLO con los números separados por comas (ejemplo: 1,3). Si ninguno es relevante, escribe: ninguno"""

        try:
            resultado = self.motor.generate_thought(prompt, max_tokens=30).strip()
            if "ninguno" in resultado.lower():
                return []

            import re
            numeros = [int(n.strip()) for n in re.findall(r'\d+', resultado)]
            seleccionados = []
            for n in numeros:
                if 1 <= n <= len(candidatos):
                    seleccionados.append(candidatos[n - 1])
            return seleccionados[:3] if seleccionados else candidatos[:3]
        except Exception as e:
            print(f"[Error en filtrado de candidatos]: {e}")
            return candidatos[:3]


    # ──────────────────────────────────────────────────────────────────────────
    # PROCESO DE PENSAMIENTO INTERNO (MEMORIZACIÓN)
    # ──────────────────────────────────────────────────────────────────────────

    def _proceso_pensamiento_interno(self):
        """
        Post-respuesta: decide aleatoriamente si extraer un nuevo recuerdo
        de la conversación reciente y guardarlo con metadatos enriquecidos.
        """
        if random.random() < 0.5:
            print("[Aurora reflexionando para memorizar...] (Thought Generation)")

            historial_reciente = self.memoria.obtener_historial_completo_texto(max_turnos=2)

            prompt_pensamiento = f"""Analiza el siguiente fragmento de conversación entre un Usuario y tú (Aurora).
Extrae UNA única frase con información importante sobre el Usuario o sobre ti misma (gustos, detalles, nombre, hechos, fechas) que sea digna de recordar a largo plazo.
Si no hay información relevante, escribe "NADA". Escribe SOLO el hecho a recordar, sin preámbulos ni explicaciones.

Conversación:
{historial_reciente}"""

            self._guardar_log_pensamiento(prompt_pensamiento)

            pensamiento = self.motor.generate_thought(prompt_pensamiento, max_tokens=100)
            pensamiento_limpio = pensamiento.strip()

            if "NADA" not in pensamiento_limpio.upper() and len(pensamiento_limpio) > 5:
                # Guardar con metadatos enriquecidos
                recuerdo_obj = {
                    "texto": pensamiento_limpio,
                    "fecha": datetime.date.today().isoformat(),
                    "categoria": self.memoria._detectar_categoria(pensamiento_limpio),
                    "etiquetas": self.memoria._extraer_palabras_clave(pensamiento_limpio),
                    "accesos": 0
                }
                print(f"[Nuevo recuerdo almacenado]: {pensamiento_limpio}")
                self.memoria.guardar_recuerdo(recuerdo_obj)


    # ──────────────────────────────────────────────────────────────────────────
    # LOGS
    # ──────────────────────────────────────────────────────────────────────────

    def _guardar_log_contexto(self, prompt, historial):
        directorio_logs = "logs_respuesta"
        os.makedirs(directorio_logs, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_archivo = os.path.join(directorio_logs, f"log_contexto_{timestamp}.txt")

        try:
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write("=== SYSTEM PROMPT + CONTEXTO ADICIONAL ===\n\n")
                f.write(prompt)
                f.write("\n\n=== HISTORIAL DE CONVERSACIÓN PUESTO EN CONTEXTO ===\n\n")
                for msg in historial:
                    f.write(f"Rol: {msg['role']}\n")
                    f.write(f"Contenido: {msg['content']}\n")
                    f.write("-" * 40 + "\n")

            # Mantener máximo 10 archivos
            archivos_log = sorted(
                [os.path.join(directorio_logs, f) for f in os.listdir(directorio_logs)
                 if f.startswith("log_contexto_") and f.endswith(".txt")],
                key=os.path.getmtime
            )
            while len(archivos_log) > 10:
                os.remove(archivos_log.pop(0))
        except Exception as e:
            print(f"[Error al guardar log de contexto]: {e}")

    def _guardar_log_pensamiento(self, prompt):
        directorio_logs = "logs_pensamientos"
        os.makedirs(directorio_logs, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_archivo = os.path.join(directorio_logs, f"log_pensamiento_{timestamp}.txt")

        try:
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write("=== PROMPT DE PENSAMIENTO ===\n\n")
                f.write(prompt)

            archivos_log = sorted(
                [os.path.join(directorio_logs, f) for f in os.listdir(directorio_logs)
                 if f.startswith("log_pensamiento_") and f.endswith(".txt")],
                key=os.path.getmtime
            )
            while len(archivos_log) > 10:
                os.remove(archivos_log.pop(0))
        except Exception as e:
            print(f"[Error al guardar log de pensamiento]: {e}")
