# /Users/justingibbs/Projects/laiers/main.py
from fastapi import FastAPI
from nicegui import ui
# import sys # No longer needed for arg parsing here

print("DEBUG: main.py script started.")

# Create a FastAPI instance
app = FastAPI()
print("DEBUG: FastAPI app instance created.")

# Define a simple NiceGUI page
@ui.page('/')
def home_page():
    print("DEBUG: home_page route accessed/defined.")
    ui.label('Hello, FastAPI and NiceGUI!').classes('text-2xl')
    ui.button('Click me!', on_click=lambda: ui.notify('Button clicked!'))

# Integrate NiceGUI with the FastAPI app instance.
# This call modifies the `app` by adding NiceGUI's routes and middleware.
# It does NOT start the server itself when a FastAPI `app` is provided.
# The server (Uvicorn) will be started by `uv run`, which should pick up the `app` instance.
ui.run_with(app, title="Laiers App") # Removed host and port arguments
print("DEBUG: ui.run_with(app, title=...) called to integrate NiceGUI.")
print("DEBUG: FastAPI 'app' object is now configured. Uvicorn (via 'uv run') should serve it.")

# The `if __name__ == "__main__":` block for argument parsing and explicit server start
# has been removed. `uv run python main.py --host <host> --port <port>` will execute
# this script (thus configuring `app` with NiceGUI), and then `uv run` will find
# the `app` object and serve it using Uvicorn with the provided host and port.
