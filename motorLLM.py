import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

class MotorLLM:
    def __init__(self, repo_id="bartowski/gemma-2-2b-it-GGUF", filename="gemma-2-2b-it-Q4_K_M.gguf"):
        self.repo_id = repo_id
        self.filename = filename
        self.model_path = os.path.join("models", filename)
        self.llm = None
        self._download_and_load_model()
        
    def _download_and_load_model(self):
        os.makedirs("models", exist_ok=True)
        if not os.path.exists(self.model_path):
            print(f"Descargando el modelo {self.filename} desde {self.repo_id}...")
            print("Esto puede tardar unos minutos dependiendo de la conexión a internet.")
            hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                local_dir="models",
                local_dir_use_symlinks=False
            )
            print("Descarga completada.")
        else:
            print(f"Modelo {self.filename} encontrado localmente en models/")

        print("Cargando modelo en memoria...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=4096,  # Context window size
            n_threads=None, # Use default threads
            n_gpu_layers=-1, # Accelerate using Metal on Mac
            verbose=False
        )
        print("Modelo cargado correctamente.")

    def generate_response(self, system_prompt, history, max_tokens=512):
        # Format history into Gemma 2 format
        # Gemma 2 chat template does not support the 'system' role natively
        # We inject the system prompt into the first message of the context window
        messages = []
        for i, msg in enumerate(history):
            if i == 0 and msg["role"] == "user":
                messages.append({"role": "user", "content": f"{system_prompt}\n\n{msg['content']}"})
            elif i == 0:
                messages.append({"role": "user", "content": system_prompt})
                messages.append(msg)
            else:
                messages.append(msg)
        
        # Using the chat_completion API from llama_cpp
        response = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9
        )
        
        return response["choices"][0]["message"]["content"]
