import os
import json
from huggingface_hub import hf_hub_download
import llama_cpp
from llama_cpp import Llama

class MotorLLM:
    def __init__(self, config_path="config.json", status_callback=None):
        self.config_path = config_path
        self.status_callback = status_callback
        self.config = self._load_or_create_config()
        
        # Guardamos datos base
        self.repo_id = self.config["model"]["repo_id"]
        self.filename = self.config["model"]["filename"]
        self.model_path = os.path.join("models", self.filename)
        self.llm = None
        self._download_and_load_model()

    def _emit_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
        
    def _load_or_create_config(self):
        default_config = {
            "model": {
                "repo_id": "bartowski/gemma-2-2b-it-GGUF",
                "filename": "gemma-2-2b-it-Q4_K_M.gguf"
            },
            "initialization": {
                "n_ctx": 4096,
                "n_threads": None,
                "n_gpu_layers": -1
            },
            "generation": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 512,
                "repeat_penalty": 1.1
            },
            "thought": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 150,
                "repeat_penalty": 1.1
            },
            "kv_cache": {
                "type_k": None,
                "type_v": None
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if not isinstance(config, dict):
                    return default_config

                # Compatibilidad hacia atrás con config antiguas.
                config.setdefault("model", {})
                config.setdefault("initialization", {})
                config.setdefault("generation", {})
                config.setdefault("thought", {})
                config.setdefault("kv_cache", {})

                for seccion, valores in default_config.items():
                    if not isinstance(valores, dict):
                        continue
                    destino = config.setdefault(seccion, {})
                    if isinstance(destino, dict):
                        for clave, valor in valores.items():
                            destino.setdefault(clave, valor)

                return config
            except Exception as e:
                self._emit_status(f"Error cargando config.json, usando valores por defecto: {e}")
                return default_config
        else:
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)
                self._emit_status("Archivo config.json creado con valores por defecto.")
            except Exception as e:
                self._emit_status(f"Error creando config.json: {e}")
            return default_config

    def _resolver_tipo_kv(self, valor):
        if valor is None:
            return None

        if isinstance(valor, int):
            return valor

        if isinstance(valor, str):
            nombre = valor.strip().upper()
            if not nombre:
                return None
            if not nombre.startswith("GGML_TYPE_"):
                nombre = f"GGML_TYPE_{nombre}"
            if hasattr(llama_cpp, nombre):
                return int(getattr(llama_cpp, nombre))

            self._emit_status(
                f"Tipo de KV cache no reconocido: {valor}. Se usará el valor por defecto del backend."
            )
            return None

        self._emit_status(
            f"Tipo de KV cache inválido ({type(valor).__name__}). Se usará el valor por defecto del backend."
        )
        return None
        
    def _download_and_load_model(self):
        os.makedirs("models", exist_ok=True)
        if not os.path.exists(self.model_path):
            self._emit_status(f"Descargando el modelo {self.filename} desde {self.repo_id}...")
            self._emit_status("Esto puede tardar unos minutos dependiendo de la conexión a internet.")
            hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                local_dir="models",
                local_dir_use_symlinks=False
            )
            self._emit_status("Descarga completada.")
        else:
            self._emit_status(f"Modelo {self.filename} encontrado localmente en models/")

        self._emit_status("Cargando modelo en memoria...")
        tipo_k = self._resolver_tipo_kv(self.config.get("kv_cache", {}).get("type_k"))
        tipo_v = self._resolver_tipo_kv(self.config.get("kv_cache", {}).get("type_v"))
        if tipo_k is not None or tipo_v is not None:
            self._emit_status(
                f"Cuantización de KV cache activada (type_k={self.config.get('kv_cache', {}).get('type_k')}, "
                f"type_v={self.config.get('kv_cache', {}).get('type_v')})"
            )
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.config["initialization"]["n_ctx"],
            n_threads=self.config["initialization"]["n_threads"],
            n_gpu_layers=self.config["initialization"]["n_gpu_layers"],
            type_k=tipo_k,
            type_v=tipo_v,
            verbose=False
        )
        self._emit_status("Modelo cargado correctamente.")

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
        max_t = self.config["generation"]["max_tokens"] if max_tokens == 512 else max_tokens
        response = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_t,
            temperature=self.config["generation"]["temperature"],
            top_p=self.config["generation"]["top_p"],
            repeat_penalty=self.config["generation"]["repeat_penalty"]
        )
        
        return response["choices"][0]["message"]["content"]

    def generate_thought(self, prompt, max_tokens=150):
        # Utilidad para generar pensamientos internos (summarization, extraction, etc.) de un solo turno (zero-shot)
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        max_t = self.config["thought"]["max_tokens"] if max_tokens == 150 else max_tokens
        response = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_t,
            temperature=self.config["thought"]["temperature"],
            top_p=self.config["thought"]["top_p"],
            repeat_penalty=self.config["thought"]["repeat_penalty"]
        )
        
        return response["choices"][0]["message"]["content"]
