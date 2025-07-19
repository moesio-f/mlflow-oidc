"""MLFlow using OIDC."""

import asyncio
import threading
import time
import webbrowser

import click
import requests
import uvicorn
from fastapi import FastAPI, Request, Response

from .config import CONFIG as config
from .config import OIDC_CLIENT as client


@click.command("mlflow_app.ui", help="Access a remote MLFlow UI locally.")
@click.option(
    "--port",
    type=int,
    default=5000,
    help="Local port to run MLFlow UI.",
)
def run(port: int = 5000):
    """Start the MLFlow UI from
    the remote tracking server.
    """
    if not client.is_logged:
        client.login()
    client.refresh()
    app = FastAPI(openapi_url=None)

    @app.get("/{fp:path}")
    @app.head("/{fp:path}")
    @app.post("/{fp:path}")
    @app.put("/{fp:path}")
    @app.patch("/{fp:path}")
    @app.delete("/{fp:path}")
    def proxied_response(fp, request: Request):
        # Get actual response from remote URL
        response = requests.request(
            method=request.method,
            url=str(request.url).replace(
                str(request.base_url), config.MLFLOW_REMOTE_TRACKING_URL
            ),
            headers={
                "Authorization": f"Bearer {client.user.access_token.encoded}",
                **request.headers,
            },
            data=asyncio.run(request.body()),
            cookies=request.cookies,
            allow_redirects=False,
        )
        return Response(
            response.content,
            response.status_code,
            response.headers,
        )

    # Open tab after a small delay (should be up)
    threading.Thread(target=lambda: _open_tab_after(f"http://localhost:{port}")).start()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )


def _open_tab_after(url: str, seconds: float = 0.5):
    """Open a new tab after some seconds.

    :param url: url to open in new tab.
    :param seconds: seconds to wait before opening.
    """
    time.sleep(seconds)
    webbrowser.open_new_tab(url)


if __name__ == "__main__":
    run()
