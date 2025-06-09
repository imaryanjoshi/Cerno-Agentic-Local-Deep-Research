# Contributing to Cerno

Thank you for considering to contribute to Cerno! We welcome contributions of all kinds—bug reports, documentation improvements, new features, or community engagement.

## Getting Started

1. **Fork the Repository**
   Click the "Fork" button on the top-right of the Cerno GitHub page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/<your-username>/cerno-ai-workspace.git
   cd cerno-ai-workspace
   ```

3. **Create a Feature Branch**

   ```bash
   git checkout -b feat/my-new-feature
   ```

4. **Set Up Your Environment**

   ```bash
   # Copy and configure .env
   cp .env.example .env
   # Activate venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate     # Windows
   # Install dependencies
   pip install -r requirements.txt
   npm install
   ```

5. **Run Tests & Linting**

   ```bash
   # Backend tests
   pytest

   # Frontend checks
   npm run lint
   npm run test
   ```

6. **Make Your Changes**
   Develop your feature or bugfix in the new branch. Follow the existing code style and include tests where appropriate.

7. **Commit & Push**

   ```bash
   git add .
   git commit -m "feat: description of feature"
   git push origin feat/my-new-feature
   ```

8. **Open a Pull Request**
   Go to your fork on GitHub and click "Compare & pull request". Provide a clear title and description of your changes.

---

## Code Style & Guidelines

* **Language**: Python 3.10+, JavaScript/TypeScript (ES6+), Tailwind CSS.
* **Formatting**: Use [Black](https://github.com/psf/black) for Python and [Prettier](https://prettier.io/) for JS/CSS.
* **Linting**: Adhere to ESLint rules for the frontend and Flake8 for the backend.
* **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`).

---

## Reporting Issues

1. **Search Existing Issues**
   Ensure your bug or feature request doesn’t already exist.
2. **Open a New Issue**
   Choose the correct template (bug report or feature request) and provide:

   * A descriptive title.
   * Detailed reproduction steps.
   * Expected vs. actual behavior.
   * Environment details (OS, versions, config).

---

## Community Code of Conduct

Please adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an inclusive and respectful community.

Thank you for helping make Cerno better! 🚀
