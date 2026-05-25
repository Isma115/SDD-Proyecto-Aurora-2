Sección: Main Workspace
Ficheros main workspace:
frontend/src/pages/MainWorkspace/Logic/aurora_gui.py
frontend/src/pages/MainWorkspace/Views/main_workspace_view.py
frontend/src/pages/MainWorkspace/Views/stats_view.py
aurora_gui.py
main.py

Segmento: Arranque de aplicación principal
class AuroraGUI(MainWorkspaceViewMixin, AjustesViewMixin, AjustesLogicMixin, ChatLogicMixin, ChatViewMixin, StatsViewMixin):
def __init__(self):
def run(self):
def main():
def main_cli():

Segmento: Ventana y estilos base
DEFINICIONES_AJUSTES_MODELO = (
def _ajustar_ventana_inicial(self):
def _configurar_estilos(self):

Segmento: Botones reutilizables de la interfaz
def _crear_boton_ui(self, parent, text, command, estilo, padx, pady, font):
def _ejecutar_boton_ui(self, boton):
def _actualizar_hover_boton_ui(self, boton, hover):
def _establecer_estado_boton_ui(self, boton, estado):
def _establecer_seleccion_boton_ui(self, boton, seleccionado):
def _aplicar_estilo_boton_ui(self, boton):

Segmento: Construcción del workspace principal
class MainWorkspaceViewMixin:
def _construir_interfaz(self):
def _construir_area_principal(self):

Segmento: Navegación de vistas principales
def _mostrar_vista(self, vista):
def _pintar_boton_vista(self, boton, activo):

Segmento: Tema visual del workspace
def _repintar_avatar(self):
def _aplicar_tema_actual(self):


Sección: Chat
Ficheros chat:
frontend/src/pages/Chat/Views/chat_view.py
frontend/src/pages/Chat/Logic/chat_logic.py
backend/src/controllers/llm_controller.py
backend/src/controllers/recursos_controller.py
gestorLLM.py
recursos.py

Segmento: Lógica de inicialización del chat
class ChatLogicMixin:
def _programar_inicializacion(self):
def _lanzar_hilo(self, target):
def _inicializar_gestor(self):
def _inicializar_api_embebida(self, gestor):
def _emitir_estado_desde_hilo(self, mensaje):
def _procesar_eventos(self):
def _actualizar_estado(self, mensaje):
def _marcar_lista(self, gestor):
def _mostrar_api_lista(self, api_server):
def _mostrar_error_api(self, error):
def _mostrar_error_inicializacion(self, error):

Segmento: Entrada y envío de mensajes
def _registrar_eventos(self):
def _manejar_return(self, event):
def _enviar_mensaje(self):
def _generar_respuesta(self, mensaje):
def _mostrar_respuesta(self, respuesta):
def _mostrar_error(self, error):

Segmento: Estado de controles de conversación
class ChatViewMixin:
def _actualizar_estado_controles(self):
def _sincronizar_presencia_desde_estado(self, texto):

Segmento: Renderizado visual del historial
def _reconstruir_chat_visual(self):
def _configurar_tags_chat(self):
def _fuente_con_tamano(self, fuente_base, tamano):
def _formatear_contenido_visual_chat(self, autor, contenido):
def _agregar_mensaje_chat(self, autor, contenido, speaker_tag, message_tag):
def _crear_burbuja_chat(self, autor, contenido):
def _agregar_chip_chat(self, texto):
def _hora_visual_chat(self):

Segmento: Scroll y redimensionado del chat
def _scroll_chat_mousewheel(self, event):
def _registrar_scroll_en_widget(self, widget):
def _al_redimensionar_chat(self, _event):
def _actualizar_burbujas_chat(self):

Segmento: Sesión y conversación activa
def _mostrar_sesion_anterior(self):
def _iniciar_nueva_conversacion(self):
def guardar_sesion(self):
def reiniciar_conversacion_actual(self):

Segmento: Contexto del modelo mostrado en interfaz
def _insertar_placeholder_contexto(self):
def _sincronizar_historial_contexto_modelo(self):
def _construir_texto_contexto_modelo(self, snapshot):
def _agregar_contexto_completo(self, snapshot):

Segmento: Reflexión y fuentes de conocimiento
def _agregar_mensaje_sistema(self, contenido):
def _agregar_reflexion(self, contenido):
def _construir_texto_contexto_fuentes(self, fuentes):
def _agregar_reflexion_fuentes(self, evento_fuentes):
def _toggle_contexto_fuentes_reflexion(self, bloque_id):

Segmento: Ajustes UI del chat
def _cargar_ajustes_ui(self):
def _guardar_ajustes_ui(self):
def _ajustar_tamano_historial(self, delta):
def _aumentar_tamano_historial(self, _event):
def _reducir_tamano_historial(self, _event):

Segmento: Cierre de la aplicación desde chat
def _mostrar_ajustes_guardados(self, recargo_modelo):
def _mostrar_error_ajustes(self, error):
def _solicitar_cierre(self):
def _cerrar_aplicacion(self):

Segmento: Configuración y carga del motor LLM
DEFAULT_CONFIG = {
def crear_configuracion_por_defecto():
class MotorLLM:
def __init__(self, config_path, status_callback):
def _emit_status(self, message):
def _load_or_create_config(self):
def _normalizar_config(self, config):
def guardar_configuracion(self, config):
def _actualizar_ruta_modelo(self):
def _requiere_recarga_modelo(self, config_anterior, config_nueva):
def recargar_modelo(self):
def actualizar_configuracion(self, nueva_config, recargar_modelo):
def _resolver_tipo_kv(self, valor):
def _download_and_load_model(self):
def _obtener_parametros_generacion(self, seccion, max_tokens, max_tokens_por_defecto):
def build_response_messages(self, system_prompt, history):
def generate_response(self, system_prompt, history, max_tokens):
def generate_thought(self, prompt, max_tokens):

Segmento: Orquestación conversacional del LLM
class GestorLLM:
def __init__(self, status_callback):
def _emit_status(self, message):
def _clonar_mensajes(self, mensajes):
def _registrar_contexto_modelo(self, prompt_enriquecido, historial, intencion):
def obtener_historial_contexto_modelo(self):
def _crear_evento_fuentes_conocimiento(self, fragmentos):
def obtener_respuesta(self, mensaje_usuario):
def _clasificar_intencion(self, mensaje, historial):
def _filtrar_candidatos_llm(self, candidatos, tipo, mensaje, historial):
def _proceso_pensamiento_interno(self):
def _guardar_log_contexto(self, prompt, historial, mensajes_modelo):
def _guardar_log_pensamiento(self, prompt):

Segmento: Memoria y recursos conversacionales
class GestorRecursos:
def __init__(self, status_callback):
def _emit_status(self, message):
def _cargar_memoria(self):
def _persistir_memoria(self, datos):
def _asegurar_memoria_cargada(self):
def _normalizar_texto(self, texto):
def _extraer_palabras_clave(self, texto):
def _detectar_categoria(self, texto):
def _score_recuerdo(self, recuerdo_obj, palabras_contexto_set, historial_texto):
def _score_fragmento_conocimiento(self, fragmento, palabras_consulta_set, historial_texto):
def guardar_recuerdo(self, recuerdo):
def buscar_recuerdos(self, contexto, historial, limite):
def buscar_conocimiento(self, consulta, historial, limite):
def _expandir_fragmentos_vecinos(self, fragmentos_base, max_total):
def _obtener_contexto_expandido_fragmento(self, origen, linea_inicio, linea_fin, margen_lineas, max_chars):
def obtener_todos_recuerdos_texto(self):
def _cargar_textos_conocimiento(self):
def agregar_mensaje_usuario(self, mensaje):
def agregar_mensaje_asistente(self, mensaje):
def obtener_historial_completo_texto(self, max_turnos):
def obtener_historial(self, max_turnos):
def _ruta_sesion_actual(self):
def guardar_conversacion(self, force):
def reiniciar_conversacion(self):
def cargar_ultima_conversacion(self):


Sección: Ajustes
Ficheros ajustes:
frontend/src/pages/Ajustes/Views/ajustes_view.py
frontend/src/pages/Ajustes/Logic/ajustes_logic.py
frontend/src/pages/MainWorkspace/Logic/aurora_gui.py
config.json
ui_settings.json
motorLLM.py

Segmento: Ventana de ajustes
class AjustesViewMixin:
def _abrir_ajustes(self):
def _actualizar_scrollregion_ajustes(self, _event):
def _ajustar_ancho_contenido_ajustes(self, event):
def _desplazar_canvas_ajustes(self, event):

Segmento: Tarjetas y campos de ajustes
def _crear_tarjeta_ajustes(self, parent, titulo, descripcion):
def _crear_campo_ajuste_modelo(self, parent, seccion, campo, valor):

Segmento: Normalización y carga de configuración
class AjustesLogicMixin:
def _normalizar_configuracion_modelo(self, config):
def _cargar_configuracion_modelo(self):
def _formatear_valor_ajuste(self, valor, tipo):
def _interpretar_valor_ajuste(self, texto, tipo, etiqueta):

Segmento: Guardado y aplicación de ajustes del modelo
def _guardar_ajustes_modelo(self):
def _aplicar_ajustes_modelo_en_hilo(self, config_modelo):

Segmento: Tema y cierre de ajustes
def _aplicar_tema_ventana_ajustes(self):
def _cerrar_ajustes(self):
def _alternar_modo_oscuro_desde_ui(self):

Segmento: Estructuras de configuración de ajustes
DEFINICIONES_AJUSTES_MODELO = (
DEFAULT_CONFIG = {
def crear_configuracion_por_defecto():


Sección: API local
Ficheros api local:
backend/src/controllers/api_controller.py
backend/src/controllers/llm_controller.py
backend/src/models/estadisticas_model.py
api.py

Segmento: Modelos de request y response
class ChatRequest(BaseModel):
class ChatResponse(BaseModel):
class HistoryResponse(BaseModel):

Segmento: Inicialización de la aplicación FastAPI
def obtener_ip_local():
def crear_app(gestor_inicial, gestor_factory, gestor_estadisticas):
app = crear_app()

Segmento: Servidor embebido de Aurora
class AuroraEmbeddedAPIServer:
def __init__(self, gestor, host, port, gestor_estadisticas):
def start(self, wait_timeout):
def stop(self, wait_timeout):


Sección: Estadísticas
Ficheros estadísticas:
frontend/src/pages/MainWorkspace/Views/stats_view.py
backend/src/models/estadisticas_model.py
estadisticas.py

Segmento: Estructuras base de estadísticas
ARCHIVO_ESTADISTICAS = "estadisticas.json"
DIRECTORIO_CONVERSACIONES = "conversaciones"
DURACION_RONDA_SEGUNDOS = 300
NIVELES_COMUNICADOR = (
def _plantilla_estadisticas():

Segmento: Persistencia de estadísticas
class GestorEstadisticas:
def __init__(self, archivo, directorio_conversaciones):
def _cargar(self):
def _guardar(self):

Segmento: Registro de actividad y rachas
def registrar_mensaje(self, longitud_mensaje):
def _actualizar_racha(self):
def _contar_conversaciones(self):
def _promedio_mensajes_por_conversacion(self):

Segmento: Ronda activa de 5 minutos
def _gestionar_ronda(self):
def _iniciar_ronda(self):
def _finalizar_ronda(self):
def obtener_estado_ronda(self):

Segmento: Nivel y resumen estadístico
def obtener_nivel(self):
def obtener_resumen(self):
def detener(self):

Segmento: Vista de tarjetas de estadísticas
class StatsViewMixin:
def _construir_estadisticas_tab(self):
def _crear_tarjeta_stat(self, parent, key, emoji, titulo, valor_inicial, color_acento, columna):
def _actualizar_valor_stat(self, key, valor):

Segmento: Vista de ronda y nivel
def _construir_indicador_ronda(self):
def _construir_barra_nivel(self):
def _actualizar_estadisticas_ui(self):

Segmento: Vista de gráfica y scroll
def _construir_grafica_progreso(self):
def _scroll_estadisticas(self, event):
def _dibujar_grafica_progreso(self):
def _aplicar_tema_estadisticas(self):
