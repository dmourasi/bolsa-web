"""Command-line entry point for running the web platform locally."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="bolsa-web", description="Run the bolsa web platform locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Address to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()

    uvicorn.run("bolsa_web.web.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
