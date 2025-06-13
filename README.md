# laiers

Add your description here

## Project Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd laiers
    ```

2.  **Install dependencies:**
    To install all production dependencies:
    ```bash
    uv sync
    ```
    To install all dependencies, including development tools like `pytest` and `black`:
    ```bash
    uv sync --extra dev
    ```

3.  **Run the application (example):**
    ```bash
    uv run python main.py
    ```