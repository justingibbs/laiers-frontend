# laiers

## Project Purpose/Goal
An agent-powered job matching platform that revolutionizes hiring by identifying candidates with the essential soft skills needed to excel in GenAI-transformed workplaces. Rather than focusing on traditional hard skills that AI increasingly automates, the platform evaluates and matches based on uniquely human capabilities—creative problem-solving, emotional intelligence, adaptability, critical thinking, and collaborative leadership—that become more valuable as AI handles routine tasks.

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

3. New run
```
uv sync
```

```
uv run -- uvicorn main:app --reload --port 8000
```

3.  **Run the application (example):**
    ```bash
    uv run python main.py
    ```