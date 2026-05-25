import argparse

from backend.src.controllers.llm_controller import GestorLLM
from frontend.src.pages.MainWorkspace.Logic.aurora_gui import AuroraGUI


COLOR_USUARIO = "\033[92m"
COLOR_AURORA = "\033[96m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def mostrar_sesion_anterior(sesion_anterior):
    if not sesion_anterior:
        return

    print(f"\n{COLOR_DIM}{'─' * 45}")
    print(f"  Retomando última conversación ({len(sesion_anterior) // 2} turno(s))")
    print(f"{'─' * 45}{COLOR_RESET}")

    for msg in sesion_anterior:
        if msg["role"] == "user":
            print(f"{COLOR_DIM}{COLOR_USUARIO}Tú:{COLOR_RESET}{COLOR_DIM} {msg['content']}{COLOR_RESET}")
        else:
            print(f"{COLOR_DIM}{COLOR_AURORA}Aurora:{COLOR_RESET}{COLOR_DIM} {msg['content']}{COLOR_RESET}")

    print(f"{COLOR_DIM}{'─' * 45}{COLOR_RESET}\n")


def main_cli():
    print("=========================================")
    print("        Bienvenido al Proyecto Aurora    ")
    print("=========================================")

    gestor = GestorLLM()
    mostrar_sesion_anterior(gestor.sesion_anterior)
    print("\n[Aurora está lista. Escribe 'salir' o 'exit' para terminar.]\n")

    while True:
        try:
            entrada = input(f"\n{COLOR_USUARIO}Tú:{COLOR_RESET} ")

            if entrada.lower().strip() in ["salir", "exit", "quit"]:
                gestor.guardar_sesion()
                print(f"{COLOR_AURORA}Aurora:{COLOR_RESET} ¡Hasta luego! Ha sido un placer hablar contigo.")
                break

            if not entrada.strip():
                continue

            respuesta = gestor.obtener_respuesta(entrada)
            print(f"\n{COLOR_AURORA}Aurora:{COLOR_RESET} {respuesta}")
        except KeyboardInterrupt:
            print(f"\n{COLOR_AURORA}Aurora:{COLOR_RESET} ¡Hasta luego! Programa interrumpido.")
            gestor.guardar_sesion()
            break
        except Exception as e:
            print(f"\n[Error inesperado]: {e}")


def main():
    parser = argparse.ArgumentParser(description="Proyecto Aurora")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Ejecuta la versión de terminal en lugar de la interfaz gráfica.",
    )
    args = parser.parse_args()

    if args.cli:
        main_cli()
        return

    app = AuroraGUI()
    app.run()


if __name__ == "__main__":
    main()
