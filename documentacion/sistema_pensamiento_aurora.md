# Sistema de Pensamiento y Memoria de Aurora

Este documento explica cómo funciona el innovador sistema de cognición interna de Aurora, diseñado para que no sea solo un chatbot que responde, sino una IA que reflexiona y recuerda.

## 1. Explicación Sencilla (Para todos)

Imagina que Aurora es como una persona real. Cuando hablas con ella, no solo te escucha y te responde al momento. Mientras conversáis, ella está haciendo dos cosas importantes en su cabeza:

1.  **Recordar (Recall)**: Antes de contestarte, echa un vistazo rápido a su "diario personal" para ver si ya le habías contado algo importante anteriormente (como tu nombre o tus gustos). Si encuentra algo, lo usa para que su respuesta sea más cercana y personal.
2.  **Reflexionar (Thought Generation)**: Después de darte una respuesta, se queda un momento pensando en lo que habéis hablado. Si cree que le has dicho algo digno de ser guardado para el futuro, lo apunta en su memoria.

Esto permite que Aurora "aprenda" de ti con el tiempo, haciendo que cada conversación sea única.

---

## 2. Detalles Técnicos

Desde un punto de vista de ingeniería, el sistema utiliza un **Bucle Cognitivo de Dos Fases** integrado en el ciclo de vida de la solicitud.

### Fase A: Proceso de Recall (Recuperación)
Ocurre **antes** de generar la respuesta final.
*   **Mecanismo**: El `GestorLLM` consulta al `GestorRecursos`.
*   **Funcionamiento**: Se extraen entradas del archivo `Memoria/memoria.json`. Actualmente se utilizan las entradas más recientes como contexto enriquecido, el cual se inyecta en el *System Prompt* del modelo Gemma 2.
*   **Inyección**: Los recuerdos se añaden como "Hechos conocidos sobre el usuario" para que el LLM tenga conocimiento persistente más allá de la ventana de contexto de la conversación actual.

### Fase B: Generación de Pensamiento (Memorización)
Ocurre **después** de entregar la respuesta al usuario.
*   **Acción Aleatoria**: Para simular un comportamiento orgánico y no saturar la memoria, Aurora decide mediante un factor de probabilidad (actualmente 50%) si procesar la información.
*   **Extracción de Conocimiento**: Si decide pensar, se lanza una petición especial al `MotorLLM` (instancia de Gemma 2 2B) con un prompt de **Extracción de Entidades y Hechos**.
*   **Persistencia**: El resultado de este pensamiento (p. ej., "Al usuario le gusta el café solo") se guarda en un array JSON persistente en disco.

### Componentes Involucrados
*   **`gestorLLM.py`**: Orquestador del bucle cognitivo y la lógica de decisión.
*   **`motorLLM.py`**: Proporciona el método `generate_thought` que usa una temperatura baja (0.3) para garantizar extracciones precisas y lógicas.
*   **`recursos.py`**: Gestiona la lectura y escritura atómica en el archivo `memoria.json`.

---
*Documentación generada para el Proyecto Aurora - Humanización de IA.*
