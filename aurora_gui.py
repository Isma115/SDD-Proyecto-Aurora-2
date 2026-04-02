import re
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from api import AuroraEmbeddedAPIServer
from gestorLLM import GestorLLM


class AuroraGUI:
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
        self.vista_activa = "chat"
        self.api_server = None
        self.archivo_ajustes_ui = "ui_settings.json"

        self._configurar_estilos()
        self.tamano_historial_min = 12
        self.tamano_historial_max = 30
        self.tamano_historial = self.fuentes["body_chat"][1]
        self._cargar_ajustes_ui()
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
        self.colores = {
            "app_bg": "#090b10",
            "panel": "#11141b",
            "panel_alt": "#171b24",
            "panel_soft": "#1d2330",
            "border": "#262e3d",
            "accent": "#7dd3fc",
            "accent_active": "#38bdf8",
            "text_primary": "#ffffff",
            "text_secondary": "#f4f7fb",
            "text_muted": "#cbd5e1",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#fb7185",
            "user_bubble": "#123044",
            "assistant_bubble": "#1b2230",
            "system_bubble": "#161c27",
            "input_bg": "#0d1118",
        }
        self.fuentes = {
            "hero": ("Helvetica", 30, "bold"),
            "section": ("Helvetica", 20, "bold"),
            "card_title": ("Helvetica", 15, "bold"),
            "label": ("Helvetica", 14, "bold"),
            "body": ("Helvetica", 14),
            "body_large": ("Helvetica", 16),
            "body_chat": ("Helvetica", 17),
            "body_chat_small": ("Helvetica", 15),
            "caption": ("Helvetica", 12),
            "caption_bold": ("Helvetica", 12, "bold"),
            "caption_italic": ("Helvetica", 13, "italic"),
        }

        self.root.configure(bg=self.colores["app_bg"])
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure("App.TFrame", background=self.colores["app_bg"])
        estilo.configure("Panel.TFrame", background=self.colores["panel"])
        estilo.configure("SoftPanel.TFrame", background=self.colores["panel_soft"])
        estilo.configure(
            "SidebarTitle.TLabel",
            background=self.colores["panel"],
            foreground=self.colores["text_primary"],
            font=self.fuentes["hero"],
        )
        estilo.configure(
            "SidebarText.TLabel",
            background=self.colores["panel"],
            foreground=self.colores["text_secondary"],
            font=self.fuentes["body"],
        )
        estilo.configure(
            "SectionTitle.TLabel",
            background=self.colores["panel_alt"],
            foreground=self.colores["text_primary"],
            font=self.fuentes["section"],
        )
        estilo.configure(
            "CardTitle.TLabel",
            background=self.colores["panel_soft"],
            foreground=self.colores["text_primary"],
            font=self.fuentes["card_title"],
        )
        estilo.configure(
            "CardText.TLabel",
            background=self.colores["panel_soft"],
            foreground=self.colores["text_secondary"],
            font=self.fuentes["caption"],
        )
        estilo.configure(
            "Primary.TButton",
            background=self.colores["accent"],
            foreground=self.colores["app_bg"],
            borderwidth=0,
            padding=(18, 14),
            font=self.fuentes["label"],
        )
        estilo.map(
            "Primary.TButton",
            background=[
                ("disabled", self.colores["border"]),
                ("active", self.colores["accent_active"]),
                ("!disabled", self.colores["accent"]),
            ],
            foreground=[
                ("disabled", self.colores["text_muted"]),
                ("!disabled", self.colores["app_bg"]),
            ],
        )
        estilo.configure(
            "Secondary.TButton",
            background=self.colores["panel_soft"],
            foreground=self.colores["text_primary"],
            borderwidth=0,
            padding=(18, 14),
            font=self.fuentes["body"],
        )
        estilo.map(
            "Secondary.TButton",
            background=[
                ("disabled", self.colores["border"]),
                ("active", self.colores["panel_alt"]),
                ("!disabled", self.colores["panel_soft"]),
            ],
            foreground=[
                ("disabled", self.colores["text_muted"]),
                ("!disabled", self.colores["text_primary"]),
            ],
        )
        estilo.configure(
            "TabActive.TButton",
            background=self.colores["panel"],
            foreground=self.colores["text_primary"],
            borderwidth=0,
            padding=(14, 7),
            font=self.fuentes["caption_bold"],
        )
        estilo.map(
            "TabActive.TButton",
            background=[
                ("active", self.colores["panel_soft"]),
                ("!disabled", self.colores["panel"]),
            ],
            foreground=[
                ("!disabled", self.colores["text_primary"]),
            ],
        )
        estilo.configure(
            "TabInactive.TButton",
            background=self.colores["panel_soft"],
            foreground=self.colores["text_muted"],
            borderwidth=0,
            padding=(14, 7),
            font=self.fuentes["caption_bold"],
        )
        estilo.map(
            "TabInactive.TButton",
            background=[
                ("active", self.colores["panel"]),
                ("!disabled", self.colores["panel_soft"]),
            ],
            foreground=[
                ("!disabled", self.colores["text_muted"]),
            ],
        )

    def _construir_interfaz(self):
        contenedor = tk.Frame(
            self.root,
            bg=self.colores["app_bg"],
            padx=18,
            pady=14,
        )
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        self.estado_var = tk.StringVar(value="Preparando Aurora...")
        self.servidor_var = tk.StringVar(value="Servidor móvil: iniciando...")

        self.workspace = tk.Frame(
            contenedor,
            bg=self.colores["panel_alt"],
            padx=14,
            pady=10,
        )
        self.workspace.grid(row=0, column=0, sticky="nsew")
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(1, weight=1)

        self._construir_area_principal()

        self._agregar_mensaje_sistema(
            "Aurora se está iniciando. Cuando termine, podrás escribir en la parte inferior."
        )
        self._agregar_reflexion("Inicializando entorno de Aurora...")

    def _construir_area_principal(self):
        tabs_bar = tk.Frame(self.workspace, bg=self.colores["panel_alt"])
        tabs_bar.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        tabs_bar.columnconfigure(3, weight=1)

        self.boton_tab_chat = ttk.Button(
            tabs_bar,
            text="Conversación",
            command=lambda: self._mostrar_vista("chat"),
            style="TabActive.TButton",
        )
        self.boton_tab_chat.grid(row=0, column=0, sticky="w")

        self.boton_tab_reflexion = ttk.Button(
            tabs_bar,
            text="Reflexión de Aurora",
            command=lambda: self._mostrar_vista("reflexion"),
            style="TabInactive.TButton",
        )
        self.boton_tab_reflexion.grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.boton_nueva_conversacion = ttk.Button(
            tabs_bar,
            text="Nueva conversación",
            command=self._iniciar_nueva_conversacion,
            style="TabInactive.TButton",
            state="disabled",
        )
        self.boton_nueva_conversacion.grid(row=0, column=2, sticky="w", padx=(6, 0))

        tk.Label(
            tabs_bar,
            textvariable=self.servidor_var,
            bg=self.colores["panel_alt"],
            fg=self.colores["accent"],
            font=self.fuentes["caption"],
            justify="right",
        ).grid(row=0, column=4, sticky="e", padx=(6, 0))

        contenido = tk.Frame(self.workspace, bg=self.colores["panel_alt"])
        contenido.grid(row=1, column=0, sticky="nsew")
        contenido.columnconfigure(0, weight=1)
        contenido.rowconfigure(0, weight=1)

        self.chat_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=12,
            pady=12,
        )
        self.chat_tab.columnconfigure(0, weight=1)
        self.chat_tab.rowconfigure(0, weight=1)
        self.chat_tab.rowconfigure(1, weight=0, minsize=92)
        self.chat_tab.grid(row=0, column=0, sticky="nsew")

        self.reflexion_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=14,
            pady=14,
        )
        self.reflexion_tab.columnconfigure(0, weight=1)
        self.reflexion_tab.rowconfigure(1, weight=1)
        self.reflexion_tab.grid(row=0, column=0, sticky="nsew")

        self.chat_text = ScrolledText(
            self.chat_tab,
            wrap="word",
            height=18,
            font=self.fuentes["body_chat"],
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            insertbackground=self.colores["text_primary"],
            highlightthickness=0,
            spacing1=0,
            spacing2=0,
            spacing3=0,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        self.chat_text.configure(state="disabled")
        self._configurar_tags_chat()

        composer = tk.Frame(
            self.chat_tab,
            bg=self.colores["panel"],
            padx=8,
            pady=4,
        )
        composer.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        composer.columnconfigure(0, weight=1)

        cuerpo_composer = tk.Frame(
            composer,
            bg=self.colores["panel_soft"],
            highlightthickness=1,
            highlightbackground=self.colores["border"],
            highlightcolor=self.colores["accent"],
            bd=0,
        )
        cuerpo_composer.grid(row=0, column=0, sticky="ew")
        cuerpo_composer.rowconfigure(0, weight=1)
        cuerpo_composer.columnconfigure(0, weight=1)
        cuerpo_composer.grid_propagate(False)
        cuerpo_composer.configure(height=70)

        self.entrada_text = tk.Text(
            cuerpo_composer,
            height=2,
            wrap="word",
            font=self.fuentes["body_large"],
            bg=self.colores["input_bg"],
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=6,
            insertbackground=self.colores["text_primary"],
            highlightthickness=0,
        )
        self.entrada_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.entrada_text.configure(state="disabled")

        self.boton_enviar = ttk.Button(
            cuerpo_composer,
            text="Enviar",
            style="Primary.TButton",
            command=self._enviar_mensaje,
            state="disabled",
        )
        self.boton_enviar.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=6)

        tk.Label(
            self.reflexion_tab,
            text="Pensamiento / reflexión interna",
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            font=self.fuentes["section"],
        ).grid(row=0, column=0, sticky="w")

        self.reflexion_text = ScrolledText(
            self.reflexion_tab,
            wrap="word",
            font=self.fuentes["body"],
            bg=self.colores["input_bg"],
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=16,
            insertbackground=self.colores["text_primary"],
            highlightthickness=1,
            highlightbackground=self.colores["border"],
            highlightcolor=self.colores["accent"],
        )
        self.reflexion_text.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.reflexion_text.configure(state="disabled")
        self.reflexion_text.tag_configure(
            "reflexion_titulo",
            foreground=self.colores["accent"],
            font=self.fuentes["caption_bold"],
            spacing1=8,
        )
        self.reflexion_text.tag_configure(
            "reflexion_texto",
            foreground=self.colores["text_primary"],
            font=self.fuentes["body"],
            spacing3=16,
        )
        self.reflexion_text.tag_configure(
            "reflexion_toggle",
            foreground=self.colores["accent"],
            font=self.fuentes["caption_bold"],
            spacing1=2,
            spacing3=6,
        )
        self.reflexion_text.tag_configure(
            "reflexion_contexto",
            foreground=self.colores["text_secondary"],
            font=self.fuentes["caption"],
            lmargin1=16,
            lmargin2=16,
            spacing1=2,
            spacing3=12,
        )
        self._mostrar_vista("chat")

    def _mostrar_vista(self, vista):
        self.vista_activa = vista
        if vista == "chat":
            self.chat_tab.tkraise()
            self.boton_tab_chat.configure(style="TabActive.TButton")
            self.boton_tab_reflexion.configure(style="TabInactive.TButton")
        else:
            self.reflexion_tab.tkraise()
            self.boton_tab_chat.configure(style="TabInactive.TButton")
            self.boton_tab_reflexion.configure(style="TabActive.TButton")

    def _configurar_tags_chat(self):
        tamano_texto = self.tamano_historial
        tamano_speaker = max(self.tamano_historial_min, tamano_texto - 5)
        tamano_sistema = max(self.tamano_historial_min, tamano_texto - 2)
        tamano_previo = max(self.tamano_historial_min, tamano_texto - 2)
        fuente_speaker = self._fuente_con_tamano(self.fuentes["caption_bold"], tamano_speaker)
        fuente_texto = self._fuente_con_tamano(self.fuentes["body_chat"], tamano_texto)
        fuente_sistema = self._fuente_con_tamano(self.fuentes["caption_italic"], tamano_sistema)
        fuente_previo = self._fuente_con_tamano(self.fuentes["body_chat_small"], tamano_previo)

        self.chat_text.configure(font=fuente_texto)
        self.chat_text.tag_configure(
            "speaker_user",
            foreground=self.colores["accent"],
            font=fuente_speaker,
            spacing1=10,
        )
        self.chat_text.tag_configure(
            "speaker_assistant",
            foreground="#c4b5fd",
            font=fuente_speaker,
            spacing1=10,
        )
        self.chat_text.tag_configure(
            "speaker_system",
            foreground=self.colores["warning"],
            font=fuente_speaker,
            spacing1=10,
        )
        self.chat_text.tag_configure(
            "message_user",
            foreground=self.colores["text_primary"],
            background=self.colores["user_bubble"],
            font=fuente_texto,
            lmargin1=18,
            lmargin2=18,
            rmargin=96,
            spacing1=4,
            spacing3=10,
        )
        self.chat_text.tag_configure(
            "message_assistant",
            foreground=self.colores["text_primary"],
            background=self.colores["assistant_bubble"],
            font=fuente_texto,
            lmargin1=18,
            lmargin2=18,
            rmargin=60,
            spacing1=4,
            spacing3=10,
        )
        self.chat_text.tag_configure(
            "message_system",
            foreground=self.colores["text_primary"],
            background=self.colores["system_bubble"],
            font=fuente_sistema,
            lmargin1=14,
            lmargin2=14,
            rmargin=80,
            spacing1=4,
            spacing3=18,
        )
        self.chat_text.tag_configure(
            "message_previous",
            foreground=self.colores["text_secondary"],
            background=self.colores["panel_soft"],
            font=fuente_previo,
            lmargin1=18,
            lmargin2=18,
            rmargin=80,
            spacing1=4,
            spacing3=10,
        )

    def _registrar_eventos(self):
        self.root.protocol("WM_DELETE_WINDOW", self._solicitar_cierre)
        self.root.bind("<Escape>", lambda _event: self._solicitar_cierre())
        self.entrada_text.bind("<Return>", self._manejar_return)
        self.root.bind_all("<Control-plus>", self._aumentar_tamano_historial)
        self.root.bind_all("<Control-equal>", self._aumentar_tamano_historial)
        self.root.bind_all("<Control-KP_Add>", self._aumentar_tamano_historial)
        self.root.bind_all("<Control-minus>", self._reducir_tamano_historial)
        self.root.bind_all("<Control-KP_Subtract>", self._reducir_tamano_historial)

    def _programar_inicializacion(self):
        self.root.after(100, self._procesar_eventos)
        self._lanzar_hilo(self._inicializar_gestor)

    def _manejar_return(self, event):
        if event.state & 0x0001:
            return None
        self._enviar_mensaje()
        return "break"

    def _fuente_con_tamano(self, fuente_base, tamano):
        familia = fuente_base[0]
        estilo = tuple(fuente_base[2:]) if len(fuente_base) > 2 else ()
        return (familia, tamano, *estilo)

    def _cargar_ajustes_ui(self):
        if not os.path.exists(self.archivo_ajustes_ui):
            return

        try:
            with open(self.archivo_ajustes_ui, "r", encoding="utf-8") as f:
                ajustes = json.load(f)
        except Exception:
            return

        tamano = ajustes.get("tamano_historial_chat")
        if isinstance(tamano, (int, float)):
            tamano_int = int(tamano)
            self.tamano_historial = max(
                self.tamano_historial_min,
                min(self.tamano_historial_max, tamano_int),
            )

    def _guardar_ajustes_ui(self):
        ajustes = {}
        if os.path.exists(self.archivo_ajustes_ui):
            try:
                with open(self.archivo_ajustes_ui, "r", encoding="utf-8") as f:
                    cargado = json.load(f)
                if isinstance(cargado, dict):
                    ajustes = cargado
            except Exception:
                ajustes = {}

        ajustes["tamano_historial_chat"] = self.tamano_historial

        try:
            with open(self.archivo_ajustes_ui, "w", encoding="utf-8") as f:
                json.dump(ajustes, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _ajustar_tamano_historial(self, delta):
        nuevo_tamano = max(
            self.tamano_historial_min,
            min(self.tamano_historial_max, self.tamano_historial + delta),
        )
        if nuevo_tamano == self.tamano_historial:
            return "break"

        self.tamano_historial = nuevo_tamano
        self._configurar_tags_chat()
        self._guardar_ajustes_ui()
        return "break"

    def _aumentar_tamano_historial(self, _event=None):
        return self._ajustar_tamano_historial(1)

    def _reducir_tamano_historial(self, _event=None):
        return self._ajustar_tamano_historial(-1)

    def _lanzar_hilo(self, target, *args):
        hilo = threading.Thread(target=target, args=args, daemon=True)
        self.lista_hilos.append(hilo)
        hilo.start()

    def _inicializar_gestor(self):
        try:
            gestor = GestorLLM(status_callback=self._emitir_estado_desde_hilo)
            self.event_queue.put(("ready", gestor))
        except Exception as exc:
            self.event_queue.put(("init_error", str(exc)))

    def _inicializar_api_embebida(self, gestor):
        try:
            api_server = AuroraEmbeddedAPIServer(gestor=gestor)
            api_server.start()
            self.event_queue.put(("api_ready", api_server))
        except Exception as exc:
            self.event_queue.put(("api_error", str(exc)))

    def _generar_respuesta(self, mensaje):
        try:
            respuesta = self.gestor.obtener_respuesta(mensaje)
            self.event_queue.put(("response", respuesta))
        except Exception as exc:
            self.event_queue.put(("response_error", str(exc)))

    def _emitir_estado_desde_hilo(self, mensaje):
        self.event_queue.put(("status", mensaje))

    def _procesar_eventos(self):
        while True:
            try:
                evento = self.event_queue.get_nowait()
            except queue.Empty:
                break

            tipo = evento[0]
            if tipo == "status":
                self._actualizar_estado(evento[1])
            elif tipo == "ready":
                self._marcar_lista(evento[1])
            elif tipo == "response":
                self._mostrar_respuesta(evento[1])
            elif tipo == "response_error":
                self._mostrar_error(evento[1])
            elif tipo == "init_error":
                self._mostrar_error_inicializacion(evento[1])
            elif tipo == "api_ready":
                self._mostrar_api_lista(evento[1])
            elif tipo == "api_error":
                self._mostrar_error_api(evento[1])

        self.root.after(100, self._procesar_eventos)

    def _actualizar_estado(self, mensaje):
        if isinstance(mensaje, dict) and mensaje.get("tipo") == "fuentes_conocimiento":
            resumen = str(mensaje.get("resumen", "")).strip()
            if resumen:
                self.estado_var.set(resumen)
            self._agregar_reflexion_fuentes(mensaje)
            return

        texto = str(mensaje)
        self.estado_var.set(texto)
        self._agregar_reflexion(texto)

    def _marcar_lista(self, gestor):
        self.gestor = gestor
        self.esta_lista = True
        self.esta_ocupada = False
        self.estado_var.set("Aurora lista. Escribe abajo para empezar.")
        self._agregar_mensaje_sistema("Aurora está lista.")
        self._agregar_reflexion("Aurora lista para conversar.")
        self._mostrar_sesion_anterior()
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()
        self.servidor_var.set("Servidor móvil: iniciando API local...")
        self._lanzar_hilo(self._inicializar_api_embebida, gestor)

    def _mostrar_api_lista(self, api_server):
        self.api_server = api_server
        self.servidor_var.set(f"Servidor móvil: {api_server.url_local}")
        self._agregar_mensaje_sistema(
            f"Servidor de red local activo. La app móvil puede conectarse en {api_server.url_local}"
        )
        self._agregar_reflexion(
            f"Servidor embebido iniciado en {api_server.url_local} para clientes móviles."
        )

    def _mostrar_error_api(self, error):
        self.servidor_var.set("Servidor móvil: no disponible")
        self._agregar_mensaje_sistema(
            f"No se pudo iniciar el servidor de red local: {error}"
        )
        self._agregar_reflexion(
            f"Fallo al iniciar la API embebida: {error}"
        )

    def _mostrar_sesion_anterior(self):
        sesion = self.gestor.sesion_anterior or []
        if not sesion:
            return

        self._agregar_mensaje_sistema(
            f"Sesión anterior recuperada: {len(sesion) // 2} turno(s)."
        )
        self._agregar_reflexion(
            f"Sesión anterior recuperada con {len(sesion) // 2} turno(s)."
        )
        for mensaje in sesion:
            if mensaje["role"] == "user":
                self._agregar_mensaje_chat("Tú", mensaje["content"], "speaker_user", "message_previous")
            else:
                self._agregar_mensaje_chat("Aurora", mensaje["content"], "speaker_assistant", "message_previous")

    def _iniciar_nueva_conversacion(self):
        if not self.esta_lista or not self.gestor:
            return
        if self.esta_ocupada:
            self.estado_var.set("Espera a que Aurora termine para iniciar una conversación nueva.")
            self._agregar_reflexion("No se inició nueva conversación porque Aurora estaba procesando.")
            return

        self.gestor.reiniciar_conversacion_actual()
        self.total_mensajes = 0

        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")

        self.reflexion_text.configure(state="normal")
        self.reflexion_text.delete("1.0", "end")
        self.reflexion_text.configure(state="disabled")
        self.ultimo_evento_reflexion = ""
        self.ultima_firma_fuentes_reflexion = None
        self.contador_fuentes_reflexion = 0
        self.bloques_fuentes_reflexion = {}

        self.entrada_text.configure(state="normal")
        self.entrada_text.delete("1.0", "end")
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()

        self.estado_var.set("Nueva conversación iniciada. Escribe para empezar.")
        self._agregar_reflexion("Nueva conversación iniciada. Historial previo descartado.")

    def _enviar_mensaje(self):
        if not self.esta_lista or self.esta_ocupada:
            return

        mensaje = self.entrada_text.get("1.0", "end").strip()
        if not mensaje:
            return

        self.entrada_text.delete("1.0", "end")
        self._agregar_mensaje_chat("Tú", mensaje, "speaker_user", "message_user")
        self.estado_var.set("Aurora está procesando el mensaje...")
        self._agregar_reflexion("Mensaje del usuario enviado. Aurora comienza a procesarlo.")
        self.esta_ocupada = True
        self._actualizar_estado_controles()
        self._lanzar_hilo(self._generar_respuesta, mensaje)

    def _mostrar_respuesta(self, respuesta):
        self._agregar_mensaje_chat("Aurora", respuesta, "speaker_assistant", "message_assistant")
        self.estado_var.set("Aurora lista. Puedes seguir escribiendo.")
        self._agregar_reflexion("Respuesta generada y añadida a la conversación.")
        self.esta_ocupada = False
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()

        if self.cierre_pendiente:
            self._cerrar_aplicacion()

    def _mostrar_error(self, error):
        self._agregar_mensaje_sistema(f"Error al generar la respuesta: {error}")
        self.estado_var.set("Se produjo un error al responder.")
        self._agregar_reflexion(f"Error durante la generación: {error}")
        self.esta_ocupada = False
        self._actualizar_estado_controles()

        if self.cierre_pendiente:
            self._cerrar_aplicacion()

    def _mostrar_error_inicializacion(self, error):
        self._agregar_mensaje_sistema(f"No se pudo iniciar Aurora: {error}")
        self.estado_var.set("Fallo al iniciar Aurora.")
        self._agregar_reflexion(f"Error de inicialización: {error}")
        self.esta_lista = False
        self.esta_ocupada = False
        self._actualizar_estado_controles()

    def _actualizar_estado_controles(self):
        entrada_habilitada = self.esta_lista and not self.esta_ocupada and not self.cierre_pendiente
        estado_entrada = "normal" if entrada_habilitada else "disabled"
        estado_boton = "normal" if entrada_habilitada else "disabled"
        estado_nueva = "normal" if entrada_habilitada else "disabled"
        color_texto = self.colores["text_primary"] if entrada_habilitada else self.colores["text_muted"]
        
        self.entrada_text.configure(state=estado_entrada, fg=color_texto)
        self.boton_enviar.configure(state=estado_boton)
        self.boton_nueva_conversacion.configure(state=estado_nueva)

        if self.cierre_pendiente:
            self.boton_enviar.configure(text="Cerrando...", state="disabled")
        elif self.esta_ocupada:
            self.boton_enviar.configure(text="Procesando...", state="disabled")
        elif self.esta_lista:
            self.boton_enviar.configure(text="Enviar", state="normal")
        else:
            self.boton_enviar.configure(text="Iniciando...", state="disabled")

    def _formatear_contenido_visual_chat(self, autor, contenido):
        if autor != "Aurora":
            return contenido

        texto = contenido.replace("\r\n", "\n").replace("\r", "\n")
        texto = re.sub(r"[ \t]+\n", "\n", texto)
        texto = re.sub(r"\n(?:[ \t]*\n)+", "\n\n", texto)
        return texto.strip("\n")

    def _agregar_mensaje_chat(self, autor, contenido, speaker_tag, message_tag):
        contenido_visible = self._formatear_contenido_visual_chat(autor, contenido)
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", f"{autor}\n", speaker_tag)
        self.chat_text.insert("end", f"{contenido_visible}\n\n", message_tag)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _agregar_mensaje_sistema(self, contenido):
        # Los eventos de sistema se siguen reflejando en el estado y en la pestaña
        # de reflexión, pero no se insertan en la conversación principal.
        return

    def _agregar_reflexion(self, contenido):
        texto = contenido.strip()
        if not texto or texto == self.ultimo_evento_reflexion:
            return

        self.ultimo_evento_reflexion = texto
        self.reflexion_text.configure(state="normal")
        self.reflexion_text.insert("end", "Aurora\n", "reflexion_titulo")
        self.reflexion_text.insert("end", f"{texto}\n\n", "reflexion_texto")
        self.reflexion_text.configure(state="disabled")
        self.reflexion_text.see("end")

    def _construir_texto_contexto_fuentes(self, fuentes):
        bloques = []
        for indice, fuente in enumerate(fuentes, start=1):
            origen = fuente.get("origen", "desconocido.txt")
            inicio = fuente.get("linea_inicio", 0)
            fin = fuente.get("linea_fin", inicio)
            inicio_ctx = fuente.get("linea_inicio_contexto", inicio)
            fin_ctx = fuente.get("linea_fin_contexto", fin)
            texto = str(fuente.get("texto", "")).strip()
            if inicio_ctx != inicio or fin_ctx != fin:
                encabezado = (
                    f"Fuente {indice}: {origen} "
                    f"(fragmento líneas {inicio}-{fin}, contexto {inicio_ctx}-{fin_ctx})"
                )
            else:
                encabezado = f"Fuente {indice}: {origen} (líneas {inicio}-{fin})"
            if texto:
                bloques.append(f"{encabezado}\n{texto}")
            else:
                bloques.append(encabezado)
        return "\n\n".join(bloques)

    def _agregar_reflexion_fuentes(self, evento_fuentes):
        resumen = str(evento_fuentes.get("resumen", "")).strip()
        fuentes = evento_fuentes.get("fuentes", [])
        if not resumen or not isinstance(fuentes, list) or not fuentes:
            if resumen:
                self._agregar_reflexion(resumen)
            return

        firma = (
            resumen,
            tuple(
                (
                    f.get("origen", "desconocido.txt"),
                    f.get("linea_inicio", 0),
                    f.get("linea_fin", 0),
                    str(f.get("texto", "")).strip(),
                )
                for f in fuentes
            ),
        )
        if firma == self.ultima_firma_fuentes_reflexion:
            return
        self.ultima_firma_fuentes_reflexion = firma

        self.contador_fuentes_reflexion += 1
        bloque_id = self.contador_fuentes_reflexion
        toggle_tag = f"fuentes_toggle_{bloque_id}"
        contexto_tag = f"fuentes_contexto_{bloque_id}"
        self.bloques_fuentes_reflexion[bloque_id] = {
            "toggle_tag": toggle_tag,
            "contexto_tag": contexto_tag,
            "fuentes": fuentes,
            "expandido": False,
        }

        etiqueta_toggle = f"▶ Mostrar contexto ({len(fuentes)} fragmento(s))\n\n"

        self.reflexion_text.configure(state="normal")
        self.reflexion_text.insert("end", "Aurora\n", "reflexion_titulo")
        self.reflexion_text.insert("end", f"{resumen}\n", "reflexion_texto")
        inicio_toggle = self.reflexion_text.index("end")
        self.reflexion_text.insert("end", etiqueta_toggle, ("reflexion_toggle", toggle_tag))
        fin_toggle = self.reflexion_text.index("end")
        self.reflexion_text.tag_add(toggle_tag, inicio_toggle, fin_toggle)
        self.reflexion_text.tag_bind(
            toggle_tag,
            "<Button-1>",
            lambda _event, bid=bloque_id: self._toggle_contexto_fuentes_reflexion(bid),
        )
        self.reflexion_text.configure(state="disabled")
        self.reflexion_text.see("end")

    def _toggle_contexto_fuentes_reflexion(self, bloque_id):
        bloque = self.bloques_fuentes_reflexion.get(bloque_id)
        if not bloque:
            return "break"

        toggle_tag = bloque["toggle_tag"]
        contexto_tag = bloque["contexto_tag"]
        rango_toggle = self.reflexion_text.tag_nextrange(toggle_tag, "1.0", "end")
        if not rango_toggle:
            return "break"

        inicio_toggle, fin_toggle = rango_toggle
        fuentes = bloque["fuentes"]

        self.reflexion_text.configure(state="normal")

        if bloque["expandido"]:
            rangos_contexto = list(self.reflexion_text.tag_ranges(contexto_tag))
            for idx in range(len(rangos_contexto) - 2, -1, -2):
                self.reflexion_text.delete(rangos_contexto[idx], rangos_contexto[idx + 1])
            self.reflexion_text.delete(inicio_toggle, fin_toggle)
            texto_toggle = f"▶ Mostrar contexto ({len(fuentes)} fragmento(s))\n\n"
            self.reflexion_text.insert(inicio_toggle, texto_toggle, ("reflexion_toggle", toggle_tag))
            bloque["expandido"] = False
        else:
            self.reflexion_text.delete(inicio_toggle, fin_toggle)
            texto_toggle = f"▼ Ocultar contexto ({len(fuentes)} fragmento(s))\n"
            self.reflexion_text.insert(inicio_toggle, texto_toggle, ("reflexion_toggle", toggle_tag))
            nuevo_rango = self.reflexion_text.tag_nextrange(toggle_tag, inicio_toggle, "end")
            insercion_contexto = nuevo_rango[1] if nuevo_rango else inicio_toggle
            contexto = self._construir_texto_contexto_fuentes(fuentes)
            self.reflexion_text.insert(
                insercion_contexto,
                f"{contexto}\n\n",
                ("reflexion_contexto", contexto_tag),
            )
            bloque["expandido"] = True

        self.reflexion_text.configure(state="disabled")
        self.reflexion_text.see(inicio_toggle)
        return "break"

    def _solicitar_cierre(self):
        if self.cierre_pendiente:
            return

        self.cierre_pendiente = True
        self._actualizar_estado_controles()

        if self.esta_ocupada:
            self.estado_var.set("Esperando a que termine la operación actual para cerrar...")
            self._agregar_reflexion("Cierre solicitado. Aurora esperará a terminar antes de cerrar.")
            self._agregar_mensaje_sistema(
                "Cierre solicitado. Aurora cerrará al terminar la operación actual."
            )
            return

        self._cerrar_aplicacion()

    def _cerrar_aplicacion(self):
        if self.api_server:
            try:
                self.api_server.stop()
            except Exception as exc:
                self._agregar_reflexion(f"Fallo al detener el servidor embebido: {exc}")

        self.root.destroy()
