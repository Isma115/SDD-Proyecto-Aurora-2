import copy
import json
import os

from huggingface_hub import hf_hub_download
import llama_cpp
from llama_cpp import Llama


DEFAULT_CONFIG = {
    "model": {
        "repo_id": "bartowski/gemma-2-2b-it-GGUF",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf"
    },
    "initialization": {
        "n_ctx": 4096,
        "n_threads": None,
        "n_gpu_layers": -1
    },
    "generation": {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "min_p": 0.05,
        "typical_p": 1.0,
        "max_tokens": 512,
        "seed": None,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "repeat_penalty": 1.1,
        "tfs_z": 1.0,
        "mirostat_mode": 0,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1
    },
    "thought": {
        "temperature": 0.3,
        "top_p": 0.9,
        "top_k": 40,
        "min_p": 0.05,
        "typical_p": 1.0,
        "max_tokens": 150,
        "seed": None,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "repeat_penalty": 1.1,
        "tfs_z": 1.0,
        "mirostat_mode": 0,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1
    },
    "kv_cache": {
        "type_k": None,
        "type_v": None
    }
}


def crear_configuracion_por_defecto():
    return copy.deepcopy(DEFAULT_CONFIG)


class MotorLLM:
    def __init__(self, config_path="config.json", status_callback=None):
        self.config_path = config_path
        self.status_callback = status_callback
        self.config = self._load_or_create_config()

        self.repo_id = self.config["model"]["repo_id"]
        self.filename = self.config["model"]["filename"]
        self.model_path = os.path.join("models", self.filename)
        self.llm = None
        self._download_and_load_model()

    def _emit_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

    def _load_or_create_config(self):
        default_config = crear_configuracion_por_defecto()

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return self._normalizar_config(config)
            except Exception as e:
                self._emit_status(f"Error cargando config.json, usando valores por defecto: {e}")
                return default_config

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            self._emit_status("Archivo config.json creado con valores por defecto.")
        except Exception as e:
            self._emit_status(f"Error creando config.json: {e}")
        return default_config

    def _normalizar_config(self, config):
        normalizada = crear_configuracion_por_defecto()
        if not isinstance(config, dict):
            return normalizada

        for seccion, valores in normalizada.items():
            origen = config.get(seccion)
            if isinstance(valores, dict) and isinstance(origen, dict):
                valores.update(origen)
        return normalizada

    def guardar_configuracion(self, config=None):
        if config is not None:
            self.config = self._normalizar_config(config)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def _actualizar_ruta_modelo(self):
        self.repo_id = self.config["model"]["repo_id"]
        self.filename = self.config["model"]["filename"]
        self.model_path = os.path.join("models", self.filename)

    def _requiere_recarga_modelo(self, config_anterior, config_nueva):
        return any(
            config_anterior.get(clave) != config_nueva.get(clave)
            for clave in ("model", "initialization", "kv_cache")
        )

    def recargar_modelo(self):
        self._actualizar_ruta_modelo()
        if self.llm is not None:
            try:
                del self.llm
            except Exception:
                pass
            self.llm = None
        self._download_and_load_model()

    def actualizar_configuracion(self, nueva_config, recargar_modelo=False):
        config_anterior = copy.deepcopy(self.config)
        self.config = self._normalizar_config(nueva_config)
        self.guardar_configuracion()
        requiere_recarga = recargar_modelo or self._requiere_recarga_modelo(config_anterior, self.config)
        if requiere_recarga:
            self.recargar_modelo()
        else:
            self._actualizar_ruta_modelo()
        return requiere_recarga

    def _resolver_tipo_kv(self, valor):
        if valor is None:
            return None

        if isinstance(valor, int):
            return valor

        if isinstance(valor, str):
            nombre = valor.strip().upper()
            if not nombre:
                return None
            if not nombre.startswith("GGML_TYPE_"):
                nombre = f"GGML_TYPE_{nombre}"
            if hasattr(llama_cpp, nombre):
                return int(getattr(llama_cpp, nombre))

            self._emit_status(
                f"Tipo de KV cache no reconocido: {valor}. Se usará el valor por defecto del backend."
            )
            return None

        self._emit_status(
            f"Tipo de KV cache inválido ({type(valor).__name__}). Se usará el valor por defecto del backend."
        )
        return None

    def _download_and_load_model(self):
        os.makedirs("models", exist_ok=True)
        if not os.path.exists(self.model_path):
            self._emit_status(f"Descargando el modelo {self.filename} desde {self.repo_id}...")
            self._emit_status("Esto puede tardar unos minutos dependiendo de la conexión a internet.")
            hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                local_dir="models",
                local_dir_use_symlinks=False
            )
            self._emit_status("Descarga completada.")
        else:
            self._emit_status(f"Modelo {self.filename} encontrado localmente en models/")

        self._emit_status("Cargando modelo en memoria...")
        tipo_k = self._resolver_tipo_kv(self.config.get("kv_cache", {}).get("type_k"))
        tipo_v = self._resolver_tipo_kv(self.config.get("kv_cache", {}).get("type_v"))
        if tipo_k is not None or tipo_v is not None:
            self._emit_status(
                f"Cuantización de KV cache activada (type_k={self.config.get('kv_cache', {}).get('type_k')}, "
                f"type_v={self.config.get('kv_cache', {}).get('type_v')})"
            )
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.config["initialization"]["n_ctx"],
            n_threads=self.config["initialization"]["n_threads"],
            n_gpu_layers=self.config["initialization"]["n_gpu_layers"],
            type_k=tipo_k,
            type_v=tipo_v,
            verbose=False
        )
        self._emit_status("Modelo cargado correctamente.")

    def _obtener_parametros_generacion(self, seccion, max_tokens, max_tokens_por_defecto):
        parametros = self.config.get(seccion, {})
        max_t = parametros.get("max_tokens", max_tokens_por_defecto) if max_tokens == max_tokens_por_defecto else max_tokens
        return {
            "max_tokens": max_t,
            "temperature": parametros.get("temperature", DEFAULT_CONFIG[seccion]["temperature"]),
            "top_p": parametros.get("top_p", DEFAULT_CONFIG[seccion]["top_p"]),
            "top_k": parametros.get("top_k", DEFAULT_CONFIG[seccion]["top_k"]),
            "min_p": parametros.get("min_p", DEFAULT_CONFIG[seccion]["min_p"]),
            "typical_p": parametros.get("typical_p", DEFAULT_CONFIG[seccion]["typical_p"]),
            "seed": parametros.get("seed", DEFAULT_CONFIG[seccion]["seed"]),
            "presence_penalty": parametros.get("presence_penalty", DEFAULT_CONFIG[seccion]["presence_penalty"]),
            "frequency_penalty": parametros.get("frequency_penalty", DEFAULT_CONFIG[seccion]["frequency_penalty"]),
            "repeat_penalty": parametros.get("repeat_penalty", DEFAULT_CONFIG[seccion]["repeat_penalty"]),
            "tfs_z": parametros.get("tfs_z", DEFAULT_CONFIG[seccion]["tfs_z"]),
            "mirostat_mode": parametros.get("mirostat_mode", DEFAULT_CONFIG[seccion]["mirostat_mode"]),
            "mirostat_tau": parametros.get("mirostat_tau", DEFAULT_CONFIG[seccion]["mirostat_tau"]),
            "mirostat_eta": parametros.get("mirostat_eta", DEFAULT_CONFIG[seccion]["mirostat_eta"]),
        }

    def build_response_messages(self, system_prompt, history):
        """
        Construye exactamente la lista de mensajes que se enviará al backend
        de chat_completion. Gemma 2 no soporta role=system de forma nativa,
        así que el prompt del sistema se inyecta en el primer mensaje user.
        """
        messages = []
        for i, msg in enumerate(history):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if i == 0 and role == "user":
                messages.append({"role": "user", "content": f"{system_prompt}\n\n{content}"})
            elif i == 0:
                messages.append({"role": "user", "content": system_prompt})
                messages.append({"role": role, "content": content})
            else:
                messages.append({"role": role, "content": content})
        return messages

    def generate_response(self, system_prompt, history, max_tokens=512):
        messages = self.build_response_messages(system_prompt, history)
        response = self.llm.create_chat_completion(
            messages=messages,
            **self._obtener_parametros_generacion("generation", max_tokens, 512)
        )
        return response["choices"][0]["message"]["content"]

    def generate_thought(self, prompt, max_tokens=150):
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = self.llm.create_chat_completion(
            messages=messages,
            **self._obtener_parametros_generacion("thought", max_tokens, 150)
        )
        return response["choices"][0]["message"]["content"]


