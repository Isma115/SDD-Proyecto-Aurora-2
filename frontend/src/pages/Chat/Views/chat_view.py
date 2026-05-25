import datetime
import re
import tkinter as tk


class ChatViewMixin:
    def _actualizar_estado_controles(self):
        entrada_habilitada = self.esta_lista and not self.esta_ocupada and not self.cierre_pendiente
        estado_entrada = "normal" if entrada_habilitada else "disabled"
        estado_boton = "normal" if entrada_habilitada else "disabled"
        estado_nueva = "normal" if entrada_habilitada else "disabled"
        color_texto = self.colores["text_primary"] if entrada_habilitada else self.colores["text_muted"]
        
        self.entrada_text.configure(state=estado_entrada, fg=color_texto)
        self._establecer_estado_boton_ui(self.boton_enviar, estado_boton)
        self._establecer_estado_boton_ui(self.boton_nueva_conversacion, estado_nueva)
        self._establecer_estado_boton_ui(self.boton_ajustes, "normal")

        if self.cierre_pendiente:
            self.boton_enviar.configure(text="…")
            self._establecer_estado_boton_ui(self.boton_enviar, "disabled")
            self.presencia_var.set("cerrando...")
        elif self.esta_ocupada:
            self.boton_enviar.configure(text="…")
            self._establecer_estado_boton_ui(self.boton_enviar, "disabled")
        elif self.esta_lista:
            self.boton_enviar.configure(text="➤")
            self._establecer_estado_boton_ui(self.boton_enviar, "normal")
        else:
            self.boton_enviar.configure(text="…")
            self._establecer_estado_boton_ui(self.boton_enviar, "disabled")

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
        burbuja = self._crear_burbuja_chat(autor, contenido_visible)
        self.chat_text.window_create("end", window=burbuja)
        self.chat_text.insert("end", "\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
        self._actualizar_burbujas_chat()

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

    def _sincronizar_presencia_desde_estado(self, texto):
        texto_l = texto.lower()
        if "escribiendo" in texto_l or "procesando" in texto_l:
            self.presencia_var.set("escribiendo...")
        elif "error" in texto_l or "fallo" in texto_l:
            self.presencia_var.set("con problemas")
        elif "lista" in texto_l:
            self.presencia_var.set("en línea")

    def _hora_visual_chat(self):
        return datetime.datetime.now().strftime("%H:%M")

    def _crear_burbuja_chat(self, autor, contenido):
        es_usuario = autor == "Tú"
        color_burbuja = self.colores["user_bubble"] if es_usuario else self.colores["assistant_bubble"]
        fuente_texto = self._fuente_con_tamano(self.fuentes["body_chat"], self.tamano_historial)
        fuente_meta = self._fuente_con_tamano(
            self.fuentes["caption"],
            max(self.tamano_historial_min - 1, self.tamano_historial - 4),
        )

        wrapper = tk.Frame(self.chat_text, bg=self.colores["panel"])
        wrapper.pack_propagate(False)
        contenedor = tk.Frame(wrapper, bg=self.colores["panel"])
        contenedor.pack(fill="both", expand=True)

        burbuja = tk.Frame(
            contenedor,
            bg=color_burbuja,
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colores["bubble_border"] if not es_usuario else color_burbuja,
        )
        burbuja.pack(
            anchor="e" if es_usuario else "w",
            padx=(220, 12) if es_usuario else (14, 180),
            pady=(8, 10),
        )

        etiqueta_texto = tk.Label(
            burbuja,
            text=contenido if contenido else " ",
            bg=color_burbuja,
            fg=self.colores["text_primary"],
            font=fuente_texto,
            justify="left",
            anchor="w",
            padx=14,
            pady=10,
        )
        etiqueta_texto.pack(anchor="w")

        meta = self._hora_visual_chat()
        if es_usuario:
            meta += "  ✓✓"
        etiqueta_meta = tk.Label(
            burbuja,
            text=meta,
            bg=color_burbuja,
            fg=self.colores["text_muted"],
            font=fuente_meta,
            padx=14,
            pady=0,
        )
        etiqueta_meta.pack(anchor="e", pady=(0, 7))

        for widget in (wrapper, contenedor, burbuja, etiqueta_texto, etiqueta_meta):
            self._registrar_scroll_en_widget(widget)

        self.burbujas_chat.append(
            {
                "wrapper": wrapper,
                "contenedor": contenedor,
                "burbuja": burbuja,
                "texto": etiqueta_texto,
                "es_usuario": es_usuario,
            }
        )
        return wrapper

    def _agregar_chip_chat(self, texto):
        if self.separador_chat_insertado:
            return

        chip = tk.Label(
            self.chat_text,
            text=texto,
            bg=self.colores["chip_bg"],
            fg=self.colores["text_secondary"],
            font=self.fuentes["caption_bold"],
            padx=10,
            pady=4,
        )
        wrapper = tk.Frame(self.chat_text, bg=self.colores["panel"])
        chip.pack(in_=wrapper, pady=8)
        self._registrar_scroll_en_widget(wrapper)
        self._registrar_scroll_en_widget(chip)

        self.chat_text.configure(state="normal")
        self.chat_text.window_create("end", window=wrapper)
        self.chat_text.insert("end", "\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
        self.separador_chat_insertado = True

    def _al_redimensionar_chat(self, _event=None):
        self._actualizar_burbujas_chat()

    def _actualizar_burbujas_chat(self):
        ancho = max(self.chat_text.winfo_width(), 420)
        margen_usuario = max(180, int(ancho * 0.28))
        margen_asistente = max(28, int(ancho * 0.10))
        wrap = max(520, int(ancho * 0.68))

        for item in self.burbujas_chat:
            item["wrapper"].configure(width=max(ancho - 10, 200))
            item["contenedor"].configure(width=max(ancho - 10, 200))
            if item["es_usuario"]:
                item["burbuja"].pack_configure(padx=(margen_usuario, 12), pady=(8, 10))
            else:
                item["burbuja"].pack_configure(padx=(14, margen_asistente), pady=(8, 10))
            item["texto"].configure(wraplength=wrap)
            item["wrapper"].update_idletasks()
            item["wrapper"].configure(height=item["contenedor"].winfo_reqheight())

    def _insertar_placeholder_contexto(self):
        self.contexto_text.configure(state="normal")
        if self.contexto_text.index("end-1c") != "1.0":
            self.contexto_text.configure(state="disabled")
            return
        self.contexto_text.insert(
            "end",
            "Aquí aparecerá, turno a turno, el contexto exacto que se envía al modelo.\n\n",
            "contexto_meta",
        )
        self.contexto_text.configure(state="disabled")

    def _sincronizar_historial_contexto_modelo(self):
        if not self.gestor:
            return
        for snapshot in self.gestor.obtener_historial_contexto_modelo():
            self._agregar_contexto_completo(snapshot)

    def _construir_texto_contexto_modelo(self, snapshot):
        indice = snapshot.get("indice", "?")
        timestamp = snapshot.get("timestamp", "")
        intencion = snapshot.get("intencion", "desconocida")
        mensajes = snapshot.get("mensajes_modelo", [])

        lineas = [
            f"Turno {indice}",
            f"Marca temporal: {timestamp}",
            f"Intención detectada: {intencion}",
            f"Mensajes enviados al modelo: {len(mensajes)}",
            "",
        ]

        for posicion, mensaje in enumerate(mensajes, start=1):
            role = mensaje.get("role", "desconocido")
            contenido = str(mensaje.get("content", "")).strip()
            lineas.append(f"[{posicion}] role={role}")
            lineas.append(contenido if contenido else "[vacío]")
            lineas.append("")

        return "\n".join(lineas).rstrip()

    def _agregar_contexto_completo(self, snapshot):
        indice = snapshot.get("indice")
        if indice in self.contextos_renderizados:
            return

        if self.contexto_text.get("1.0", "end-1c").startswith("Aquí aparecerá, turno a turno"):
            self.contexto_text.configure(state="normal")
            self.contexto_text.delete("1.0", "end")
            self.contexto_text.configure(state="disabled")

        bloque = self._construir_texto_contexto_modelo(snapshot)
        self.contexto_text.configure(state="normal")
        self.contexto_text.insert("end", f"Contexto completo · turno {indice}\n", "contexto_titulo")
        self.contexto_text.insert(
            "end",
            f"{snapshot.get('resumen', '').strip()}\n",
            "contexto_meta",
        )
        self.contexto_text.insert("end", f"{bloque}\n\n", "contexto_bloque")
        self.contexto_text.configure(state="disabled")
        self.contexto_text.see("end")
        self.contextos_renderizados.add(indice)

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
