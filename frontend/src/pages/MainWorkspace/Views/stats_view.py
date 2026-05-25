import tkinter as tk


class StatsViewMixin:
    def _construir_estadisticas_tab(self):
        """Construye el contenido completo de la pestaña de estadísticas."""
        self._stats_canvas = tk.Canvas(
            self.estadisticas_tab,
            bg=self.colores["panel"],
            highlightthickness=0,
            bd=0,
        )
        self._stats_scroll = tk.Scrollbar(
            self.estadisticas_tab,
            orient="vertical",
            command=self._stats_canvas.yview,
        )
        self._stats_canvas.configure(yscrollcommand=self._stats_scroll.set)
        self._stats_scroll.pack(side="right", fill="y")
        self._stats_canvas.pack(side="left", fill="both", expand=True)

        self._stats_contenido = tk.Frame(
            self._stats_canvas,
            bg=self.colores["panel"],
            padx=24,
            pady=20,
        )
        self._stats_ventana = self._stats_canvas.create_window(
            (0, 0), window=self._stats_contenido, anchor="nw",
        )
        self._stats_contenido.bind(
            "<Configure>",
            lambda _e: self._stats_canvas.configure(scrollregion=self._stats_canvas.bbox("all")),
        )
        self._stats_canvas.bind(
            "<Configure>",
            lambda e: self._stats_canvas.itemconfigure(self._stats_ventana, width=e.width),
        )
        for w in (self._stats_canvas, self._stats_contenido):
            w.bind("<MouseWheel>", self._scroll_estadisticas)
            w.bind("<Button-4>", self._scroll_estadisticas)
            w.bind("<Button-5>", self._scroll_estadisticas)

        # ── Header ──
        self._stats_titulo = tk.Label(
            self._stats_contenido,
            text="📊  Estadísticas de Progreso",
            bg=self.colores["panel"],
            fg=self.colores["text_primary"],
            font=self.fuentes["section"],
            anchor="w",
        )
        self._stats_titulo.pack(fill="x", pady=(0, 4))

        self._stats_subtitulo = tk.Label(
            self._stats_contenido,
            text="Sigue tu mejora conversacional con Aurora",
            bg=self.colores["panel"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption"],
            anchor="w",
        )
        self._stats_subtitulo.pack(fill="x", pady=(0, 18))

        # ── Tarjetas resumen (fila superior) ──
        fila_tarjetas = tk.Frame(self._stats_contenido, bg=self.colores["panel"])
        fila_tarjetas.pack(fill="x", pady=(0, 16))
        fila_tarjetas.columnconfigure((0, 1, 2, 3), weight=1, uniform="card")
        self._widgets_estadisticas["fila_tarjetas"] = fila_tarjetas

        self._crear_tarjeta_stat(fila_tarjetas, "mensajes_totales", "📨", "Mensajes totales", "0", self.colores["accent"], 0)
        self._crear_tarjeta_stat(fila_tarjetas, "record_5min", "🏆", "Récord 5 min", "0", self.colores["warning"], 1)
        self._crear_tarjeta_stat(fila_tarjetas, "racha_dias", "🔥", "Racha de días", "0", self.colores["danger"], 2)
        self._crear_tarjeta_stat(fila_tarjetas, "total_conversaciones", "💬", "Conversaciones", "0", self.colores["success"], 3)

        # ── Ronda activa (contador 5 min en vivo) ──
        self._construir_indicador_ronda()

        # ── Barra de nivel ──
        self._construir_barra_nivel()

        # ── Gráfica de progreso ──
        self._construir_grafica_progreso()

        # ── Tarjetas adicionales ──
        fila_extra = tk.Frame(self._stats_contenido, bg=self.colores["panel"])
        fila_extra.pack(fill="x", pady=(0, 8))
        fila_extra.columnconfigure((0, 1, 2), weight=1, uniform="card2")
        self._widgets_estadisticas["fila_extra"] = fila_extra

        self._crear_tarjeta_stat(fila_extra, "mensaje_mas_largo", "📝", "Mensaje más largo", "0 chars", self.colores["warning"], 0)
        self._crear_tarjeta_stat(fila_extra, "promedio_msgs", "📈", "Promedio msg/conv", "0.0", self.colores["accent"], 1)
        self._crear_tarjeta_stat(fila_extra, "dias_activos", "📅", "Días activos", "0", self.colores["success"], 2)

    def _crear_tarjeta_stat(self, parent, key, emoji, titulo, valor_inicial, color_acento, columna):
        """Crea una tarjeta de estadística individual."""
        tarjeta = tk.Frame(
            parent,
            bg=self.colores["surface_white"],
            highlightthickness=1,
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
            padx=14,
            pady=14,
        )
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=6, pady=4)

        barra = tk.Frame(tarjeta, bg=color_acento, height=3)
        barra.pack(fill="x", pady=(0, 8))

        emoji_label = tk.Label(
            tarjeta, text=emoji,
            bg=self.colores["surface_white"],
            font=("Helvetica", 22), anchor="w",
        )
        emoji_label.pack(anchor="w")

        valor_label = tk.Label(
            tarjeta, text=valor_inicial,
            bg=self.colores["surface_white"],
            fg=color_acento,
            font=("Helvetica", 26, "bold"), anchor="w",
        )
        valor_label.pack(anchor="w", pady=(4, 2))

        titulo_label = tk.Label(
            tarjeta, text=titulo,
            bg=self.colores["surface_white"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption"], anchor="w",
        )
        titulo_label.pack(anchor="w")

        self._widgets_estadisticas[key] = {
            "tarjeta": tarjeta, "emoji": emoji_label, "valor": valor_label,
            "titulo": titulo_label, "barra": barra, "color_acento": color_acento,
        }
        for w in (tarjeta, emoji_label, valor_label, titulo_label, barra):
            w.bind("<MouseWheel>", self._scroll_estadisticas)
            w.bind("<Button-4>", self._scroll_estadisticas)
            w.bind("<Button-5>", self._scroll_estadisticas)

    def _construir_indicador_ronda(self):
        """Construye el indicador de ronda de 5 minutos en vivo."""
        marco = tk.Frame(
            self._stats_contenido,
            bg=self.colores["surface_white"],
            highlightthickness=1,
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
            padx=18, pady=14,
        )
        marco.pack(fill="x", pady=(0, 16))

        cabecera = tk.Frame(marco, bg=self.colores["surface_white"])
        cabecera.pack(fill="x")

        titulo = tk.Label(
            cabecera, text="⏱  Ronda de 5 minutos",
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            font=self.fuentes["card_title"], anchor="w",
        )
        titulo.pack(side="left")

        estado_label = tk.Label(
            cabecera, text="Inactivo",
            bg=self.colores["surface_white"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption_bold"], anchor="e",
        )
        estado_label.pack(side="right")

        info_frame = tk.Frame(marco, bg=self.colores["surface_white"])
        info_frame.pack(fill="x", pady=(8, 4))

        msgs_label = tk.Label(
            info_frame, text="Mensajes: 0",
            bg=self.colores["surface_white"],
            fg=self.colores["text_secondary"],
            font=self.fuentes["body"], anchor="w",
        )
        msgs_label.pack(side="left")

        tiempo_label = tk.Label(
            info_frame, text="Tiempo: --:--",
            bg=self.colores["surface_white"],
            fg=self.colores["text_secondary"],
            font=self.fuentes["body"], anchor="e",
        )
        tiempo_label.pack(side="right")

        barra_canvas = tk.Canvas(
            marco, height=8,
            bg=self.colores["surface_line"],
            highlightthickness=0, bd=0,
        )
        barra_canvas.pack(fill="x", pady=(4, 0))

        self._widgets_estadisticas["ronda"] = {
            "marco": marco, "cabecera": cabecera, "titulo": titulo,
            "estado": estado_label, "info_frame": info_frame,
            "msgs": msgs_label, "tiempo": tiempo_label,
            "barra_canvas": barra_canvas,
        }
        for w in (marco, cabecera, titulo, estado_label, info_frame, msgs_label, tiempo_label, barra_canvas):
            w.bind("<MouseWheel>", self._scroll_estadisticas)
            w.bind("<Button-4>", self._scroll_estadisticas)
            w.bind("<Button-5>", self._scroll_estadisticas)

    def _construir_barra_nivel(self):
        """Construye la barra de nivel de comunicador."""
        marco = tk.Frame(
            self._stats_contenido,
            bg=self.colores["surface_white"],
            highlightthickness=1,
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
            padx=18, pady=14,
        )
        marco.pack(fill="x", pady=(0, 16))

        fila_titulo = tk.Frame(marco, bg=self.colores["surface_white"])
        fila_titulo.pack(fill="x")

        nivel_nombre = tk.Label(
            fila_titulo, text="🌱  Principiante",
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            font=self.fuentes["card_title"], anchor="w",
        )
        nivel_nombre.pack(side="left")

        nivel_info = tk.Label(
            fila_titulo, text="0 / 50 mensajes",
            bg=self.colores["surface_white"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption"], anchor="e",
        )
        nivel_info.pack(side="right")

        desc = tk.Label(
            marco, text="Envía más mensajes para subir de nivel",
            bg=self.colores["surface_white"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption"], anchor="w", pady=4,
        )
        desc.pack(fill="x")

        barra_canvas = tk.Canvas(
            marco, height=18,
            bg=self.colores["surface_line"],
            highlightthickness=0, bd=0,
        )
        barra_canvas.pack(fill="x", pady=(6, 0))

        self._widgets_estadisticas["nivel"] = {
            "marco": marco, "fila_titulo": fila_titulo,
            "nombre": nivel_nombre, "info": nivel_info,
            "desc": desc, "barra_canvas": barra_canvas,
        }
        for w in (marco, fila_titulo, nivel_nombre, nivel_info, desc, barra_canvas):
            w.bind("<MouseWheel>", self._scroll_estadisticas)
            w.bind("<Button-4>", self._scroll_estadisticas)
            w.bind("<Button-5>", self._scroll_estadisticas)

    def _construir_grafica_progreso(self):
        """Construye el canvas de la gráfica de puntajes de 5 minutos."""
        marco = tk.Frame(
            self._stats_contenido,
            bg=self.colores["surface_white"],
            highlightthickness=1,
            highlightbackground=self.colores["surface_line"],
            highlightcolor=self.colores["surface_line"],
            padx=18, pady=14,
        )
        marco.pack(fill="x", pady=(0, 16))

        titulo = tk.Label(
            marco, text="📈  Progreso de Puntajes (Rondas de 5 min)",
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            font=self.fuentes["card_title"], anchor="w",
        )
        titulo.pack(fill="x")

        subtitulo = tk.Label(
            marco, text="Cada punto representa los mensajes enviados en una ronda de 5 minutos",
            bg=self.colores["surface_white"],
            fg=self.colores["text_muted"],
            font=self.fuentes["caption"], anchor="w",
        )
        subtitulo.pack(fill="x", pady=(2, 10))

        grafica = tk.Canvas(
            marco, height=220,
            bg=self.colores["surface_white"],
            highlightthickness=0, bd=0,
        )
        grafica.pack(fill="x")
        grafica.bind("<Configure>", lambda _e: self._dibujar_grafica_progreso())

        self._widgets_estadisticas["grafica"] = {
            "marco": marco, "titulo": titulo,
            "subtitulo": subtitulo, "canvas": grafica,
        }
        for w in (marco, titulo, subtitulo, grafica):
            w.bind("<MouseWheel>", self._scroll_estadisticas)
            w.bind("<Button-4>", self._scroll_estadisticas)
            w.bind("<Button-5>", self._scroll_estadisticas)

    def _scroll_estadisticas(self, event):
        if not hasattr(self, "_stats_canvas"):
            return "break"
        delta = getattr(event, "delta", 0)
        num = getattr(event, "num", None)
        if delta:
            pasos = -1 * int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            self._stats_canvas.yview_scroll(pasos, "units")
        elif num == 4:
            self._stats_canvas.yview_scroll(-1, "units")
        elif num == 5:
            self._stats_canvas.yview_scroll(1, "units")
        return "break"

    def _actualizar_estadisticas_ui(self):
        """Refresca todos los valores de la pestaña de estadísticas."""
        if not self._widgets_estadisticas:
            return

        resumen = self.gestor_estadisticas.obtener_resumen()

        # Tarjetas principales
        self._actualizar_valor_stat("mensajes_totales", str(resumen["mensajes_totales"]))
        self._actualizar_valor_stat("record_5min", str(resumen["record_5min"]))
        self._actualizar_valor_stat("racha_dias", str(resumen["racha_dias"]))
        self._actualizar_valor_stat("total_conversaciones", str(resumen["total_conversaciones"]))

        # Tarjetas adicionales
        self._actualizar_valor_stat("mensaje_mas_largo", f"{resumen['mensaje_mas_largo']} chars")
        self._actualizar_valor_stat("promedio_msgs", str(resumen["promedio_mensajes_conversacion"]))
        self._actualizar_valor_stat("dias_activos", str(resumen["dias_activos_total"]))

        # Ronda activa
        ronda = resumen["ronda_actual"]
        ronda_w = self._widgets_estadisticas.get("ronda")
        if ronda_w:
            if ronda["activa"]:
                mins = ronda["segundos_restantes"] // 60
                secs = ronda["segundos_restantes"] % 60
                ronda_w["estado"].configure(text="🟢 Activo", fg=self.colores["success"])
                ronda_w["msgs"].configure(text=f"Mensajes: {ronda['mensajes']}")
                ronda_w["tiempo"].configure(text=f"Tiempo: {mins:02d}:{secs:02d}")
                canvas = ronda_w["barra_canvas"]
                canvas.delete("all")
                ancho_c = canvas.winfo_width()
                progreso = ronda["segundos_restantes"] / 300.0
                canvas.create_rectangle(0, 0, int(ancho_c * progreso), 8, fill=self.colores["accent"], outline="")
            else:
                ronda_w["estado"].configure(text="Inactivo", fg=self.colores["text_muted"])
                ronda_w["msgs"].configure(text="Mensajes: 0")
                ronda_w["tiempo"].configure(text="Tiempo: --:--")
                ronda_w["barra_canvas"].delete("all")

        # Nivel
        nivel = resumen["nivel"]
        nivel_w = self._widgets_estadisticas.get("nivel")
        if nivel_w:
            nivel_w["nombre"].configure(text=f"{nivel['emoji']}  {nivel['nombre']}")
            max_n = nivel["max_nivel"]
            if max_n:
                nivel_w["info"].configure(text=f"{nivel['mensajes_totales']} / {max_n} mensajes")
                faltan = max_n - nivel["mensajes_totales"]
                nivel_w["desc"].configure(text=f"Te faltan {faltan} mensajes para el siguiente nivel")
            else:
                nivel_w["info"].configure(text=f"{nivel['mensajes_totales']} mensajes")
                nivel_w["desc"].configure(text="¡Has alcanzado el nivel máximo! 🎉")

            canvas = nivel_w["barra_canvas"]
            canvas.delete("all")
            ancho_c = canvas.winfo_width()
            alto_c = 18
            canvas.create_rectangle(0, 0, ancho_c, alto_c, fill=self.colores["surface_line"], outline="")
            prog_ancho = int(ancho_c * nivel["progreso"])
            if prog_ancho > 0:
                canvas.create_rectangle(0, 0, prog_ancho, alto_c, fill=self.colores["accent"], outline="")
                canvas.create_rectangle(0, 0, prog_ancho, alto_c // 3, fill=self.colores["accent_active"], outline="")
            color_txt = "#ffffff" if nivel["progreso"] > 0.15 else self.colores["text_muted"]
            canvas.create_text(
                ancho_c // 2, alto_c // 2,
                text=f"{int(nivel['progreso'] * 100)}%",
                fill=color_txt, font=("Helvetica", 9, "bold"),
            )

        # Gráfica
        self._dibujar_grafica_progreso()

    def _actualizar_valor_stat(self, key, valor):
        widget = self._widgets_estadisticas.get(key)
        if widget and "valor" in widget:
            widget["valor"].configure(text=valor)

    def _dibujar_grafica_progreso(self):
        """Dibuja la gráfica de línea con puntajes de rondas de 5 minutos."""
        graf = self._widgets_estadisticas.get("grafica")
        if not graf:
            return

        canvas = graf["canvas"]
        canvas.delete("all")

        ancho = canvas.winfo_width()
        alto = canvas.winfo_height()
        if ancho < 100 or alto < 60:
            return

        resumen = self.gestor_estadisticas.obtener_resumen()
        puntajes = resumen.get("puntajes_5min", [])
        record = resumen.get("record_5min", 0)

        m_izq, m_der, m_sup, m_inf = 45, 20, 20, 30
        area_w = ancho - m_izq - m_der
        area_h = alto - m_sup - m_inf

        # Fondo del área
        canvas.create_rectangle(
            m_izq, m_sup, ancho - m_der, alto - m_inf,
            fill=self.colores["surface_white"], outline=self.colores["surface_line"],
        )

        if not puntajes:
            canvas.create_text(
                ancho // 2, alto // 2,
                text="Aún no hay datos de rondas",
                fill=self.colores["text_muted"], font=self.fuentes["caption"],
            )
            return

        valores = [p.get("puntaje", 0) for p in puntajes]
        max_val = max(max(valores), record, 1)

        # Grid lines
        for i in range(5):
            y = m_sup + (area_h * i / 4)
            canvas.create_line(m_izq, y, ancho - m_der, y, fill=self.colores["surface_line"], dash=(2, 4))
            val = int(max_val * (1 - i / 4))
            canvas.create_text(m_izq - 8, y, text=str(val), fill=self.colores["text_muted"], font=("Helvetica", 9), anchor="e")

        # Record line
        if record > 0:
            ry = m_sup + area_h * (1 - record / max_val)
            canvas.create_line(m_izq, ry, ancho - m_der, ry, fill=self.colores["danger"], dash=(6, 3), width=1.5)
            canvas.create_text(
                ancho - m_der - 4, ry - 10,
                text=f"Récord: {record}", fill=self.colores["danger"],
                font=("Helvetica", 9, "bold"), anchor="e",
            )

        # Últimos 20 puntos
        mostrar = valores[-20:]
        n = len(mostrar)
        espaciado = area_w / max(n - 1, 1)

        puntos = []
        for i, val in enumerate(mostrar):
            x = m_izq + (i * espaciado if n > 1 else area_w / 2)
            y = m_sup + area_h * (1 - val / max_val)
            puntos.append((x, y))

        # Área de relleno bajo la curva
        if len(puntos) >= 2:
            poly = []
            for px, py in puntos:
                poly.extend([px, py])
            poly.extend([puntos[-1][0], alto - m_inf, puntos[0][0], alto - m_inf])
            canvas.create_polygon(poly, fill=self.colores["accent"], outline="", stipple="gray25")

        # Línea de la curva
        if len(puntos) >= 2:
            coords = []
            for px, py in puntos:
                coords.extend([px, py])
            canvas.create_line(coords, fill=self.colores["accent"], width=2.5, smooth=True)

        # Puntos
        for i, (px, py) in enumerate(puntos):
            r = 5
            es_rec = mostrar[i] == record and record > 0
            col = self.colores["danger"] if es_rec else self.colores["accent"]
            canvas.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="#ffffff", width=2)

        # Etiquetas eje X
        for i, (px, _py) in enumerate(puntos):
            if n <= 10 or i % max(1, n // 10) == 0 or i == n - 1:
                off = len(valores) - n
                canvas.create_text(
                    px, alto - m_inf + 14, text=str(off + i + 1),
                    fill=self.colores["text_muted"], font=("Helvetica", 8),
                )

    def _aplicar_tema_estadisticas(self):
        """Aplica los colores de tema a los widgets de estadísticas."""
        if not self._widgets_estadisticas:
            return

        self.estadisticas_tab.configure(bg=self.colores["panel"])
        if hasattr(self, "_stats_canvas"):
            self._stats_canvas.configure(bg=self.colores["panel"])
            self._stats_contenido.configure(bg=self.colores["panel"])
        if hasattr(self, "_stats_titulo"):
            self._stats_titulo.configure(bg=self.colores["panel"], fg=self.colores["text_primary"])
        if hasattr(self, "_stats_subtitulo"):
            self._stats_subtitulo.configure(bg=self.colores["panel"], fg=self.colores["text_muted"])

        for key in ("mensajes_totales", "record_5min", "racha_dias", "total_conversaciones",
                     "mensaje_mas_largo", "promedio_msgs", "dias_activos"):
            w = self._widgets_estadisticas.get(key)
            if not w:
                continue
            bg = self.colores["surface_white"]
            w["tarjeta"].configure(bg=bg, highlightbackground=self.colores["surface_line"], highlightcolor=self.colores["surface_line"])
            w["emoji"].configure(bg=bg)
            w["valor"].configure(bg=bg, fg=w["color_acento"])
            w["titulo"].configure(bg=bg, fg=self.colores["text_muted"])
            w["barra"].configure(bg=w["color_acento"])

        for key in ("fila_tarjetas", "fila_extra"):
            w = self._widgets_estadisticas.get(key)
            if w:
                w.configure(bg=self.colores["panel"])

        for panel_key in ("ronda", "nivel", "grafica"):
            panel = self._widgets_estadisticas.get(panel_key)
            if not panel:
                continue
            bg = self.colores["surface_white"]
            for _wk, wv in panel.items():
                if isinstance(wv, (tk.Frame, tk.Label)):
                    try:
                        wv.configure(bg=bg, highlightbackground=self.colores["surface_line"], highlightcolor=self.colores["surface_line"])
                    except tk.TclError:
                        try:
                            wv.configure(bg=bg)
                        except tk.TclError:
                            pass
                elif isinstance(wv, tk.Canvas):
                    wv.configure(bg=bg)

        if self.vista_activa == "estadisticas":
            self._actualizar_estadisticas_ui()

