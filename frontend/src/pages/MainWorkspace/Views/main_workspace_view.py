import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class MainWorkspaceViewMixin:
    def _construir_interfaz(self):
        contenedor = tk.Frame(
            self.root,
            bg=self.colores["app_bg"],
            padx=0,
            pady=0,
        )
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        self.estado_var = tk.StringVar(value="Preparando Aurora...")
        self.servidor_var = tk.StringVar(value="Servidor local: iniciando...")
        self.presencia_var = tk.StringVar(value="conectando...")

        self.workspace = tk.Frame(
            contenedor,
            bg=self.colores["panel"],
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
        self.header = tk.Frame(self.workspace, bg=self.colores["panel_alt"])
        header = self.header
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        self.top_bar = tk.Frame(
            header,
            bg=self.colores["panel_alt"],
            padx=14,
            pady=10,
        )
        top_bar = self.top_bar
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.columnconfigure(1, weight=1)

        self.label_back = tk.Label(
            top_bar,
            text="←",
            bg=self.colores["panel_alt"],
            fg=self.colores["header_text"],
            font=("Helvetica", 16, "bold"),
        )
        self.label_back.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.info_contacto = tk.Frame(top_bar, bg=self.colores["panel_alt"])
        info_contacto = self.info_contacto
        info_contacto.grid(row=0, column=1, sticky="w")

        self.avatar = tk.Canvas(
            info_contacto,
            width=38,
            height=38,
            bg=self.colores["panel_alt"],
            highlightthickness=0,
        )
        self.avatar.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 10))
        self._repintar_avatar()

        self.label_nombre = tk.Label(
            info_contacto,
            text="Aurora",
            bg=self.colores["panel_alt"],
            fg=self.colores["header_text"],
            font=self.fuentes["hero"],
        )
        self.label_nombre.grid(row=0, column=1, sticky="w")

        self.label_presencia = tk.Label(
            info_contacto,
            textvariable=self.presencia_var,
            bg=self.colores["panel_alt"],
            fg=self.colores["header_muted"],
            font=self.fuentes["caption"],
        )
        self.label_presencia.grid(row=1, column=1, sticky="w")

        self.actions_bar = tk.Frame(
            header,
            bg=self.colores["panel_soft"],
            padx=10,
            pady=7,
        )
        actions_bar = self.actions_bar
        actions_bar.grid(row=1, column=0, sticky="ew")
        actions_bar.columnconfigure(6, weight=1)

        self.boton_tab_chat = self._crear_boton_ui(
            actions_bar,
            text="Conversación",
            command=lambda: self._mostrar_vista("chat"),
            estilo="tab",
            padx=16,
            pady=8,
        )
        self.boton_tab_chat.grid(row=0, column=0, sticky="w")

        self.boton_tab_reflexion = self._crear_boton_ui(
            actions_bar,
            text="Reflexión",
            command=lambda: self._mostrar_vista("reflexion"),
            estilo="tab",
            padx=16,
            pady=8,
        )
        self.boton_tab_reflexion.grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.boton_tab_contexto = self._crear_boton_ui(
            actions_bar,
            text="Contexto",
            command=lambda: self._mostrar_vista("contexto"),
            estilo="tab",
            padx=16,
            pady=8,
        )
        self.boton_tab_contexto.grid(row=0, column=2, sticky="w", padx=(6, 0))

        self.boton_tab_estadisticas = self._crear_boton_ui(
            actions_bar,
            text="Estadísticas",
            command=lambda: self._mostrar_vista("estadisticas"),
            estilo="tab",
            padx=16,
            pady=8,
        )
        self.boton_tab_estadisticas.grid(row=0, column=3, sticky="w", padx=(6, 0))

        self.boton_nueva_conversacion = self._crear_boton_ui(
            actions_bar,
            text="Nueva conversación",
            command=self._iniciar_nueva_conversacion,
            estilo="primary",
            padx=18,
            pady=8,
        )
        self.boton_nueva_conversacion.grid(row=0, column=4, sticky="w", padx=(12, 0))
        self._establecer_estado_boton_ui(self.boton_nueva_conversacion, "disabled")

        self.boton_ajustes = self._crear_boton_ui(
            actions_bar,
            text="⚙ Ajustes",
            command=self._abrir_ajustes,
            estilo="utility",
            padx=16,
            pady=8,
        )
        self.boton_ajustes.grid(row=0, column=5, sticky="w", padx=(12, 0))

        self.info_servidor = tk.Label(
            actions_bar,
            textvariable=self.servidor_var,
            bg=self.colores["panel_soft"],
            fg=self.colores["header_muted"],
            font=self.fuentes["caption"],
            justify="right",
        )
        self.info_servidor.grid(row=0, column=6, sticky="e")

        self.contenido = tk.Frame(self.workspace, bg=self.colores["panel_alt"])
        contenido = self.contenido
        contenido.grid(row=1, column=0, sticky="nsew")
        contenido.columnconfigure(0, weight=1)
        contenido.rowconfigure(0, weight=1)

        self.chat_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=0,
            pady=0,
        )
        self.chat_tab.columnconfigure(0, weight=1)
        self.chat_tab.rowconfigure(0, weight=1)
        self.chat_tab.rowconfigure(1, weight=0)
        self.chat_tab.grid(row=0, column=0, sticky="nsew")

        self.reflexion_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=20,
            pady=18,
        )
        self.reflexion_tab.columnconfigure(0, weight=1)
        self.reflexion_tab.rowconfigure(1, weight=1)
        self.reflexion_tab.grid(row=0, column=0, sticky="nsew")

        self.contexto_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=20,
            pady=18,
        )
        self.contexto_tab.columnconfigure(0, weight=1)
        self.contexto_tab.rowconfigure(1, weight=1)
        self.contexto_tab.grid(row=0, column=0, sticky="nsew")

        self.estadisticas_tab = tk.Frame(
            contenido,
            bg=self.colores["panel"],
            padx=0,
            pady=0,
        )
        self.estadisticas_tab.columnconfigure(0, weight=1)
        self.estadisticas_tab.rowconfigure(0, weight=1)
        self.estadisticas_tab.grid(row=0, column=0, sticky="nsew")
        self._construir_estadisticas_tab()

        self.chat_text = ScrolledText(
            self.chat_tab,
            wrap="word",
            height=18,
            font=self.fuentes["body_chat"],
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=12,
            insertbackground=self.colores["text_primary"],
            highlightthickness=0,
            spacing1=0,
            spacing2=0,
            spacing3=0,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_text.configure(state="disabled")
        self.chat_text.bind("<Configure>", self._al_redimensionar_chat)
        self._configurar_tags_chat()

        self.composer = tk.Frame(
            self.chat_tab,
            bg=self.colores["panel"],
            padx=10,
            pady=10,
        )
        composer = self.composer
        composer.grid(row=1, column=0, sticky="ew")
        composer.columnconfigure(0, weight=1)
        composer.columnconfigure(1, weight=0)

        self.cuerpo_composer = tk.Frame(
            composer,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#d9dee3",
            highlightcolor="#d9dee3",
            bd=0,
        )
        cuerpo_composer = self.cuerpo_composer
        cuerpo_composer.grid(row=0, column=0, sticky="ew")
        cuerpo_composer.rowconfigure(0, weight=1)
        cuerpo_composer.columnconfigure(0, weight=1)
        cuerpo_composer.grid_propagate(False)
        cuerpo_composer.configure(height=54)

        self.entrada_text = tk.Text(
            cuerpo_composer,
            height=1,
            wrap="word",
            font=self.fuentes["body_large"],
            bg="#ffffff",
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=10,
            insertbackground=self.colores["text_primary"],
            highlightthickness=0,
        )
        self.entrada_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.entrada_text.configure(state="disabled")

        self.boton_enviar = self._crear_boton_ui(
            composer,
            text="➤",
            command=self._enviar_mensaje,
            estilo="send",
            padx=16,
            pady=10,
            font=("Helvetica", 14, "bold"),
        )
        self.boton_enviar.grid(row=0, column=1, sticky="e", padx=(10, 0))
        self._establecer_estado_boton_ui(self.boton_enviar, "disabled")

        self.label_reflexion = tk.Label(
            self.reflexion_tab,
            text="Reflexión de Aurora",
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            font=self.fuentes["section"],
        )
        self.label_reflexion.grid(row=0, column=0, sticky="w")

        self.reflexion_text = ScrolledText(
            self.reflexion_tab,
            wrap="word",
            font=self.fuentes["body"],
            bg="#ffffff",
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=16,
            insertbackground=self.colores["text_primary"],
            highlightthickness=1,
            highlightbackground="#d8d5cf",
            highlightcolor="#d8d5cf",
        )
        self.reflexion_text.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.reflexion_text.configure(state="disabled")
        self.reflexion_text.tag_configure(
            "reflexion_titulo",
            foreground=self.colores["panel_alt"],
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
            foreground=self.colores["panel_alt"],
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

        self.label_contexto = tk.Label(
            self.contexto_tab,
            text="Contexto real enviado al modelo",
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            font=self.fuentes["section"],
        )
        self.label_contexto.grid(row=0, column=0, sticky="w")

        self.contexto_text = ScrolledText(
            self.contexto_tab,
            wrap="word",
            font=("Courier", 12),
            bg="#ffffff",
            fg=self.colores["text_primary"],
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=16,
            insertbackground=self.colores["text_primary"],
            highlightthickness=1,
            highlightbackground="#d8d5cf",
            highlightcolor="#d8d5cf",
        )
        self.contexto_text.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.contexto_text.configure(state="disabled")
        self.contexto_text.tag_configure(
            "contexto_titulo",
            foreground=self.colores["panel_alt"],
            font=("Courier", 12, "bold"),
            spacing1=8,
        )
        self.contexto_text.tag_configure(
            "contexto_meta",
            foreground=self.colores["text_muted"],
            font=("Courier", 12),
            spacing3=8,
        )
        self.contexto_text.tag_configure(
            "contexto_bloque",
            foreground=self.colores["text_primary"],
            font=("Courier", 12),
            spacing3=18,
        )
        self._insertar_placeholder_contexto()
        self._mostrar_vista("chat")
        self._aplicar_tema_actual()

    def _mostrar_vista(self, vista):
        self.vista_activa = vista
        todos_los_botones = {
            "chat": self.boton_tab_chat,
            "reflexion": self.boton_tab_reflexion,
            "contexto": self.boton_tab_contexto,
            "estadisticas": self.boton_tab_estadisticas,
        }
        todas_las_tabs = {
            "chat": self.chat_tab,
            "reflexion": self.reflexion_tab,
            "contexto": self.contexto_tab,
            "estadisticas": self.estadisticas_tab,
        }
        tab = todas_las_tabs.get(vista)
        if tab:
            tab.tkraise()
        for nombre, boton in todos_los_botones.items():
            self._pintar_boton_vista(boton, activo=(nombre == vista))
        if vista == "estadisticas":
            self._actualizar_estadisticas_ui()

    def _pintar_boton_vista(self, boton, activo):
        self._establecer_seleccion_boton_ui(boton, activo)

    def _repintar_avatar(self):
        if not hasattr(self, "avatar"):
            return
        self.avatar.configure(bg=self.colores["panel_alt"])
        self.avatar.delete("all")
        self.avatar.create_oval(
            2, 2, 36, 36,
            fill=self.colores["avatar_bg"],
            outline=self.colores["avatar_bg"],
        )
        self.avatar.create_text(
            19, 19,
            text="A",
            fill=self.colores["avatar_fg"],
            font=("Helvetica", 14, "bold"),
        )

    def _aplicar_tema_actual(self):
        self._configurar_tags_chat()
        self.root.configure(bg=self.colores["app_bg"])
        self.workspace.configure(bg=self.colores["panel"])
        self.header.configure(bg=self.colores["panel_alt"])
        self.top_bar.configure(bg=self.colores["panel_alt"])
        self.info_contacto.configure(bg=self.colores["panel_alt"])
        self.label_back.configure(bg=self.colores["panel_alt"], fg=self.colores["header_text"])
        self.label_nombre.configure(bg=self.colores["panel_alt"], fg=self.colores["header_text"])
        self.label_presencia.configure(bg=self.colores["panel_alt"], fg=self.colores["header_muted"])
        self._repintar_avatar()

        self.actions_bar.configure(bg=self.colores["panel_soft"])
        self.info_servidor.configure(bg=self.colores["panel_soft"], fg=self.colores["header_muted"])
        self._pintar_boton_vista(self.boton_tab_chat, self.vista_activa == "chat")
        self._pintar_boton_vista(self.boton_tab_reflexion, self.vista_activa == "reflexion")
        self._pintar_boton_vista(self.boton_tab_contexto, self.vista_activa == "contexto")
        self._pintar_boton_vista(self.boton_tab_estadisticas, self.vista_activa == "estadisticas")
        self._aplicar_estilo_boton_ui(self.boton_ajustes)

        self.contenido.configure(bg=self.colores["panel_alt"])
        self.chat_tab.configure(bg=self.colores["panel"])
        self.reflexion_tab.configure(bg=self.colores["panel"])
        self.contexto_tab.configure(bg=self.colores["panel"])
        self.estadisticas_tab.configure(bg=self.colores["panel"])
        self._aplicar_tema_estadisticas()

        self.chat_text.configure(
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            insertbackground=self.colores["text_primary"],
        )
        self.composer.configure(bg=self.colores["panel"])
        self.cuerpo_composer.configure(
            bg=self.colores["field_bg"],
            highlightbackground=self.colores["field_border"],
            highlightcolor=self.colores["field_border"],
        )
        self.entrada_text.configure(
            bg=self.colores["field_bg"],
            fg=self.colores["text_primary"],
            insertbackground=self.colores["text_primary"],
        )
        self._aplicar_estilo_boton_ui(self.boton_enviar)

        self.label_reflexion.configure(bg=self.colores["panel"], fg=self.colores["text_primary"])
        self.reflexion_text.configure(
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            insertbackground=self.colores["text_primary"],
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
        )
        self.reflexion_text.tag_configure("reflexion_titulo", foreground=self.colores["accent"])
        self.reflexion_text.tag_configure("reflexion_texto", foreground=self.colores["text_primary"])
        self.reflexion_text.tag_configure("reflexion_toggle", foreground=self.colores["accent"])
        self.reflexion_text.tag_configure("reflexion_contexto", foreground=self.colores["text_secondary"])

        self.label_contexto.configure(bg=self.colores["panel"], fg=self.colores["text_primary"])
        self.contexto_text.configure(
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            insertbackground=self.colores["text_primary"],
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
        )
        self.contexto_text.tag_configure("contexto_titulo", foreground=self.colores["accent"])
        self.contexto_text.tag_configure("contexto_meta", foreground=self.colores["text_muted"])
        self.contexto_text.tag_configure("contexto_bloque", foreground=self.colores["text_primary"])

        self._actualizar_estado_controles()
        self._reconstruir_chat_visual()
        if self.ventana_ajustes and self.ventana_ajustes.winfo_exists():
            self._aplicar_tema_ventana_ajustes()

