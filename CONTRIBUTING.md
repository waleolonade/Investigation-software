# Contributing to LEIP

Thank you for your interest in contributing to the Law Enforcement Intelligence Platform (LEIP)! We welcome contributions from developers, researchers, and security analysts.

---

## 🛠️ Development Environment Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/waleolonade/Investigation-software.git
    cd Investigation-software
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r leip/requirements.txt
    ```

4.  **Set Up Environment**:
    Copy `leip/.env.example` to `leip/.env` and adjust the variables for your local database and systems.

---

## 📂 Project Structure

*   `leip/app/`: Core backend logic (FastAPI, database models, CRUD, and AI util wrappers).
*   `leip/config/`: App configuration classes and default configurations.
*   `leip/frontend/`: User interface screens (Streamlit app dashboard).
*   `leip/tests/`: Diagnostic unit and integration test suites.

---

## 🚦 Guidelines & Coding Standards

### Python Style & Quality
We adhere to `PEP 8` standards. To verify your code style before committing:
```bash
# Run lint check
flake8 leip/app

# Format files
black leip/app
```

### Database Development
*   Always use UUID primary keys via the `BaseModel` abstract class defined in `leip/app/models.py`.
*   Ensure every model inherits from `BaseModel` to benefit from automatic soft-deletes, timestamp tracking, and version increments.
*   If changing database schemas, update both `leip/app/models.py` and `leip/app/schemas.py` synchronously.

---

## 🧪 Testing

Ensure all tests pass before making pull requests:
```bash
pytest leip/tests/
```
Ensure you have appropriate mock files or environment variables configured for integration tests.

---

## 🔀 Git Workflow

1.  Create a branch from `main`:
    ```bash
    git checkout -b feature/your-feature-name
    ```
2.  Commit changes with a clear and descriptive commit message.
3.  Push your branch to your origin fork:
    ```bash
    git push origin feature/your-feature-name
    ```
4.  Open a Pull Request describing the changes, tests executed, and design rationale.