import random
import os
import datetime
import threading
from collections import OrderedDict
from recursos import GestorRecursos

class GestorLLM:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self._bloqueo = threading.RLock()
        self.historial_contexto_modelo = []
        self._emit_status("Iniciando GestorLLM...")
        self.motor = MotorLLM(status_callback=self._emit_status)
        self.memoria = GestorRecursos(status_callback=self._emit_status)

        system_base = ""
        user_info = ""

        # 1. Cargar personalidad base
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_base = f.read().strip()
            self._emit_status("System prompt cargado desde system_prompt.txt")
        except FileNotFoundError:
            self._emit_status("Advertencia: No se encontró system_prompt.txt, usando personalidad por defecto.")
            system_base = (
                "Eres Aurora, un asistente de IA amigable, empático y servicial. "
                "Responde de forma clara, cálida y en español."
            )

        # 2. Cargar información crucial del usuario
        try:
            with open("user_system_prompt.txt", "r", encoding="utf-8") as f:
                user_info = f.read().strip()
            self._emit_status("Información de usuario cargada desde user_system_prompt.txt")
        except FileNotFoundError:
            self._emit_status("Nota: No se encontró user_system_prompt.txt")
            user_info = ""

        # 3. Concatenar ambos prompts
        self.system_prompt = system_base + "\n\nINFORMACIÓN SOBRE EL USUARIO:\n" + user_info

        # 4. Cargar la última sesión de conversación (si existe)
        sesion_previa = self.memoria.cargar_ultima_conversacion()
        if sesion_previa:
            self.memoria.historial_conversacion = list(sesion_previa)
        # Exponemos la sesión cargada para que main.py la muestre en terminal
        self.sesion_anterior = sesion_previa

    def _emit_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            if isinstance(message, dict):
                tipo = message.get("tipo")
                if tipo == "contexto_modelo":
                    print(message.get("resumen", "[Contexto del modelo preparado]"))
                else:
                    print(message.get("resumen", message))
            else:
                print(message)

    def _clonar_mensajes(self, mensajes):
        return [
            {
                "role": msg.get("role", ""),
                "content": msg.get("content", ""),
            }
            for msg in mensajes
        ]

    def _registrar_contexto_modelo(self, prompt_enriquecido, historial, intencion=None):
        mensajes_modelo = self.motor.build_response_messages(prompt_enriquecido, historial)
        snapshot = {
            "tipo": "contexto_modelo",
            "indice": len(self.historial_contexto_modelo) + 1,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "intencion": intencion or "desconocida",
            "mensajes_modelo": self._clonar_mensajes(mensajes_modelo),
        }
        snapshot["resumen"] = (
            f"Contexto completo preparado para el turno {snapshot['indice']} "
            f"({len(snapshot['mensajes_modelo'])} mensaje(s) enviados al modelo)."
        )
        self.historial_contexto_modelo.append(snapshot)
        self._emit_status(snapshot)
        return snapshot

    def obtener_historial_contexto_modelo(self):
        with self._bloqueo:
            return [
                {
                    "tipo": snap.get("tipo", "contexto_modelo"),
                    "indice": snap.get("indice", 0),
                    "timestamp": snap.get("timestamp", ""),
                    "intencion": snap.get("intencion", "desconocida"),
                    "resumen": snap.get("resumen", ""),
                    "mensajes_modelo": self._clonar_mensajes(snap.get("mensajes_modelo", [])),
                }
                for snap in self.historial_contexto_modelo
            ]

    def _crear_evento_fuentes_conocimiento(self, fragmentos):
        if not fragmentos:
            return None

        # Evita repetir exactamente el mismo origen+rango.
        fuentes_unicas = OrderedDict()
        for frag in fragmentos:
            origen = frag.get("origen", "desconocido.txt")
            inicio = frag.get("linea_inicio", 0)
            fin = frag.get("linea_fin", inicio)
            clave = (origen, inicio, fin)
            if clave not in fuentes_unicas:
                texto_contexto = str(
                    frag.get("texto_contexto", frag.get("texto", ""))
                ).strip()
                fuentes_unicas[clave] = {
                    "origen": origen,
                    "linea_inicio": inicio,
                    "linea_fin": fin,
                    "linea_inicio_contexto": frag.get("linea_inicio_contexto", inicio),
                    "linea_fin_contexto": frag.get("linea_fin_contexto", fin),
                    "texto": texto_contexto,
                }

        if not fuentes_unicas:
            return None

        resumen = "Información recogida de " + ", ".join(
            f"[{fuente['origen']} (líneas {fuente['linea_inicio']}-{fuente['linea_fin']})]"
            for fuente in fuentes_unicas.values()
        )
        return {
            "tipo": "fuentes_conocimiento",
            "resumen": resumen,
            "fuentes": list(fuentes_unicas.values()),
        }


    def obtener_respuesta(self, mensaje_usuario):
        with self._bloqueo:
            # ── 1. Clasificar la intención del usuario ────────────────────────
            historial_actual = self.memoria.obtener_historial()
            intencion = self._clasificar_intencion(mensaje_usuario, historial_actual)
            self._emit_status(f"[Intención detectada]: {intencion}")

            # ── 2. Búsqueda de memoria según intención ────────────────────────
            conocimiento_previo = []
            conocimiento_crudo = []
            conocimiento_crudo_texto = []

            if intencion in ("recuerdo_personal", "charla", "tarea"):
                if random.random() < 0.8:
                    conocimiento_previo = self.memoria.buscar_recuerdos(
                        contexto=mensaje_usuario,
                        historial=historial_actual,
                        limite=4
                    )
                    if conocimiento_previo:
                        self._emit_status("[Aurora recordando conversaciones pasadas...] (Recall Memoria)")

            if intencion in ("conocimiento_general", "tarea"):
                conocimiento_crudo = self.memoria.buscar_conocimiento(
                    consulta=mensaje_usuario,
                    historial=historial_actual,
                    limite=4
                )
                if conocimiento_crudo:
                    self._emit_status("[Aurora consultando su base de conocimiento general...] (Recall Conocimiento)")
                    evento_fuentes = self._crear_evento_fuentes_conocimiento(conocimiento_crudo)
                    if evento_fuentes:
                        self._emit_status(evento_fuentes)
                    conocimiento_crudo_texto = [
                        (
                            f"{frag.get('origen', 'desconocido.txt')} "
                            f"(contexto líneas {frag.get('linea_inicio_contexto', frag.get('linea_inicio', 0))}-"
                            f"{frag.get('linea_fin_contexto', frag.get('linea_fin', 0))}): "
                            f"{frag.get('texto_contexto', frag.get('texto', ''))}"
                        )
                        for frag in conocimiento_crudo
                    ]

            if intencion == "charla" and not conocimiento_previo:
                conocimiento_crudo = []

            # ── 3. Filtrado LLM de candidatos (si hay muchos) ────────────────
            if len(conocimiento_previo) > 3:
                conocimiento_previo = self._filtrar_candidatos_llm(
                    candidatos=conocimiento_previo,
                    tipo="recuerdos",
                    mensaje=mensaje_usuario,
                    historial=historial_actual
                )

            # ── 4. Construir contexto adicional ───────────────────────────────
            contexto_adicional = ""
            if conocimiento_previo or conocimiento_crudo_texto:
                contexto_adicional = "\n\nINFORMACIÓN DE CONTEXTO RELEVANTE PARA RESPONDER (Úsala si es pertinente):\n"
                if conocimiento_previo:
                    contexto_adicional += "- Hechos y recuerdos de conversaciones pasadas:\n"
                    contexto_adicional += "\n".join(f"  * {c}" for c in conocimiento_previo) + "\n"
                if conocimiento_crudo_texto:
                    contexto_adicional += "- Información de tu base de conocimiento general:\n"
                    contexto_adicional += "\n".join(f"  * {c}" for c in conocimiento_crudo_texto) + "\n"
                    contexto_adicional += (
                        "\n[DIRECTRIZ DE RESPUESTA]: Estás consultando tu base de conocimiento externo general "
                        "para responder. Por lo tanto, debes actuar como una **EXPERTA** en el tema y dar una "
                        "explicación **MUY EXTENSA, RICA EN DETALLES Y BIEN ESTRUCTURADA**, no te limites a una respuesta breve.\n"
                    )

            # ── 5. Añadir mensaje del usuario al historial a corto plazo ─────
            self.memoria.agregar_mensaje_usuario(mensaje_usuario)

            # ── 6. Obtener historial actualizado ──────────────────────────────
            historial = self.memoria.obtener_historial()

            # ── 7. Solicitar respuesta al motor ───────────────────────────────
            self._emit_status("Aurora está escribiendo...")
            prompt_enriquecido = self.system_prompt + contexto_adicional
            snapshot_contexto = self._registrar_contexto_modelo(
                prompt_enriquecido,
                historial,
                intencion=intencion,
            )

            self._guardar_log_contexto(
                prompt_enriquecido,
                historial,
                snapshot_contexto.get("mensajes_modelo", []),
            )
            respuesta = self.motor.generate_response(prompt_enriquecido, historial)

            # ── 8. Guardar respuesta en memoria a corto plazo ─────────────────
            self.memoria.agregar_mensaje_asistente(respuesta)

            # ── 9. Proceso de pensamiento interno post-respuesta ──────────────
            self._proceso_pensamiento_interno()

            return respuesta

    def guardar_sesion(self):
        """Guarda la conversación actual en disco. Llamar al salir del programa."""
        with self._bloqueo:
            self.memoria.guardar_conversacion()

    def reiniciar_conversacion_actual(self):
        """
        Reinicia el historial de conversación en memoria para empezar un chat nuevo
        manteniendo la misma configuración/base de system prompt.
        """
        with self._bloqueo:
            self.memoria.reiniciar_conversacion()
            self.sesion_anterior = []
            self.historial_contexto_modelo = []


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
            self._emit_status(f"[Error en clasificación de intención]: {e}")

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
            self._emit_status(f"[Error en filtrado de candidatos]: {e}")
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
            self._emit_status("[Aurora reflexionando para memorizar...] (Thought Generation)")

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
                self._emit_status(f"[Nuevo recuerdo almacenado]: {pensamiento_limpio}")
                self.memoria.guardar_recuerdo(recuerdo_obj)


    # ──────────────────────────────────────────────────────────────────────────
    # LOGS
    # ──────────────────────────────────────────────────────────────────────────

    def _guardar_log_contexto(self, prompt, historial, mensajes_modelo=None):
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
                if mensajes_modelo:
                    f.write("\n=== MENSAJES REALES ENVIADOS AL MODELO ===\n\n")
                    for indice, msg in enumerate(mensajes_modelo, start=1):
                        f.write(f"Mensaje {indice}\n")
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
            self._emit_status(f"[Error al guardar log de contexto]: {e}")

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
            self._emit_status(f"[Error al guardar log de pensamiento]: {e}")
