from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Servidor local para EMS 3D Model Editor."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host de escucha.")
    parser.add_argument(
        "--port", type=int, default=8000, help="Puerto HTTP para el editor."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"Sirviendo {root} en http://{args.host}:{args.port}")
    print("Pulsa Ctrl+C para detener el servidor.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
