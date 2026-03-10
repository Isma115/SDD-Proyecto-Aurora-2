Funcionamiento principal del Proyecto Aurora

El Proyecto Aurora es un proyecto de momento de solo terminal, que trata de humanizar un chatbot con IA al punto de que sea casi indistinguible de un humano, para ello se han creado varias funcionalidades que permiten al chatbot tener una personalidad, una memoria, y una capacidad de razonamiento.

1. main.py: Archivo principal que ejecuta el programa
2. motorLLM.py: Se encarga de la comunicación con el LLM, el flujo de datos de entrada y salida del LLM, la congelación, etc y funcionalidades varias
3. recursos.py se encarga de la gestión de memoria, datos e información sobre el usuario, y el conocimiento almacenado y recuperado mediante RAG
4. gestorLLM, se encarga de gestionar las instancias de un LLM en este proyecto van a existir dos instancias de LLM, una dedicada a proporcionar las respuestas y seguir el flujo de conversación, y otra instancia dedicada a generar una toma de decisión, un pensamiento, memorizar información, o recordar información.

la librería principal de LLM es llama-cpp-python

[COMPLETADA] Ahora mismo los ficheros están vacíos, el programa debe hacer lo siguiente: Al iniciar el programa se debe descargar el modelo Gemma 2 2B si este no estaba descargado previamente y guardarlo en la carpeta models, y conseguir que se pueda llevar una conversación simple con el modelo y este con una personalidad amigable responder con una estructura conversacional


[TAREA] Definir un fichero de system prompt que defina la personalidad de Aurora, su pasado, sus vivencias, etc, basándote en una chica , y que esta sea capaz de mantener una conversación coherente y natural con el usuario, además de tener una personalidad amigable y empática. Este fichero se utilizará en el gestorLLM para proporcionar el system prompt al modelo. Ya he definido un system_prompt.txt ahora necesito que lo implementes en el gestorLLM y que este sea capaz de mantener una conversación coherente y natural con el usuario.