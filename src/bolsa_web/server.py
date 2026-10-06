"""Command-line entry point for running the web platform locally."""

import argparse
import os

import uvicorn


def main() -> None:
    # Hosting platforms inject PORT and need HOST=0.0.0.0; local runs keep the defaults.
    parser = argparse.ArgumentParser(prog="bolsa-web", description="Run the bolsa web platform.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Address to bind")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Port to listen on")
    args = parser.parse_args()

    uvicorn.run("bolsa_web.web.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
