import json
import os
import datetime
from typing import List, Dict, Optional, Any

class GestorRecursos:
    def __init__(self):
        self.historial_conversacion: List[Dict[str, str]] = []
        self.archivo_memoria: str = "Recursos/memoria.json"
        self.conocimiento: Optional[List[Dict[str, Any]]] = None
        self.carpeta_textos_conocimiento: str = "Recursos/conocimiento"
        self.textos_conocimiento: List[Dict[str, str]] = self._cargar_textos_conocimiento()

    # ─────────────────────────────────────────────────────────────────────────
    # MEMORIA A LARGO PLAZO (recuerdos enriquecidos)
    # ─────────────────────────────────────────────────────────────────────────

    def _cargar_memoria(self):
        """Carga memoria.json (lista de strings) y construye dicts enriquecidos en memoria."""
        if not os.path.exists(self.archivo_memoria):
            return []
        try:
            with open(self.archivo_memoria, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, list):
                return []

            hoy = datetime.date.today().isoformat()
            enriquecidos = []
            for entrada in datos:
                # Soportar tanto strings (formato guardado) como dicts (por si acaso)
                if isinstance(entrada, str):
                    texto = entrada.strip()
                elif isinstance(entrada, dict) and "texto" in entrada:
                    texto = entrada["texto"].strip()
                else:
                    continue
                if not texto:
                    continue
                enriquecidos.append({
                    "texto": texto,
                    "fecha": hoy,
                    "categoria": self._detectar_categoria(texto),
                    "etiquetas": self._extraer_palabras_clave(texto),
                    "accesos": 0
                })

            # Eliminar duplicados por texto normalizado
            vistos = set()
            limpios = []
            for r in enriquecidos:
                norm = self._normalizar_texto(r["texto"])
                if norm not in vistos:
                    vistos.add(norm)
                    limpios.append(r)

            return limpios
        except (json.JSONDecodeError, Exception):
            return []

    def _persistir_memoria(self, datos):
        """Guarda solo los textos como lista de strings en memoria.json."""
        try:
            strings = [r["texto"] if isinstance(r, dict) else str(r) for r in datos]
            with open(self.archivo_memoria, "w", encoding="utf-8") as f:
                json.dump(strings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Error guardando memoria]: {e}")

    def _asegurar_memoria_cargada(self):
        if self.conocimiento is None:
            self.conocimiento = self._cargar_memoria()

    # ─────────────────────────────────────────────────────────────────────────
    # UTILIDADES DE TEXTO
    # ─────────────────────────────────────────────────────────────────────────

    def _normalizar_texto(self, texto):
        if not texto:
            return ""
        t = str(texto).lower().strip()
        if t.endswith('.'):
            t = t[:-1].strip()
        return t

    STOPWORDS = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o",
        "pero", "si", "no", "en", "de", "a", "por", "para", "con", "sin",
        "es", "son", "del", "al", "que", "como", "sobre", "su", "me", "te",
        "se", "ya", "yo", "tu", "mi", "le", "lo", "más", "muy", "hay",
        "ser", "estar", "tiene", "tengo", "ha", "he", "sido", "cuando",
        "también", "donde", "porque", "qué", "cómo", "quién", "cuál"
    }

    def _extraer_palabras_clave(self, texto):
        """Extrae palabras relevantes eliminando stopwords y puntuación."""
        import re
        palabras = re.sub(r"[¿?¡!,\.\"'():\-]", " ", self._normalizar_texto(str(texto))).split()
        return [p for p in palabras if p not in self.STOPWORDS and len(p) > 2]

    def _detectar_categoria(self, texto):
        """Heurística simple para clasificar un recuerdo en una categoría."""
        texto_lower = str(texto).lower()
        indicadores_usuario = [
            "el usuario", "ismael", "le gusta", "trabaja", "su trabajo",
            "cumpleaños", "vive", "tiene", "quiere", "prefiere", "llama"
        ]
        indicadores_aurora = [
            "aurora", "me gusta", "soy", "recuerdo", "siento", "pienso", "creo que"
        ]
        for ind in indicadores_usuario:
            if ind in texto_lower:
                return "usuario"
        for ind in indicadores_aurora:
            if ind in texto_lower:
                return "aurora"
        return "general"

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING DE RELEVANCIA
    # ─────────────────────────────────────────────────────────────────────────

    def _score_recuerdo(self, recuerdo_obj, palabras_contexto_set, historial_texto=""):
        """
        Calcula la puntuación de relevancia de un recuerdo dado un contexto.
        Combina:
          - Coincidencia de palabras clave (TF-IDF simplificado)
          - Bonus por coincidencia en historial de conversación reciente
          - Penalización suave por antigüedad (recuerdos viejos puntúan menos)
          - Bonus por número de accesos previos (recuerdos útiles en el pasado)
        """
        texto = recuerdo_obj.get("texto", "")
        palabras_recuerdo = set(recuerdo_obj.get("etiquetas", self._extraer_palabras_clave(texto)))
        
        # 1. Coincidencia básica de palabras clave
        interseccion = palabras_contexto_set.intersection(palabras_recuerdo)
        score = len(interseccion)
        
        # Bonus proporcional: recuerdos más cortos que coinciden muchas palabras son más relevantes
        if len(palabras_recuerdo) > 0:
            score += len(interseccion) / len(palabras_recuerdo)

        # 2. Bonus si el recuerdo también aparece en el historial de conversación reciente
        if historial_texto and texto:
            palabras_historial = set(self._extraer_palabras_clave(historial_texto))
            coincidencias_historial = palabras_recuerdo.intersection(palabras_historial)
            score += len(coincidencias_historial) * 0.5

        # 3. Penalización por antigüedad suave (máx -1 punto por recuerdo de hace 1 año)
        try:
            fecha_str = recuerdo_obj.get("fecha", "")
            if fecha_str:
                fecha_rec = datetime.date.fromisoformat(fecha_str)
                dias_antiguedad = (datetime.date.today() - fecha_rec).days
                score -= min(dias_antiguedad / 365.0, 1.0)
        except Exception:
            pass

        # 4. Bonus por accesos previos (útilidad histórica)
        accesos = recuerdo_obj.get("accesos", 0)
        score += min(accesos * 0.1, 0.5)  # Máximo +0.5

        return score

    def _score_fragmento_conocimiento(self, fragmento, palabras_consulta_set, historial_texto=""):
        """Scoring para fragmentos de conocimiento en bruto."""
        palabras_fragmento = set(self._extraer_palabras_clave(fragmento["texto"]))
        interseccion = palabras_consulta_set.intersection(palabras_fragmento)
        score = len(interseccion)
        
        # Bonus por densidad de coincidencias
        if len(palabras_fragmento) > 0:
            score += (len(interseccion) / len(palabras_fragmento)) * 2

        # Bonus si el historial de conversación también toca el tema
        if historial_texto:
            palabras_historial = set(self._extraer_palabras_clave(historial_texto))
            coincidencias_historial = palabras_fragmento.intersection(palabras_historial)
            score += len(coincidencias_historial) * 0.3

        return score

    # ─────────────────────────────────────────────────────────────────────────
    # API PÚBLICA: BÚSQUEDA
    # ─────────────────────────────────────────────────────────────────────────

    def guardar_recuerdo(self, recuerdo):
        """
        Guarda un recuerdo. Acepta:
          - str: se convierte al nuevo formato enriquecido
          - dict: se guarda directamente (con campos por defecto si faltan)
        """
        self._asegurar_memoria_cargada()

        if isinstance(recuerdo, str):
            recuerdo_obj = {
                "texto": recuerdo.strip(),
                "fecha": datetime.date.today().isoformat(),
                "categoria": self._detectar_categoria(recuerdo),
                "etiquetas": self._extraer_palabras_clave(recuerdo),
                "accesos": 0
            }
        elif isinstance(recuerdo, dict):
            recuerdo_obj = recuerdo
            recuerdo_obj.setdefault("fecha", datetime.date.today().isoformat())
            recuerdo_obj.setdefault("categoria", self._detectar_categoria(recuerdo_obj.get("texto", "")))
            recuerdo_obj.setdefault("etiquetas", self._extraer_palabras_clave(recuerdo_obj.get("texto", "")))
            recuerdo_obj.setdefault("accesos", 0)
        else:
            return

        nuevo_norm = self._normalizar_texto(recuerdo_obj["texto"])
        # Anti-duplicados
        for r in self.conocimiento:
            if self._normalizar_texto(r.get("texto", "")) == nuevo_norm:
                return

        self.conocimiento.append(recuerdo_obj)
        self._persistir_memoria(self.conocimiento)

    def buscar_recuerdos(self, contexto, historial=None, limite=4):
        """
        Busca recuerdos relevantes para el contexto e historial dados.
        Devuelve los `limite` recuerdos más relevantes usando scoring contextual.
        Si ninguno supera un umbral mínimo, devuelve los más recientes como fallback.
        """
        self._asegurar_memoria_cargada()
        if not self.conocimiento:
            return []

        # Construir el texto de historial para el scoring
        historial_texto = ""
        if historial:
            for msg in historial[-6:]:  # Últimos 3 turnos
                rol = "Usuario" if msg["role"] == "user" else "Aurora"
                historial_texto += f"{rol}: {msg['content']}\n"

        # Combinar contexto + historial para la búsqueda
        texto_busqueda = contexto + " " + historial_texto
        palabras_contexto = set(self._extraer_palabras_clave(texto_busqueda))

        if not palabras_contexto:
            # Sin palabras clave, devolver los más recientes
            return [r["texto"] for r in self.conocimiento[-limite:]]

        # Puntuar cada recuerdo
        puntuados = []
        for recuerdo in self.conocimiento:
            score = self._score_recuerdo(recuerdo, palabras_contexto, historial_texto)
            if score > 0:
                puntuados.append((score, recuerdo))

        puntuados.sort(key=lambda x: x[0], reverse=True)

        if puntuados:
            # Incrementar contador de accesos para los recuerdos recuperados
            seleccionados = puntuados[:limite]
            for _, rec in seleccionados:
                rec["accesos"] = rec.get("accesos", 0) + 1
            self._persistir_memoria(self.conocimiento)
            return [rec["texto"] for _, rec in seleccionados]
        else:
            # Fallback: últimos N recuerdos
            return [r["texto"] for r in self.conocimiento[-limite:]]

    def buscar_conocimiento(self, consulta, historial=None, limite=2):
        """
        Busca fragmentos relevantes de conocimiento en bruto.
        Usa scoring mejorado con bonus por historial de conversación.
        """
        if not self.textos_conocimiento:
            return []

        historial_texto = ""
        if historial:
            for msg in historial[-6:]:
                rol = "Usuario" if msg["role"] == "user" else "Aurora"
                historial_texto += f"{rol}: {msg['content']}\n"

        texto_busqueda = consulta + " " + historial_texto
        palabras_consulta = set(self._extraer_palabras_clave(texto_busqueda))
        if not palabras_consulta:
            return []

        puntuados = []
        for fragmento in self.textos_conocimiento:
            score = self._score_fragmento_conocimiento(fragmento, palabras_consulta, historial_texto)
            if score > 0:
                puntuados.append((score, fragmento))

        puntuados.sort(key=lambda x: x[0], reverse=True)
        return [f"{res[1]['origen']}: {res[1]['texto']}" for res in puntuados[:limite]]

    def obtener_todos_recuerdos_texto(self):
        """Devuelve todos los recuerdos como lista de strings (para filtrado LLM)."""
        self._asegurar_memoria_cargada()
        return [r["texto"] for r in self.conocimiento]

    # ─────────────────────────────────────────────────────────────────────────
    # CARGA DE CONOCIMIENTO EN BRUTO
    # ─────────────────────────────────────────────────────────────────────────

    def _cargar_textos_conocimiento(self):
        """Carga y fragmenta textos en bruto de la carpeta especificada."""
        fragmentos = []
        if not os.path.exists(self.carpeta_textos_conocimiento):
            os.makedirs(self.carpeta_textos_conocimiento, exist_ok=True)
            return fragmentos

        for filename in os.listdir(self.carpeta_textos_conocimiento):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.carpeta_textos_conocimiento, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        texto_completo = f.read()
                    parrafos = texto_completo.split("\n\n")
                    for parrafo in parrafos:
                        if len(parrafo.strip()) > 30:
                            fragmentos.append({
                                "origen": filename,
                                "texto": parrafo.strip()
                            })
                except Exception as e:
                    print(f"[Error cargando archivo {filename}]: {e}")
        return fragmentos

    # ─────────────────────────────────────────────────────────────────────────
    # HISTORIAL DE CONVERSACIÓN A CORTO PLAZO
    # ─────────────────────────────────────────────────────────────────────────

    def agregar_mensaje_usuario(self, mensaje):
        self.historial_conversacion.append({"role": "user", "content": mensaje})

    def agregar_mensaje_asistente(self, mensaje):
        self.historial_conversacion.append({"role": "assistant", "content": mensaje})

    def obtener_historial_completo_texto(self, max_turnos=3):
        mensajes = self.obtener_historial(max_turnos)
        texto = ""
        for msg in mensajes:
            rol = "Usuario" if msg["role"] == "user" else "Aurora"
            texto += f"{rol}: {msg['content']}\n"
        return texto

    def obtener_historial(self, max_turnos=10):
        limite = max_turnos * 2
        return self.historial_conversacion[-limite:]

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTENCIA DE SESIÓN DE CONVERSACIÓN
    # ─────────────────────────────────────────────────────────────────────────

    CARPETA_CONVERSACIONES = "conversaciones"
    MAX_CONVERSACIONES_GUARDADAS = 5

    def guardar_conversacion(self):
        """
        Guarda el historial de conversación actual como un archivo JSON en
        la carpeta 'conversaciones/', con timestamp en el nombre.
        Mantiene un máximo de MAX_CONVERSACIONES_GUARDADAS archivos.
        No guarda si el historial está vacío.
        """
        if not self.historial_conversacion:
            return

        os.makedirs(self.CARPETA_CONVERSACIONES, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"sesion_{timestamp}.json"
        ruta = os.path.join(self.CARPETA_CONVERSACIONES, nombre)

        datos = {
            "fecha": datetime.datetime.now().isoformat(),
            "mensajes": self.historial_conversacion
        }

        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)

            # Rotar: eliminar las más antiguas si superan el límite
            archivos = sorted(
                [os.path.join(self.CARPETA_CONVERSACIONES, fn)
                 for fn in os.listdir(self.CARPETA_CONVERSACIONES)
                 if fn.startswith("sesion_") and fn.endswith(".json")],
                key=os.path.getmtime
            )
            while len(archivos) > self.MAX_CONVERSACIONES_GUARDADAS:
                os.remove(archivos.pop(0))

            print(f"[Conversación guardada en {nombre}]")
        except Exception as e:
            print(f"[Error guardando conversación]: {e}")

    def cargar_ultima_conversacion(self):
        """
        Carga el historial de la sesión más reciente guardada en 'conversaciones/'.
        Devuelve una lista de mensajes, o [] si no hay ninguna guardada.
        """
        if not os.path.exists(self.CARPETA_CONVERSACIONES):
            return []

        archivos = sorted(
            [os.path.join(self.CARPETA_CONVERSACIONES, fn)
             for fn in os.listdir(self.CARPETA_CONVERSACIONES)
             if fn.startswith("sesion_") and fn.endswith(".json")],
            key=os.path.getmtime
        )

        if not archivos:
            return []

        ultimo = archivos[-1]
        try:
            with open(ultimo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            mensajes = datos.get("mensajes", [])
            fecha = datos.get("fecha", "desconocida")
            print(f"[Cargando última sesión del {fecha[:10]}... {len(mensajes)//2} turno(s)]")
            return mensajes
        except Exception as e:
            print(f"[Error cargando última sesión]: {e}")
            return []

