import tkinter as tk


class AjustesViewMixin:
    def _abrir_ajustes(self):
        if self.ventana_ajustes and self.ventana_ajustes.winfo_exists():
            self.ventana_ajustes.lift()
            self.ventana_ajustes.focus_force()
            return

        config_modelo = self._cargar_configuracion_modelo()
        self.vars_ajustes_modelo = {}
        self.widgets_ajustes = {
            "frames": [],
            "cards": [],
            "titles": [],
            "descriptions": [],
            "entries": [],
            "checkboxes": [],
            "notes": [],
        }

        self.ventana_ajustes = tk.Toplevel(self.root)
        self.ventana_ajustes.title("Ajustes")
        self.ventana_ajustes.transient(self.root)
        self.ventana_ajustes.resizable(True, True)
        self.ventana_ajustes.geometry("760x820")
        self.ventana_ajustes.minsize(680, 620)
        self.ventana_ajustes.protocol("WM_DELETE_WINDOW", self._cerrar_ajustes)

        self.panel_ajustes = tk.Frame(self.ventana_ajustes)
        self.panel_ajustes.pack(fill="both", expand=True)

        self.canvas_ajustes = tk.Canvas(self.panel_ajustes, bd=0, highlightthickness=0)
        self.scroll_ajustes = tk.Scrollbar(
            self.panel_ajustes,
            orient="vertical",
            command=self.canvas_ajustes.yview,
        )
        self.canvas_ajustes.configure(yscrollcommand=self.scroll_ajustes.set)
        self.scroll_ajustes.pack(side="right", fill="y")
        self.canvas_ajustes.pack(side="left", fill="both", expand=True)

        self.contenido_ajustes = tk.Frame(self.canvas_ajustes, padx=20, pady=20)
        self._ventana_interior_ajustes = self.canvas_ajustes.create_window(
            (0, 0),
            window=self.contenido_ajustes,
            anchor="nw",
        )
        self.contenido_ajustes.bind("<Configure>", self._actualizar_scrollregion_ajustes)
        self.canvas_ajustes.bind("<Configure>", self._ajustar_ancho_contenido_ajustes)
        for widget in (self.canvas_ajustes, self.contenido_ajustes):
            widget.bind("<MouseWheel>", self._desplazar_canvas_ajustes)
            widget.bind("<Button-4>", self._desplazar_canvas_ajustes)
            widget.bind("<Button-5>", self._desplazar_canvas_ajustes)

        self.label_ajustes = tk.Label(
            self.contenido_ajustes,
            text="Ajustes de interfaz y modelo",
            font=self.fuentes["section"],
            anchor="w",
        )
        self.label_ajustes.pack(fill="x")

        self.descripcion_ajustes = tk.Label(
            self.contenido_ajustes,
            text=(
                "Desde aquí puedes ajustar apariencia, muestreo de respuesta, "
                "parámetros del pensamiento interno y opciones de carga del modelo."
            ),
            font=self.fuentes["body"],
            anchor="w",
            justify="left",
            wraplength=660,
            pady=12,
        )
        self.descripcion_ajustes.pack(fill="x")

        self.nota_ajustes = tk.Label(
            self.contenido_ajustes,
            text=(
                "Los cambios en respuesta y pensamiento se aplican al guardar. "
                "Los cambios de inicialización y KV cache recargan el modelo local."
            ),
            font=self.fuentes["caption"],
            anchor="w",
            justify="left",
            wraplength=660,
            pady=2,
        )
        self.nota_ajustes.pack(fill="x", pady=(0, 14))
        self.widgets_ajustes["notes"].append(self.nota_ajustes)

        panel_apariencia = self._crear_tarjeta_ajustes(
            self.contenido_ajustes,
            "Apariencia",
            "Opciones visuales de la interfaz del chat.",
        )
        self.var_modo_oscuro = tk.BooleanVar(value=self.modo_oscuro)
        self.check_modo_oscuro = tk.Checkbutton(
            panel_apariencia,
            text="Modo oscuro",
            variable=self.var_modo_oscuro,
            command=self._alternar_modo_oscuro_desde_ui,
            anchor="w",
            padx=0,
            pady=6,
        )
        self.check_modo_oscuro.pack(fill="x")
        self.widgets_ajustes["checkboxes"].append(self.check_modo_oscuro)

        for definicion in DEFINICIONES_AJUSTES_MODELO:
            panel_seccion = self._crear_tarjeta_ajustes(
                self.contenido_ajustes,
                definicion["titulo"],
                definicion["descripcion"],
            )
            seccion = definicion["seccion"]
            for campo in definicion["campos"]:
                valor = config_modelo.get(seccion, {}).get(campo["clave"])
                self._crear_campo_ajuste_modelo(panel_seccion, seccion, campo, valor)

        self.footer_ajustes = tk.Frame(self.ventana_ajustes, padx=20, pady=14)
        self.footer_ajustes.pack(fill="x")

        self.boton_guardar_ajustes = self._crear_boton_ui(
            self.footer_ajustes,
            text="Guardar ajustes",
            command=self._guardar_ajustes_modelo,
            estilo="primary",
            padx=16,
            pady=8,
        )
        self.boton_guardar_ajustes.pack(side="right")
        self.boton_cerrar_ajustes = self._crear_boton_ui(
            self.footer_ajustes,
            text="Cerrar",
            command=self._cerrar_ajustes,
            estilo="utility",
            padx=16,
            pady=8,
        )
        self.boton_cerrar_ajustes.pack(side="right", padx=(0, 10))

        self._aplicar_tema_ventana_ajustes()

    def _crear_tarjeta_ajustes(self, parent, titulo, descripcion):
        tarjeta = tk.Frame(parent, padx=16, pady=16, bd=1, relief="solid")
        tarjeta.pack(fill="x", pady=(0, 14))
        self.widgets_ajustes["frames"].append(tarjeta)
        self.widgets_ajustes["cards"].append(tarjeta)

        titulo_label = tk.Label(
            tarjeta,
            text=titulo,
            font=self.fuentes["card_title"],
            anchor="w",
        )
        titulo_label.pack(fill="x")
        self.widgets_ajustes["titles"].append(titulo_label)

        descripcion_label = tk.Label(
            tarjeta,
            text=descripcion,
            font=self.fuentes["caption"],
            anchor="w",
            justify="left",
            wraplength=620,
            pady=2,
        )
        descripcion_label.pack(fill="x", pady=(4, 10))
        self.widgets_ajustes["descriptions"].append(descripcion_label)

        cuerpo = tk.Frame(tarjeta)
        cuerpo.pack(fill="x")
        self.widgets_ajustes["frames"].append(cuerpo)
        return cuerpo

    def _crear_campo_ajuste_modelo(self, parent, seccion, campo, valor):
        contenedor = tk.Frame(parent)
        contenedor.pack(fill="x", pady=(0, 10))
        self.widgets_ajustes["frames"].append(contenedor)

        bloque_texto = tk.Frame(contenedor)
        bloque_texto.pack(side="left", fill="x", expand=True)
        self.widgets_ajustes["frames"].append(bloque_texto)

        etiqueta = tk.Label(
            bloque_texto,
            text=campo["etiqueta"],
            font=self.fuentes["label"],
            anchor="w",
        )
        etiqueta.pack(fill="x")
        self.widgets_ajustes["titles"].append(etiqueta)

        ayuda = tk.Label(
            bloque_texto,
            text=campo["ayuda"],
            font=self.fuentes["caption"],
            anchor="w",
            justify="left",
            wraplength=470,
        )
        ayuda.pack(fill="x", pady=(2, 0))
        self.widgets_ajustes["descriptions"].append(ayuda)

        variable = tk.StringVar(value=self._formatear_valor_ajuste(valor, campo["tipo"]))
        self.vars_ajustes_modelo[(seccion, campo["clave"])] = variable
        entrada = tk.Entry(
            contenedor,
            textvariable=variable,
            width=14,
            justify="right",
            bd=1,
            relief="solid",
            font=self.fuentes["body"],
        )
        entrada.pack(side="right", padx=(16, 0), ipady=4)
        self.widgets_ajustes["entries"].append(entrada)

    def _actualizar_scrollregion_ajustes(self, _event=None):
        if not self.ventana_ajustes or not self.ventana_ajustes.winfo_exists():
            return
        self.canvas_ajustes.configure(scrollregion=self.canvas_ajustes.bbox("all"))

    def _ajustar_ancho_contenido_ajustes(self, event):
        if not self.ventana_ajustes or not self.ventana_ajustes.winfo_exists():
            return
        self.canvas_ajustes.itemconfigure(self._ventana_interior_ajustes, width=event.width)

    def _desplazar_canvas_ajustes(self, event):
        if not self.ventana_ajustes or not self.ventana_ajustes.winfo_exists():
            return "break"

        delta = getattr(event, "delta", 0)
        num = getattr(event, "num", None)
        if delta:
            pasos = -1 * int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            self.canvas_ajustes.yview_scroll(pasos, "units")
        elif num == 4:
            self.canvas_ajustes.yview_scroll(-1, "units")
        elif num == 5:
            self.canvas_ajustes.yview_scroll(1, "units")
        return "break"

