from gestorLLM import GestorLLM

# Colores para la terminal
COLOR_USUARIO = "\033[92m"  # Verde
COLOR_AURORA  = "\033[96m"  # Cian
COLOR_DIM     = "\033[2m"   # Texto atenuado (para mostrar sesión anterior)
COLOR_RESET   = "\033[0m"


def mostrar_sesion_anterior(sesion_anterior):
    """Muestra en terminal la última conversación guardada de forma atenuada."""
    if not sesion_anterior:
        return

    print(f"\n{COLOR_DIM}{'─' * 45}")
    print(f"  Retomando última conversación ({len(sesion_anterior)//2} turno(s))")
    print(f"{'─' * 45}{COLOR_RESET}")

    for msg in sesion_anterior:
        if msg["role"] == "user":
            print(f"{COLOR_DIM}{COLOR_USUARIO}Tú:{COLOR_RESET}{COLOR_DIM} {msg['content']}{COLOR_RESET}")
        else:
            print(f"{COLOR_DIM}{COLOR_AURORA}Aurora:{COLOR_RESET}{COLOR_DIM} {msg['content']}{COLOR_RESET}")

    print(f"{COLOR_DIM}{'─' * 45}{COLOR_RESET}\n")


def main():
    print("=========================================")
    print("        Bienvenido al Proyecto Aurora      ")
    print("=========================================")

    # Inicializamos el gestor principal, que de forma transparente
    # descargará o cargará el modelo local.
    gestor = GestorLLM()

    # Mostrar la sesión anterior si existía
    mostrar_sesion_anterior(gestor.sesion_anterior)

    print("\n[Aurora está lista. Escribe 'salir' o 'exit' para terminar.]\n")

    while True:
        try:
            # Capturamos la entrada del usuario con color
            entrada = input(f"\n{COLOR_USUARIO}Tú:{COLOR_RESET} ")

            # Condición de salida
            if entrada.lower().strip() in ["salir", "exit", "quit"]:
                gestor.guardar_sesion()
                print(f"{COLOR_AURORA}Aurora:{COLOR_RESET} ¡Hasta luego! Ha sido un placer hablar contigo.")
                break

            # Si el usuario solo pulsó Enter, ignoramos
            if not entrada.strip():
                continue

            # Obtenemos la respuesta de Aurora
            respuesta = gestor.obtener_respuesta(entrada)

            # Mostramos la respuesta con color
            print(f"\n{COLOR_AURORA}Aurora:{COLOR_RESET} {respuesta}")

        except KeyboardInterrupt:
            # Manejamos Ctrl+C: guardar conversación antes de salir
            print(f"\n{COLOR_AURORA}Aurora:{COLOR_RESET} ¡Hasta luego! Programa interrumpido.")
            gestor.guardar_sesion()
            break
        except Exception as e:
            print(f"\n[Error inesperado]: {e}")

if __name__ == "__main__":
    main()
