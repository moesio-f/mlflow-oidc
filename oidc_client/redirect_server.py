"""Simple redirect server
to receive tokens from OIDC
provider.
"""

import re
import socket

import requests


class RedirectServer:
    """Simple HTTP server to handle
    OIDC redirects.
    """

    def __init__(
        self,
        token_endpoint_url: str,
        client_id: str,
        host: str = "127.0.0.1",
        port: int = 0,
    ):
        self._token_endpoint = token_endpoint_url
        self._client_id = client_id
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((host, port))
        self._socket.listen()
        self._closed = False

    @property
    def host(self) -> str:
        return self._socket.getsockname()[0]

    @property
    def port(self) -> int:
        return self._socket.getsockname()[1]

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def read_token(self) -> dict:
        assert not self._closed, "Redirect server are single-use."
        conn, addr = self._socket.accept()
        with conn:
            # Fetch Authorization Token (OAuth2)
            data = "".join(b.decode() for b in self._read_all(conn))
            m = re.match(r"GET.*&code=(?P<code>.+)[ &].+", data)
            if m is None:
                self._send_internal_error(
                    conn, f"Unable to find authorization token: {data}"
                )

            # Exchange authorization code to ID+Access
            response = requests.post(
                self._token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": m.group("code"),
                    "client_id": self._client_id,
                    "redirect_uri": self.url,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                self._send_internal_error(
                    conn,
                    f"Failed to obtain ID/Access tokens: {e}\n\n"
                    f"Auth Response: {data}\n\n"
                    f"Auth Code: {m.group('code')}",
                )

                raise

            data = response.json()
            conn.sendall(
                "HTTP/1.1 200 OK\n\nYou are logged!\n"
                "Feel free to close this window.".encode()
            )

        # Close server
        self._socket.close()
        self._closed = True
        return data

    @staticmethod
    def _send_internal_error(conn: socket.socket, message: str):
        conn.sendall(f"HTTP/1.1 500 Internal Server Error\n\n{message}".encode())

    @staticmethod
    def _read_all(conn: socket.socket, timeout: float = 0.5) -> list[bytes]:
        """Read all data from the connection.

        :param conn: connection.
        :param timeout: timeout between reads.
        :return: chunks read from the connection.
        """
        buffer = []
        conn.settimeout(timeout)
        while True:
            try:
                data = conn.recv(1024)
            except socket.timeout:
                break

            if not data:
                break

            buffer.append(data)
        conn.settimeout(None)
        return buffer
