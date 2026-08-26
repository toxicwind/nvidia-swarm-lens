#!/usr/bin/env python3
"""Simple HTTP proxy daemon for browser automation tunneling."""
import socket, threading, select, sys, os

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 18888
BUFFER_SIZE = 4096

def handle_client(client_socket):
    try:
        request = client_socket.recv(BUFFER_SIZE)
        if not request:
            client_socket.close()
            return

        # Parse CONNECT or GET/POST
        first_line = request.split(b'\r\n')[0].decode('utf-8', errors='ignore')

        if first_line.startswith("CONNECT"):
            # HTTPS tunnel
            parts = first_line.split()
            if len(parts) >= 2:
                target = parts[1]
                host, port = target.split(":")
                port = int(port)

                try:
                    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server.connect((host, port))
                    client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

                    # Bidirectional relay
                    while True:
                        readable, _, _ = select.select([client_socket, server], [], [], 30)
                        if not readable:
                            break
                        for sock in readable:
                            data = sock.recv(BUFFER_SIZE)
                            if not data:
                                break
                            (server if sock is client_socket else client_socket).sendall(data)
                except Exception as e:
                    client_socket.sendall(f"HTTP/1.1 502 Bad Gateway\r\n\r\n{e}".encode())
        else:
            # HTTP proxy
            lines = first_line.split()
            if len(lines) >= 2:
                url = lines[1]
                if url.startswith("http://"):
                    host_start = url.find("://") + 3
                    path_start = url.find("/", host_start)
                    if path_start == -1:
                        path_start = len(url)
                    host_port = url[host_start:path_start]
                    if ":" in host_port:
                        host, port = host_port.split(":")
                        port = int(port)
                    else:
                        host, port = host_port, 80

                    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server.connect((host, port))
                    # Rewrite request to remove full URL
                    new_request = request.replace(url.encode(), url[path_start:].encode() or b"/")
                    server.sendall(new_request)

                    while True:
                        data = server.recv(BUFFER_SIZE)
                        if not data:
                            break
                        client_socket.sendall(data)
    except Exception as e:
        pass
    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(100)
    print(f"[PROXY] Daemon listening on {PROXY_HOST}:{PROXY_PORT}", flush=True)

    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client,), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
