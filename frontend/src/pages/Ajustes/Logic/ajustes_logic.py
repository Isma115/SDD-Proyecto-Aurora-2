import json
import os
import tkinter as tk

from motorLLM import crear_configuracion_por_defecto


class AjustesLogicMixin:
    def _normalizar_configuracion_modelo(self, config):
        normalizada = crear_configuracion_por_defecto()
        if not isinstance(config, dict):
            return normalizada

        for seccion, valores in normalizada.items():
            origen = config.get(seccion)
            if isinstance(valores, dict) and isinstance(origen, dict):
                valores.update(origen)
        return normalizada

    def _cargar_configuracion_modelo(self):
        if self.gestor and getattr(self.gestor, "motor", None):
            return self._normalizar_configuracion_modelo(self.gestor.motor.config)

        if not os.path.exists(self.archivo_config_modelo):
            return crear_configuracion_por_defecto()

        try:
            with open(self.archivo_config_modelo, "r", encoding="utf-8") as f:
                cargada = json.load(f)
        except Exception:
            return crear_configuracion_por_defecto()

        return self._normalizar_configuracion_modelo(cargada)

    def _formatear_valor_ajuste(self, valor, tipo):
        if valor is None and tipo in ("optional_int", "optional_text"):
            return ""
        return "" if valor is None else str(valor)

    def _interpretar_valor_ajuste(self, texto, tipo, etiqueta):
        valor = texto.strip()
        if tipo == "float":
            if not valor:
                raise ValueError(f"El campo '{etiqueta}' no puede estar vacío.")
            return float(valor)
        if tipo == "int":
            if not valor:
                raise ValueError(f"El campo '{etiqueta}' no puede estar vacío.")
            return int(valor)
        if tipo == "optional_int":
            return None if not valor else int(valor)
        if tipo == "optional_text":
            return valor or None
        return valor

    def _guardar_ajustes_modelo(self):
        if self.esta_ocupada:
            mensaje = "Espera a que Aurora termine antes de guardar ajustes del modelo."
            self.estado_var.set(mensaje)
            self._agregar_mensaje_sistema(mensaje)
            self._agregar_reflexion(mensaje)
            return

        config_modelo = self._cargar_configuracion_modelo()
        try:
            for definicion in self.DEFINICIONES_AJUSTES_MODELO:
                seccion = definicion["seccion"]
                for campo in definicion["campos"]:
                    variable = self.vars_ajustes_modelo.get((seccion, campo["clave"]))
                    texto = variable.get() if variable else ""
                    config_modelo[seccion][campo["clave"]] = self._interpretar_valor_ajuste(
                        texto,
                        campo["tipo"],
                        campo["etiqueta"],
                    )
        except ValueError as exc:
            mensaje = f"No se pudieron guardar los ajustes: {exc}"
            self.estado_var.set(mensaje)
            self._agregar_mensaje_sistema(mensaje)
            self._agregar_reflexion(mensaje)
            return

        try:
            if self.gestor and getattr(self.gestor, "motor", None):
                self.esta_ocupada = True
                self.estado_var.set("Aplicando ajustes del modelo...")
                self._agregar_reflexion("Aplicando nueva configuración del modelo local.")
                self._actualizar_estado_controles()
                self._lanzar_hilo(self._aplicar_ajustes_modelo_en_hilo, config_modelo)
                return
            else:
                with open(self.archivo_config_modelo, "w", encoding="utf-8") as f:
                    json.dump(config_modelo, f, ensure_ascii=False, indent=4)
                recargo_modelo = False
        except Exception as exc:
            mensaje = f"Error aplicando los ajustes del modelo: {exc}"
            self.estado_var.set(mensaje)
            self._agregar_mensaje_sistema(mensaje)
            self._agregar_reflexion(mensaje)
            return

        mensaje = (
            "Ajustes guardados. El modelo se ha recargado con la nueva configuración."
            if recargo_modelo
            else "Ajustes guardados. Los nuevos parámetros de generación ya están activos."
        )
        self.estado_var.set(mensaje)
        self._agregar_mensaje_sistema(mensaje)
        self._agregar_reflexion(mensaje)

    def _aplicar_ajustes_modelo_en_hilo(self, config_modelo):
        try:
            recargo_modelo = self.gestor.motor.actualizar_configuracion(config_modelo)
            self.event_queue.put(("settings_saved", recargo_modelo))
        except Exception as exc:
            self.event_queue.put(("settings_error", str(exc)))

    def _aplicar_tema_ventana_ajustes(self):
        if not self.ventana_ajustes or not self.ventana_ajustes.winfo_exists():
            return
        self.ventana_ajustes.configure(bg=self.colores["panel"])
        self.panel_ajustes.configure(bg=self.colores["panel"])
        self.canvas_ajustes.configure(bg=self.colores["panel"])
        self.contenido_ajustes.configure(bg=self.colores["panel"])
        self.footer_ajustes.configure(bg=self.colores["panel"])
        self.label_ajustes.configure(bg=self.colores["panel"], fg=self.colores["text_primary"])
        self.descripcion_ajustes.configure(bg=self.colores["panel"], fg=self.colores["text_secondary"])
        try:
            self.scroll_ajustes.configure(
                bg=self.colores["panel_soft"],
                activebackground=self.colores["accent"],
                troughcolor=self.colores["panel"],
            )
        except tk.TclError:
            self.scroll_ajustes.configure(
                bg=self.colores["panel_soft"],
                activebackground=self.colores["accent"],
            )
        for frame in self.widgets_ajustes.get("frames", []):
            frame.configure(bg=self.colores["surface_white"])
        for card in self.widgets_ajustes.get("cards", []):
            card.configure(
                bg=self.colores["surface_white"],
                highlightbackground=self.colores["surface_line"],
                highlightcolor=self.colores["surface_line"],
            )
        for titulo in self.widgets_ajustes.get("titles", []):
            titulo.configure(bg=self.colores["surface_white"], fg=self.colores["text_primary"])
        for descripcion in self.widgets_ajustes.get("descriptions", []):
            descripcion.configure(bg=self.colores["surface_white"], fg=self.colores["text_secondary"])
        for nota in self.widgets_ajustes.get("notes", []):
            nota.configure(bg=self.colores["panel"], fg=self.colores["warning"])
        self.check_modo_oscuro.configure(
            bg=self.colores["surface_white"],
            fg=self.colores["text_primary"],
            activebackground=self.colores["surface_white"],
            activeforeground=self.colores["text_primary"],
            selectcolor=self.colores["surface_white"],
            font=self.fuentes["body"],
        )
        for entry in self.widgets_ajustes.get("entries", []):
            entry.configure(
                bg=self.colores["field_bg"],
                fg=self.colores["text_primary"],
                insertbackground=self.colores["text_primary"],
                highlightbackground=self.colores["field_border"],
                highlightcolor=self.colores["accent"],
            )
        self._aplicar_estilo_boton_ui(self.boton_guardar_ajustes)
        self._aplicar_estilo_boton_ui(self.boton_cerrar_ajustes)

    def _cerrar_ajustes(self):
        if self.ventana_ajustes and self.ventana_ajustes.winfo_exists():
            self.ventana_ajustes.destroy()
        self.ventana_ajustes = None
        self.var_modo_oscuro = None
        self.vars_ajustes_modelo = {}
        self.widgets_ajustes = {}

    def _alternar_modo_oscuro_desde_ui(self):
        nuevo_valor = bool(self.var_modo_oscuro.get()) if self.var_modo_oscuro else False
        if nuevo_valor == self.modo_oscuro:
            return
        self.modo_oscuro = nuevo_valor
        self._configurar_estilos()
        self._guardar_ajustes_ui()
        self._aplicar_tema_actual()

