import json
import os

class GestorRecursos:
    def __init__(self):
        self.historial_conversacion = []
        self.archivo_memoria = "Recursos/memoria.json"
        self.conocimiento = self._cargar_memoria()
        self.carpeta_textos_conocimiento = "Recursos/conocimiento"
        self.textos_conocimiento = self._cargar_textos_conocimiento()
        
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
                        # Fragmentación simple por párrafos dobles
                        parrafos = texto_completo.split("\n\n")
                        for parrafo in parrafos:
                            if len(parrafo.strip()) > 30: # Ignorar párrafos muy cortos
                                fragmentos.append({
                                    "origen": filename,
                                    "texto": parrafo.strip()
                                })
                except Exception as e:
                    print(f"Error cargando archivo {filename}: {e}")
        return fragmentos

    def _normalizar_texto(self, texto):
        # Normaliza para comparación: minúsculas, sin espacios extra, sin punto final
        if not texto:
            return ""
        t = str(texto).lower().strip()
        if t.endswith('.'):
            t = t.removesuffix('.').strip()
        return t

    def _extraer_palabras_clave(self, texto):
        # Stopwords muy básicas en español para mejorar la búsqueda simple
        stopwords = {"el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "si", "no", "en", "de", "a", "por", "para", "con", "sin", "es", "son", "del", "al", "que", "como", "sobre", "del", "los", "su"}
        palabras = self._normalizar_texto(texto).replace(",", "").replace(".", "").replace("?", "").replace("¿", "").replace("!", "").replace("¡", "").split()
        return [p for p in palabras if p not in stopwords and len(p) > 2]

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

    def buscar_conocimiento(self, consulta, limite=2):
        if not self.textos_conocimiento:
            return []
            
        palabras_consulta = set(self._extraer_palabras_clave(consulta))
        if not palabras_consulta:
            return []

        # Puntuamos cada fragmento según cuántas palabras clave contiene
        resultados_puntuados = []
        for fragmento in self.textos_conocimiento:
            palabras_fragmento = set(self._extraer_palabras_clave(fragmento["texto"]))
            interseccion = palabras_consulta.intersection(palabras_fragmento)
            puntuacion = len(interseccion)
            if puntuacion > 0:
                resultados_puntuados.append((puntuacion, fragmento))
                
        # Ordenamos de mayor a menor puntuación y tomamos los mejores
        resultados_puntuados.sort(key=lambda x: x[0], reverse=True)
        return [f"{res[1]['origen']}: {res[1]['texto']}" for res in resultados_puntuados[:limite]]
        
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
