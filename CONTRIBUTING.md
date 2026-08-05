# Contributing to RAGTUNE

Thank you for your interest in contributing to **RAGTUNE**! We welcome contributions from developers, researchers, and open-source enthusiasts.

---

## Code of Conduct

All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand our community standards.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing [GitHub Issues](https://github.com/sreeram0343/ragtune/issues) before opening a new issue.
- Use the **Bug Report** issue template.
- Provide a clear summary, steps to reproduce, environment details, and expected behavior.

### 2. Suggesting Features
- Open a **Feature Request** issue detailing the problem your feature solves and proposed API designs.

### 3. Submitting Pull Requests
1. Fork the repository and create a new feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Set up your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
3. Ensure all tests pass:
   ```bash
   pytest
   ```
4. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add new vector index provider`
   - `fix: resolve CORS header parsing on gateway`
   - `docs: update deployment architecture guide`
5. Push to your fork and submit a Pull Request.

---

## Testing & Quality Guidelines

- **Unit Tests**: All new features or bug fixes must include unit or integration tests in `tests/`.
- **Code Style**: Maintain clean code formatting and docstrings across Python and JavaScript files.
- **Backward Compatibility**: Ensure public API endpoints and database models preserve backward compatibility.
