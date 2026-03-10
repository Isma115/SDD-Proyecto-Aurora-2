from gestorLLM import GestorLLM

def main():
    print("=========================================")
    print("        Bienvenido al Proyecto Aurora      ")
    print("=========================================")
    
    # Inicializamos el gestor principal, que de forma transparente 
    # descargará o cargará el modelo local.
    gestor = GestorLLM()
    
    print("\n[Aurora está lista. Escribe 'salir' o 'exit' para terminar.]\n")
    
    while True:
        try:
            # Capturamos la entrada del usuario
            entrada = input("\nTú: ")
            
            # Condición de salida
            if entrada.lower().strip() in ["salir", "exit", "quit"]:
                print("Aurora: ¡Hasta luego! Ha sido un placer hablar contigo.")
                break
            
            # Si el usuario solo pulsó Enter, ignoramos
            if not entrada.strip():
                continue
                
            # Obtenemos la respuesta de Aurora
            respuesta = gestor.obtener_respuesta(entrada)
            
            # Mostramos la respuesta
            print(f"\nAurora: {respuesta}")
            
        except KeyboardInterrupt:
            # Manejamos Ctrl+C
            print("\nAurora: ¡Hasta luego! Programa interrumpido.")
            break
        except Exception as e:
            print(f"\n[Error inesperado]: {e}")

if __name__ == "__main__":
    main()
