import queue
import tkinter as tk

from estadisticas import GestorEstadisticas
from frontend.src.pages.MainWorkspace.Views.main_workspace_view import MainWorkspaceViewMixin
from frontend.src.pages.Ajustes.Views.ajustes_view import AjustesViewMixin
from frontend.src.pages.Ajustes.Logic.ajustes_logic import AjustesLogicMixin
from frontend.src.pages.Chat.Logic.chat_logic import ChatLogicMixin
from frontend.src.pages.Chat.Views.chat_view import ChatViewMixin
from frontend.src.pages.MainWorkspace.Views.stats_view import StatsViewMixin


DEFINICIONES_AJUSTES_MODELO = (
    {
        "seccion": "generation",
        "titulo": "Respuesta principal",
        "descripcion": "Parámetros usados para responder al chat. Se aplican al guardar.",
        "campos": (
            {"clave": "temperature", "etiqueta": "Temperatura", "tipo": "float", "ayuda": "Más alto aumenta variación y creatividad."},
            {"clave": "top_p", "etiqueta": "Top-p", "tipo": "float", "ayuda": "Muestreo nucleus; limita la masa de probabilidad."},
            {"clave": "top_k", "etiqueta": "Top-k", "tipo": "int", "ayuda": "Número máximo de tokens candidatos considerados."},
            {"clave": "min_p", "etiqueta": "Min-p", "tipo": "float", "ayuda": "Descarta tokens con probabilidad demasiado baja."},
            {"clave": "typical_p", "etiqueta": "Typical-p", "tipo": "float", "ayuda": "Favorece tokens con sorpresa típica."},
            {"clave": "max_tokens", "etiqueta": "Máx. tokens", "tipo": "int", "ayuda": "Límite de tokens generados por respuesta."},
            {"clave": "seed", "etiqueta": "Seed", "tipo": "optional_int", "ayuda": "Semilla opcional. Déjalo vacío para aleatorio."},
            {"clave": "presence_penalty", "etiqueta": "Presence penalty", "tipo": "float", "ayuda": "Penaliza reutilizar temas ya presentes."},
            {"clave": "frequency_penalty", "etiqueta": "Frequency penalty", "tipo": "float", "ayuda": "Penaliza repetir tokens frecuentes."},
            {"clave": "repeat_penalty", "etiqueta": "Repeat penalty", "tipo": "float", "ayuda": "Reduce repeticiones literales en la salida."},
            {"clave": "tfs_z", "etiqueta": "TFS-z", "tipo": "float", "ayuda": "Tail free sampling para recortar colas de baja calidad."},
            {"clave": "mirostat_mode", "etiqueta": "Mirostat mode", "tipo": "int", "ayuda": "0 desactivado, 1 o 2 activan control adaptativo."},
            {"clave": "mirostat_tau", "etiqueta": "Mirostat tau", "tipo": "float", "ayuda": "Objetivo de sorpresa para Mirostat."},
            {"clave": "mirostat_eta", "etiqueta": "Mirostat eta", "tipo": "float", "ayuda": "Velocidad de ajuste de Mirostat."},
        ),
    },
    {
        "seccion": "thought",
        "titulo": "Pensamiento interno",
        "descripcion": "Parámetros usados en clasificación, filtrado y reflexión interna.",
        "campos": (
            {"clave": "temperature", "etiqueta": "Temperatura", "tipo": "float", "ayuda": "Suele convenir más baja para tareas internas."},
            {"clave": "top_p", "etiqueta": "Top-p", "tipo": "float", "ayuda": "Controla el muestreo nucleus del pensamiento."},
            {"clave": "top_k", "etiqueta": "Top-k", "tipo": "int", "ayuda": "Número máximo de candidatos para procesos internos."},
            {"clave": "min_p", "etiqueta": "Min-p", "tipo": "float", "ayuda": "Filtrado adicional de tokens poco probables."},
            {"clave": "typical_p", "etiqueta": "Typical-p", "tipo": "float", "ayuda": "Ajuste fino de diversidad típica."},
            {"clave": "max_tokens", "etiqueta": "Máx. tokens", "tipo": "int", "ayuda": "Límite base para pensamientos internos."},
            {"clave": "seed", "etiqueta": "Seed", "tipo": "optional_int", "ayuda": "Semilla opcional para reproducibilidad."},
            {"clave": "presence_penalty", "etiqueta": "Presence penalty", "tipo": "float", "ayuda": "Penalización por volver sobre temas ya usados."},
            {"clave": "frequency_penalty", "etiqueta": "Frequency penalty", "tipo": "float", "ayuda": "Penaliza repeticiones frecuentes en pensamiento."},
            {"clave": "repeat_penalty", "etiqueta": "Repeat penalty", "tipo": "float", "ayuda": "Reduce repeticiones token a token."},
            {"clave": "tfs_z", "etiqueta": "TFS-z", "tipo": "float", "ayuda": "Recorte de cola para tareas internas."},
            {"clave": "mirostat_mode", "etiqueta": "Mirostat mode", "tipo": "int", "ayuda": "Modo de control adaptativo de entropía."},
            {"clave": "mirostat_tau", "etiqueta": "Mirostat tau", "tipo": "float", "ayuda": "Objetivo de sorpresa de Mirostat."},
            {"clave": "mirostat_eta", "etiqueta": "Mirostat eta", "tipo": "float", "ayuda": "Ritmo de corrección de Mirostat."},
        ),
    },
    {
        "seccion": "initialization",
        "titulo": "Inicialización del modelo",
        "descripcion": "Afecta a cómo se carga el modelo local. Guardar estos cambios recarga el modelo.",
        "campos": (
            {"clave": "n_ctx", "etiqueta": "n_ctx", "tipo": "int", "ayuda": "Tamaño de contexto cargado en memoria."},
            {"clave": "n_threads", "etiqueta": "n_threads", "tipo": "optional_int", "ayuda": "Número de hilos CPU. Vacío deja el valor por defecto."},
            {"clave": "n_gpu_layers", "etiqueta": "n_gpu_layers", "tipo": "int", "ayuda": "Capas en GPU. `-1` intenta usar todas las posibles."},
        ),
    },
    {
        "seccion": "kv_cache",
        "titulo": "KV cache",
        "descripcion": "Tipos opcionales de cuantización para la cache K/V. Guardar estos cambios recarga el modelo.",
        "campos": (
            {"clave": "type_k", "etiqueta": "type_k", "tipo": "optional_text", "ayuda": "Ej.: `q8_0`, `f16` o vacío para el valor por defecto."},
            {"clave": "type_v", "etiqueta": "type_v", "tipo": "optional_text", "ayuda": "Ej.: `q8_0`, `f16` o vacío para el valor por defecto."},
        ),
    },
)
class AuroraGUI(
    MainWorkspaceViewMixin,
    AjustesViewMixin,
    AjustesLogicMixin,
    ChatLogicMixin,
    ChatViewMixin,
    StatsViewMixin,
):
    DEFINICIONES_AJUSTES_MODELO = DEFINICIONES_AJUSTES_MODELO
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Proyecto Aurora")
        self.root.minsize(1180, 780)
        self._ajustar_ventana_inicial()

        self.event_queue = queue.Queue()
        self.gestor = None
        self.lista_hilos = []
        self.esta_lista = False
        self.esta_ocupada = False
        self.cierre_pendiente = False
        self.total_mensajes = 0
        self.ultimo_evento_reflexion = ""
        self.ultima_firma_fuentes_reflexion = None
        self.contador_fuentes_reflexion = 0
        self.bloques_fuentes_reflexion = {}
        self.contextos_renderizados = set()
        self.burbujas_chat = []
        self.separador_chat_insertado = False
        self.vista_activa = "chat"
        self.api_server = None
        self.archivo_ajustes_ui = "ui_settings.json"
        self.archivo_config_modelo = "config.json"
        self.ventana_ajustes = None
        self.var_modo_oscuro = None
        self.vars_ajustes_modelo = {}
        self.widgets_ajustes = {}
        self.modo_oscuro = False
        self._botones_ui = {}
        self.gestor_estadisticas = GestorEstadisticas()
        self._widgets_estadisticas = {}

        self._configurar_estilos()
        self.tamano_historial_min = 14
        self.tamano_historial_max = 38
        self.tamano_historial = self.fuentes["body_chat"][1]
        self._cargar_ajustes_ui()
        self._configurar_estilos()
        self._construir_interfaz()
        self._registrar_eventos()
        self._programar_inicializacion()

    def run(self):
        self.root.mainloop()

    def _ajustar_ventana_inicial(self):
        self.root.update_idletasks()
        try:
            self.root.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.root.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass

        ancho = self.root.winfo_screenwidth()
        alto = self.root.winfo_screenheight()
        self.root.geometry(f"{ancho}x{alto}+0+0")

    def _configurar_estilos(self):
        if self.modo_oscuro:
            self.colores = {
                "app_bg": "#111b21",
                "panel": "#0b141a",
                "panel_alt": "#202c33",
                "panel_soft": "#111b21",
                "border": "#0f1a20",
                "accent": "#00a884",
                "accent_active": "#008069",
                "text_primary": "#e9edef",
                "text_secondary": "#cfd4d6",
                "text_muted": "#8696a0",
                "success": "#00a884",
                "warning": "#53bdeb",
                "danger": "#ff6b6b",
                "user_bubble": "#005c4b",
                "assistant_bubble": "#202c33",
                "system_bubble": "#182229",
                "input_bg": "#202c33",
                "header_text": "#e9edef",
                "header_muted": "#8696a0",
                "action_active": "#103529",
                "action_inactive": "#b7c4cc",
                "button_tab_bg": "#16242c",
                "button_tab_hover": "#20313a",
                "button_tab_fg": "#dbe5e8",
                "button_tab_active_bg": "#00a884",
                "button_tab_active_hover": "#12b896",
                "button_tab_active_fg": "#ffffff",
                "button_primary_bg": "#25d366",
                "button_primary_hover": "#3be07c",
                "button_primary_fg": "#062720",
                "button_primary_disabled_bg": "#18252b",
                "button_primary_disabled_fg": "#6f828b",
                "button_utility_bg": "#142129",
                "button_utility_hover": "#1c2c35",
                "button_utility_fg": "#d9e4e8",
                "button_send_bg": "#00a884",
                "button_send_hover": "#12b896",
                "button_send_fg": "#ffffff",
                "button_border": "#29404a",
                "button_active_border": "#32d2b0",
                "button_disabled_border": "#1d2d34",
                "paper_shadow": "#091116",
                "field_bg": "#2a3942",
                "field_border": "#2a3942",
                "surface_white": "#202c33",
                "surface_line": "#2f3b43",
                "chip_bg": "#182229",
                "bubble_border": "#202c33",
                "avatar_bg": "#dfe5e7",
                "avatar_fg": "#202c33",
            }
        else:
            self.colores = {
                "app_bg": "#d1d7db",
                "panel": "#efeae2",
                "panel_alt": "#075e54",
                "panel_soft": "#054d44",
                "border": "#d1d7db",
                "accent": "#25d366",
                "accent_active": "#1faa59",
                "text_primary": "#111b21",
                "text_secondary": "#3b4a54",
                "text_muted": "#667781",
                "success": "#25d366",
                "warning": "#53bdeb",
                "danger": "#e74c3c",
                "user_bubble": "#d9fdd3",
                "assistant_bubble": "#ffffff",
                "system_bubble": "#fff3c4",
                "input_bg": "#f0f2f5",
                "header_text": "#ffffff",
                "header_muted": "#d7efe8",
                "action_active": "#e7fce3",
                "action_inactive": "#d7efe8",
                "button_tab_bg": "#0c5f54",
                "button_tab_hover": "#117062",
                "button_tab_fg": "#eefaf6",
                "button_tab_active_bg": "#25d366",
                "button_tab_active_hover": "#34de75",
                "button_tab_active_fg": "#ffffff",
                "button_primary_bg": "#25d366",
                "button_primary_hover": "#1fbe5a",
                "button_primary_fg": "#ffffff",
                "button_primary_disabled_bg": "#47746f",
                "button_primary_disabled_fg": "#d4e6e2",
                "button_utility_bg": "#0a584f",
                "button_utility_hover": "#0e6a5d",
                "button_utility_fg": "#edf7f5",
                "button_send_bg": "#128c7e",
                "button_send_hover": "#159d8d",
                "button_send_fg": "#ffffff",
                "button_border": "#1e7a6d",
                "button_active_border": "#92f1bc",
                "button_disabled_border": "#648a85",
                "paper_shadow": "#e2d8cb",
                "field_bg": "#ffffff",
                "field_border": "#d9dee3",
                "surface_white": "#ffffff",
                "surface_line": "#d8d5cf",
                "chip_bg": "#d8f4ff",
                "bubble_border": "#d5d7db",
                "avatar_bg": "#f5f7f8",
                "avatar_fg": "#075e54",
            }
        self.fuentes = {
            "hero": ("Helvetica", 18, "bold"),
            "section": ("Helvetica", 18, "bold"),
            "card_title": ("Helvetica", 14, "bold"),
            "label": ("Helvetica", 13, "bold"),
            "body": ("Helvetica", 14),
            "body_large": ("Helvetica", 16),
            "body_chat": ("Helvetica", 17),
            "body_chat_small": ("Helvetica", 15),
            "caption": ("Helvetica", 12),
            "caption_bold": ("Helvetica", 12, "bold"),
            "caption_italic": ("Helvetica", 13, "italic"),
        }

        self.root.configure(bg=self.colores["app_bg"])

    def _crear_boton_ui(self, parent, text, command, estilo="tab", padx=14, pady=7, font=None):
        boton = tk.Label(
            parent,
            text=text,
            bd=0,
            relief="flat",
            padx=padx,
            pady=pady,
            font=font or self.fuentes["caption_bold"],
            cursor="hand2",
        )
        self._botones_ui[boton] = {
            "command": command,
            "estilo": estilo,
            "state": "normal",
            "hover": False,
            "selected": False,
            "font": font or self.fuentes["caption_bold"],
        }
        boton.bind("<Button-1>", lambda _event, widget=boton: self._ejecutar_boton_ui(widget))
        boton.bind("<Enter>", lambda _event, widget=boton: self._actualizar_hover_boton_ui(widget, True))
        boton.bind("<Leave>", lambda _event, widget=boton: self._actualizar_hover_boton_ui(widget, False))
        self._aplicar_estilo_boton_ui(boton)
        return boton

    def _ejecutar_boton_ui(self, boton):
        meta = self._botones_ui.get(boton)
        if not meta or meta["state"] == "disabled":
            return
        meta["command"]()

    def _actualizar_hover_boton_ui(self, boton, hover):
        meta = self._botones_ui.get(boton)
        if not meta:
            return
        meta["hover"] = hover
        self._aplicar_estilo_boton_ui(boton)

    def _establecer_estado_boton_ui(self, boton, estado):
        meta = self._botones_ui.get(boton)
        if not meta:
            return
        meta["state"] = estado
        if estado == "disabled":
            meta["hover"] = False
        self._aplicar_estilo_boton_ui(boton)

    def _establecer_seleccion_boton_ui(self, boton, seleccionado):
        meta = self._botones_ui.get(boton)
        if not meta:
            return
        meta["selected"] = seleccionado
        self._aplicar_estilo_boton_ui(boton)

    def _aplicar_estilo_boton_ui(self, boton):
        if not boton.winfo_exists():
            self._botones_ui.pop(boton, None)
            return

        meta = self._botones_ui.get(boton)
        if not meta:
            return

        deshabilitado = meta["state"] == "disabled"
        hover = meta["hover"] and not deshabilitado
        seleccionado = meta["selected"]
        estilo = meta["estilo"]

        if estilo == "tab":
            if seleccionado:
                bg = self.colores["button_tab_active_hover"] if hover else self.colores["button_tab_active_bg"]
                fg = self.colores["button_tab_active_fg"]
                border = self.colores["button_active_border"]
            else:
                bg = self.colores["button_tab_hover"] if hover else self.colores["button_tab_bg"]
                fg = self.colores["button_tab_fg"]
                border = self.colores["button_border"]
        elif estilo == "primary":
            if deshabilitado:
                bg = self.colores["button_primary_disabled_bg"]
                fg = self.colores["button_primary_disabled_fg"]
                border = self.colores["button_disabled_border"]
            else:
                bg = self.colores["button_primary_hover"] if hover else self.colores["button_primary_bg"]
                fg = self.colores["button_primary_fg"]
                border = self.colores["button_active_border"]
        elif estilo == "send":
            if deshabilitado:
                bg = self.colores["button_primary_disabled_bg"]
                fg = self.colores["button_primary_disabled_fg"]
                border = self.colores["button_disabled_border"]
            else:
                bg = self.colores["button_send_hover"] if hover else self.colores["button_send_bg"]
                fg = self.colores["button_send_fg"]
                border = self.colores["button_active_border"]
        else:
            if deshabilitado:
                bg = self.colores["button_primary_disabled_bg"]
                fg = self.colores["button_primary_disabled_fg"]
                border = self.colores["button_disabled_border"]
            else:
                bg = self.colores["button_utility_hover"] if hover else self.colores["button_utility_bg"]
                fg = self.colores["button_utility_fg"]
                border = self.colores["button_border"]

        boton.configure(
            bg=bg,
            fg=fg,
            font=meta["font"],
            cursor="hand2" if not deshabilitado else "arrow",
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
        )
