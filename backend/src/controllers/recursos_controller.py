import json
import os
import datetime
from typing import List, Dict, Optional, Any

class GestorRecursos:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.historial_conversacion: List[Dict[str, str]] = []
        self.base_dir: str = os.path.dirname(os.path.abspath(__file__))
        self.archivo_memoria: str = os.path.join(self.base_dir, "Recursos", "memoria.json")
        self.conocimiento: Optional[List[Dict[str, Any]]] = None
        self.carpeta_textos_conocimiento: str = os.path.join(self.base_dir, "Recursos", "conocimiento")
        self.carpeta_conversaciones: str = os.path.join(self.base_dir, "conversaciones")
        self.textos_conocimiento: List[Dict[str, Any]] = self._cargar_textos_conocimiento()

    def _emit_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

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
            self._emit_status(f"[Error guardando memoria]: {e}")

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

    def buscar_conocimiento(self, consulta, historial=None, limite=4):
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

        seleccionados_base = [res[1] for res in puntuados[:limite]]
        if seleccionados_base and len(seleccionados_base) < limite:
            seleccionados_base = self._expandir_fragmentos_vecinos(seleccionados_base, max_total=limite)

        seleccionados = []
        for fragmento in seleccionados_base:
            frag = dict(fragmento)
            contexto = self._obtener_contexto_expandido_fragmento(
                origen=frag.get("origen", ""),
                linea_inicio=frag.get("linea_inicio", 0),
                linea_fin=frag.get("linea_fin", 0),
                margen_lineas=8,
                max_chars=2200,
            )
            if contexto:
                frag["texto_contexto"] = contexto["texto"]
                frag["linea_inicio_contexto"] = contexto["linea_inicio"]
                frag["linea_fin_contexto"] = contexto["linea_fin"]
            else:
                frag["texto_contexto"] = frag.get("texto", "")
                frag["linea_inicio_contexto"] = frag.get("linea_inicio", 0)
                frag["linea_fin_contexto"] = frag.get("linea_fin", 0)
            seleccionados.append(frag)

        return seleccionados

    def _expandir_fragmentos_vecinos(self, fragmentos_base, max_total):
        if not fragmentos_base or max_total <= len(fragmentos_base):
            return fragmentos_base

        por_origen = {}
        for frag in self.textos_conocimiento:
            origen = frag.get("origen", "")
            por_origen.setdefault(origen, []).append(frag)

        for origen in por_origen:
            por_origen[origen].sort(key=lambda f: f.get("linea_inicio", 0))

        resultado = list(fragmentos_base)
        claves = {
            (
                f.get("origen", ""),
                f.get("linea_inicio", 0),
                f.get("linea_fin", 0),
            )
            for f in resultado
        }

        hubo_cambios = True
        while len(resultado) < max_total and hubo_cambios:
            hubo_cambios = False
            actuales = list(resultado)
            for base in actuales:
                origen = base.get("origen", "")
                candidatos = por_origen.get(origen, [])
                if not candidatos:
                    continue

                idx_base = None
                for idx, cand in enumerate(candidatos):
                    if (
                        cand.get("linea_inicio", 0) == base.get("linea_inicio", 0)
                        and cand.get("linea_fin", 0) == base.get("linea_fin", 0)
                    ):
                        idx_base = idx
                        break

                if idx_base is None:
                    continue

                for desplazamiento in (-1, 1):
                    idx_vecino = idx_base + desplazamiento
                    if idx_vecino < 0 or idx_vecino >= len(candidatos):
                        continue

                    vecino = candidatos[idx_vecino]
                    clave = (
                        vecino.get("origen", ""),
                        vecino.get("linea_inicio", 0),
                        vecino.get("linea_fin", 0),
                    )
                    if clave in claves:
                        continue

                    resultado.append(vecino)
                    claves.add(clave)
                    hubo_cambios = True

                    if len(resultado) >= max_total:
                        return resultado

        return resultado

    def _obtener_contexto_expandido_fragmento(
        self,
        origen,
        linea_inicio,
        linea_fin,
        margen_lineas=8,
        max_chars=2200,
    ):
        if not origen:
            return None

        ruta = os.path.join(self.carpeta_textos_conocimiento, origen)
        if not os.path.exists(ruta):
            return None

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                lineas = f.read().splitlines()
        except Exception:
            return None

        if not lineas:
            return None

        inicio = max(0, int(linea_inicio) - margen_lineas)
        fin = min(len(lineas) - 1, int(linea_fin) + margen_lineas)
        texto = "\n".join(lineas[inicio:fin + 1]).strip()
        if len(texto) > max_chars:
            texto = texto[:max_chars].rstrip() + "..."

        return {
            "texto": texto,
            "linea_inicio": inicio,
            "linea_fin": fin,
        }

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
                        lineas = f.read().splitlines()

                    inicio = None
                    buffer = []

                    for idx, linea in enumerate(lineas):
                        if linea.strip():
                            if inicio is None:
                                inicio = idx
                            buffer.append(linea.rstrip())
                            continue

                        if inicio is not None:
                            texto_fragmento = "\n".join(buffer).strip()
                            if len(texto_fragmento) > 30:
                                fragmentos.append({
                                    "origen": filename,
                                    "texto": texto_fragmento,
                                    "linea_inicio": inicio,
                                    "linea_fin": idx - 1,
                                })
                            inicio = None
                            buffer = []

                    if inicio is not None:
                        texto_fragmento = "\n".join(buffer).strip()
                        if len(texto_fragmento) > 30:
                            fragmentos.append({
                                "origen": filename,
                                "texto": texto_fragmento,
                                "linea_inicio": inicio,
                                "linea_fin": len(lineas) - 1,
                            })
                except Exception as e:
                    self._emit_status(f"[Error cargando archivo {filename}]: {e}")
        return fragmentos

    # ─────────────────────────────────────────────────────────────────────────
    # HISTORIAL DE CONVERSACIÓN A CORTO PLAZO
    # ─────────────────────────────────────────────────────────────────────────

    def agregar_mensaje_usuario(self, mensaje):
        self.historial_conversacion.append({"role": "user", "content": mensaje})
        self.guardar_conversacion()

    def agregar_mensaje_asistente(self, mensaje):
        self.historial_conversacion.append({"role": "assistant", "content": mensaje})
        self.guardar_conversacion()

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
    ARCHIVO_SESION_ACTUAL = "sesion_actual.json"
    MAX_CONVERSACIONES_GUARDADAS = 5

    def _ruta_sesion_actual(self):
        return os.path.join(self.carpeta_conversaciones, self.ARCHIVO_SESION_ACTUAL)

    def guardar_conversacion(self, force=False):
        """
        Guarda (sobrescribe) la sesión activa en conversaciones/sesion_actual.json.
        Si `force=False`, no guarda cuando el historial está vacío.
        """
        if not force and not self.historial_conversacion:
            return

        os.makedirs(self.carpeta_conversaciones, exist_ok=True)

        ruta = self._ruta_sesion_actual()

        datos = {
            "fecha": datetime.datetime.now().isoformat(),
            "mensajes": self.historial_conversacion
        }

        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            self._emit_status(f"[Error guardando conversación]: {e}")

    def reiniciar_conversacion(self):
        """
        Limpia el historial conversacional en memoria y lo persiste
        inmediatamente como sesión activa vacía.
        """
        self.historial_conversacion = []
        self.guardar_conversacion(force=True)

    def cargar_ultima_conversacion(self):
        """
        Carga primero la sesión activa (sesion_actual.json). Si no existe,
        hace fallback a la última sesión legacy con timestamp.
        Devuelve una lista de mensajes, o [] si no hay ninguna guardada.
        """
        if not os.path.exists(self.carpeta_conversaciones):
            return []

        ruta_actual = self._ruta_sesion_actual()
        if os.path.exists(ruta_actual):
            try:
                with open(ruta_actual, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                mensajes = datos.get("mensajes", [])
                fecha = datos.get("fecha", "desconocida")
                self._emit_status(
                    f"[Cargando sesión actual del {fecha[:10]}... {len(mensajes)//2} turno(s)]"
                )
                return mensajes
            except Exception as e:
                self._emit_status(f"[Error cargando sesión actual]: {e}")

        # Fallback legacy: sesiones por timestamp.
        archivos = sorted(
            [os.path.join(self.carpeta_conversaciones, fn)
             for fn in os.listdir(self.carpeta_conversaciones)
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
            self._emit_status(f"[Cargando última sesión del {fecha[:10]}... {len(mensajes)//2} turno(s)]")
            return mensajes
        except Exception as e:
            self._emit_status(f"[Error cargando última sesión]: {e}")
            return []
