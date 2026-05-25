import json
import os
import queue
import threading

from api import AuroraEmbeddedAPIServer
from gestorLLM import GestorLLM


class ChatLogicMixin:
    def _reconstruir_chat_visual(self):
        if not hasattr(self, "chat_text"):
            return

        borrador = ""
        if hasattr(self, "entrada_text"):
            borrador = self.entrada_text.get("1.0", "end-1c")

        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self.burbujas_chat = []
        self.separador_chat_insertado = False
        self._agregar_chip_chat("HOY")

        if self.gestor:
            historial = self.gestor.memoria.obtener_historial()
            for mensaje in historial:
                autor = "Tú" if mensaje.get("role") == "user" else "Aurora"
                self._agregar_mensaje_chat(autor, mensaje.get("content", ""), "", "")

        if hasattr(self, "entrada_text"):
            self.entrada_text.delete("1.0", "end")
            if borrador:
                self.entrada_text.insert("1.0", borrador)

    def _configurar_tags_chat(self):
        self.chat_text.configure(font=self._fuente_con_tamano(self.fuentes["body_chat"], self.tamano_historial))
        if hasattr(self, "label_nombre"):
            self.label_nombre.configure(font=self._fuente_con_tamano(self.fuentes["hero"], max(18, self.tamano_historial - 1)))
        if hasattr(self, "label_presencia"):
            self.label_presencia.configure(font=self._fuente_con_tamano(self.fuentes["caption"], max(12, self.tamano_historial - 5)))

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

    def _scroll_chat_mousewheel(self, event):
        if not hasattr(self, "chat_text"):
            return "break"

        delta = getattr(event, "delta", 0)
        num = getattr(event, "num", None)

        if delta:
            pasos = -1 * int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            self.chat_text.yview_scroll(pasos, "units")
        elif num == 4:
            self.chat_text.yview_scroll(-1, "units")
        elif num == 5:
            self.chat_text.yview_scroll(1, "units")
        return "break"

    def _registrar_scroll_en_widget(self, widget):
        for secuencia in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(secuencia, self._scroll_chat_mousewheel)

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

        modo_oscuro = ajustes.get("modo_oscuro")
        if isinstance(modo_oscuro, bool):
            self.modo_oscuro = modo_oscuro

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
        ajustes["modo_oscuro"] = self.modo_oscuro

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
            api_server = AuroraEmbeddedAPIServer(
                gestor=gestor,
                gestor_estadisticas=self.gestor_estadisticas,
            )
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
            elif tipo == "settings_saved":
                self._mostrar_ajustes_guardados(evento[1])
            elif tipo == "settings_error":
                self._mostrar_error_ajustes(evento[1])

        self.root.after(100, self._procesar_eventos)

    def _actualizar_estado(self, mensaje):
        if isinstance(mensaje, dict) and mensaje.get("tipo") == "fuentes_conocimiento":
            resumen = str(mensaje.get("resumen", "")).strip()
            if resumen:
                self.estado_var.set(resumen)
            self._agregar_reflexion_fuentes(mensaje)
            return
        if isinstance(mensaje, dict) and mensaje.get("tipo") == "contexto_modelo":
            resumen = str(mensaje.get("resumen", "")).strip()
            if resumen:
                self._agregar_reflexion(resumen)
            self._agregar_contexto_completo(mensaje)
            return

        texto = str(mensaje)
        self.estado_var.set(texto)
        self._sincronizar_presencia_desde_estado(texto)
        self._agregar_reflexion(texto)

    def _marcar_lista(self, gestor):
        self.gestor = gestor
        self.esta_lista = True
        self.esta_ocupada = False
        self.estado_var.set("Aurora lista. Escribe abajo para empezar.")
        self.presencia_var.set("en línea")
        self._agregar_mensaje_sistema("Aurora está lista.")
        self._agregar_reflexion("Aurora lista para conversar.")
        self._mostrar_sesion_anterior()
        if not self.gestor.sesion_anterior:
            self._agregar_chip_chat("HOY")
        self._sincronizar_historial_contexto_modelo()
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()
        self.servidor_var.set("Servidor local: iniciando API...")
        self._lanzar_hilo(self._inicializar_api_embebida, gestor)

    def _mostrar_api_lista(self, api_server):
        self.api_server = api_server
        self.servidor_var.set(f"Servidor local: {api_server.url_local}")
        self._agregar_mensaje_sistema(
            f"Servidor de red local activo. La app móvil puede conectarse en {api_server.url_local}"
        )
        self._agregar_reflexion(
            f"Servidor embebido iniciado en {api_server.url_local} para clientes móviles."
        )

    def _mostrar_error_api(self, error):
        self.servidor_var.set("Servidor local: no disponible")
        self._agregar_mensaje_sistema(
            f"No se pudo iniciar el servidor de red local: {error}"
        )
        self._agregar_reflexion(
            f"Fallo al iniciar la API embebida: {error}"
        )

    def _mostrar_ajustes_guardados(self, recargo_modelo):
        self.esta_ocupada = False
        self._actualizar_estado_controles()
        mensaje = (
            "Ajustes guardados. El modelo se ha recargado con la nueva configuración."
            if recargo_modelo
            else "Ajustes guardados. Los nuevos parámetros de generación ya están activos."
        )
        self.estado_var.set(mensaje)
        self._agregar_mensaje_sistema(mensaje)
        self._agregar_reflexion(mensaje)

    def _mostrar_error_ajustes(self, error):
        self.esta_ocupada = False
        self._actualizar_estado_controles()
        mensaje = f"Error aplicando los ajustes del modelo: {error}"
        self.estado_var.set(mensaje)
        self._agregar_mensaje_sistema(mensaje)
        self._agregar_reflexion(mensaje)

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
        self.contextos_renderizados = set()
        self.burbujas_chat = []
        self.separador_chat_insertado = False

        self.contexto_text.configure(state="normal")
        self.contexto_text.delete("1.0", "end")
        self.contexto_text.configure(state="disabled")
        self._insertar_placeholder_contexto()

        self.entrada_text.configure(state="normal")
        self.entrada_text.delete("1.0", "end")
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()

        self.estado_var.set("Nueva conversación iniciada. Escribe para empezar.")
        self.presencia_var.set("en línea")
        self._agregar_reflexion("Nueva conversación iniciada. Historial previo descartado.")
        self._agregar_chip_chat("HOY")

    def _enviar_mensaje(self):
        if not self.esta_lista or self.esta_ocupada:
            return

        mensaje = self.entrada_text.get("1.0", "end").strip()
        if not mensaje:
            return

        self.entrada_text.delete("1.0", "end")
        self._agregar_mensaje_chat("Tú", mensaje, "speaker_user", "message_user")
        self.gestor_estadisticas.registrar_mensaje(len(mensaje))
        self.estado_var.set("Aurora está procesando el mensaje...")
        self.presencia_var.set("escribiendo...")
        self._agregar_reflexion("Mensaje del usuario enviado. Aurora comienza a procesarlo.")
        self.esta_ocupada = True
        self._actualizar_estado_controles()
        self._lanzar_hilo(self._generar_respuesta, mensaje)

    def _mostrar_respuesta(self, respuesta):
        self._agregar_mensaje_chat("Aurora", respuesta, "speaker_assistant", "message_assistant")
        self.estado_var.set("Aurora lista. Puedes seguir escribiendo.")
        self.presencia_var.set("en línea")
        self._agregar_reflexion("Respuesta generada y añadida a la conversación.")
        self.esta_ocupada = False
        self._actualizar_estado_controles()
        self.entrada_text.focus_set()
        if self.vista_activa == "estadisticas":
            self._actualizar_estadisticas_ui()

        if self.cierre_pendiente:
            self._cerrar_aplicacion()

    def _mostrar_error(self, error):
        self._agregar_mensaje_sistema(f"Error al generar la respuesta: {error}")
        self.estado_var.set("Se produjo un error al responder.")
        self.presencia_var.set("con problemas")
        self._agregar_reflexion(f"Error durante la generación: {error}")
        self.esta_ocupada = False
        self._actualizar_estado_controles()

        if self.cierre_pendiente:
            self._cerrar_aplicacion()

    def _mostrar_error_inicializacion(self, error):
        self._agregar_mensaje_sistema(f"No se pudo iniciar Aurora: {error}")
        self.estado_var.set("Fallo al iniciar Aurora.")
        self.presencia_var.set("no disponible")
        self._agregar_reflexion(f"Error de inicialización: {error}")
        self.esta_lista = False
        self.esta_ocupada = False
        self._actualizar_estado_controles()


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
        if self.gestor_estadisticas:
            try:
                self.gestor_estadisticas.detener()
            except Exception:
                pass

        if self.api_server:
            try:
                self.api_server.stop()
            except Exception as exc:
                self._agregar_reflexion(f"Fallo al detener el servidor embebido: {exc}")

        self.root.destroy()
