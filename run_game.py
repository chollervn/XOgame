from __future__ import annotations

import socket
import threading
import webbrowser

import uvicorn


def find_available_port(start_port: int = 8000, attempts: int = 20) -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available port found in range 8000-8019")


def open_browser(url: str) -> None:
    webbrowser.open(url, new=2)


def main() -> None:
    port = find_available_port()
    url = f"http://127.0.0.1:{port}"

    print("Starting XO AI server...", flush=True)
    print(f"Open: {url}", flush=True)

    timer = threading.Timer(1.0, open_browser, args=(url,))
    timer.daemon = True
    timer.start()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
