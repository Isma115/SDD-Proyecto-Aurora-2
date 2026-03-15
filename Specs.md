Funcionamiento principal del Proyecto Aurora

El Proyecto Aurora es un proyecto de momento de solo terminal, que trata de humanizar un chatbot con IA al punto de que sea casi indistinguible de un humano, para ello se han creado varias funcionalidades que permiten al chatbot tener una personalidad, una memoria, y una capacidad de razonamiento.

1. main.py: Archivo principal que ejecuta el programa
2. motorLLM.py: Se encarga de la comunicación con el LLM, el flujo de datos de entrada y salida del LLM, la congelación, etc y funcionalidades varias
3. recursos.py se encarga de la gestión de memoria, datos e información sobre el usuario, y el conocimiento almacenado y recuperado mediante RAG
4. gestorLLM, se encarga de gestionar las instancias de un LLM en este proyecto van a existir dos instancias de LLM, una dedicada a proporcionar las respuestas y seguir el flujo de conversación, y otra instancia dedicada a generar una toma de decisión, un pensamiento, memorizar información, o recordar información.

la librería principal de LLM es llama-cpp-python

[COMPLETADA] Ahora mismo los ficheros están vacíos, el programa debe hacer lo siguiente: Al iniciar el programa se debe descargar el modelo Gemma 2 2B si este no estaba descargado previamente y guardarlo en la carpeta models, y conseguir que se pueda llevar una conversación simple con el modelo y este con una personalidad amigable responder con una estructura conversacional


[COMPLETADA] Definir un fichero de system prompt que defina la personalidad de Aurora, su pasado, sus vivencias, etc, basándote en una chica , y que esta sea capaz de mantener una conversación coherente y natural con el usuario, además de tener una personalidad amigable y empática. Este fichero se utilizará en el gestorLLM para proporcionar el system prompt al modelo. Ya he definido un system_prompt.txt ahora necesito que lo implementes en el gestorLLM y que este sea capaz de mantener una conversación coherente y natural con el usuario.

[COMPLETADA] Cada vez que Aurora responde al usuario, posteriormente internamente tiene que producirse un proceso de "generación de pensamiento", lo cual lleva de forma aleatoria a Aurora a generar un recuerdo de la conversación con el usuario de los últimos mensajes, y memorizar ese recuerdo en su base de conocimiento. O también puede estar la opción de que el pensamiento tenga como objetivo recordar información anterior de Aurora, (dentro de Memoria, en esta carpeta se almacenará el conocimiento, recuerdos y detalles del usuario) y de forma selectiva mediante ese proceso de "pensamiento" Aurora seleccionará el recuerdo o conocimiento anterior más adecuado para la conversación actual. Quiero que generes también un documento dónde documentes de forma explicativa y fácil como funciona el sistema que has creado para hacer esto, con una explicación sencilla, y luego una explicación dándo detalles más técnicos después

[COMPLETADA] Gestionar un fichero user_system_prompt.txt que tenga información crucial sobre el usuario, (en este caso solamente el nombre) debe estar cargado siempre, por lo que será parte del system prompt (se concatenarán ambos ficheros)

[COMPLETADA] El pensamiento de Aurora no debe generar recuerdos repetidos

[COMPLETADA] Aurora debe tener conocimiento de cualquier tema, para eso la carpeta de Recursos tiene que tener un apartado para cualquier tipo de texto, pero claro, no es lo mismo recuperar conocimiento que Aurora guarda de conversaciones que recuperar conocimiento de este tipo (más extenso y en bruto) por lo que Aurora debe ser capaz de recuperar conocimiento de ambos tipos, y debe ser capaz de diferenciarlos y utilizarlos adecuadamente.

[COMPLETADA] Cada vez que Aurora genera una respuesta, se tiene que imprimir en una carpeta logs un ficheros de logs (máximo acumular 10 ficheros de logs) con todo el contexto que Aurora ha utilizado hasta ese momento, para saber que se le está metiendo por contexto en cada iteracion de la conversación

[COMPLETADA] Permitir desde un fichero de configuración especificar manualmente los parámetros del modelo de lenguaje (todos)

[COMPLETADA] Documentar el algoritmo de RAG dentro de un txt dentro de una nueva carpeta documentacion de tal manera que expliques el algoritmo de RAG de forma sencilla y luego de forma más técnica

[COMPLETADA] Al momento de querer recuperar información de conocimiento de Aurora, la forma de responder debe ser diferente, Aurora con la información que recupera del conocimiento siempre debe responder de forma más extendida a la pregunta o cuestión que el usuario le propone, ahora mismo contesta de forma muy simple superficial a esas cuestiones, eso está bien cuando la información que recupera son recuerdos o memoria, pero no cuando recupera conocimiento, la manera de responder debe ser diferente

[COMPLETADA] El modelo tiende a hacer muchas preguntas al final de cada generación, a veces me gusta que haga esto, pero no todo el rato, quiero que consigas que deje de hacer tantas preguntas al final de cada generación, ya que esto se siente antinatural

[COMPLETADA] La información de conversaciones anteriores no debe cargarse por defecto al iniciar el programa

[COMPLETADA] Quiero otra carpeta de logs_pensamientos que guarde el prompt que generó el pensamiento de Aurora, o el prompt que generó la nueva memoria a largo plazo, y que se distingan entre logs_respuesta, logs_pensamientos

[COMPLETADA] Distinguir con colores el nombre de Tú y Aurora en la terminal

[COMPLETADA] Ahora mismo el sistema de memoria de Aurora es muy simple, se limita a guardar recuerdos de conversaciones pasadas, y conocimiento general, pero no tiene en cuenta el contexto de la conversación, ni la intención del usuario, ni la relevancia de la información, por lo que a veces recupera información que no es relevante para la conversación, o recupera información de forma superficial, quiero que mejores el sistema de memoria de Aurora para que sea capaz de recuperar información de forma más inteligente y relevante, además de que tenga en cuenta el contexto de la conversación, y la intención del usuario, y que sea capaz de diferenciar entre recuerdos de conversaciones pasadas y conocimiento general, y que sea capaz de utilizarlos adecuadamente.

[TAREA] Cada vez que se inicie el programa Aurora quiero que se cargue la última conversación anterior, y que se muestre en la terminal como si fuera una conversación normal, para que Aurora sepa que ha pasado en la conversación anterior