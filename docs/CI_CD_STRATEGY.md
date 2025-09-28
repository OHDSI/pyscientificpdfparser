# CI/CD Strategy and Architecture

## 1. Overview

This document outlines the architecture and rationale behind the continuous integration and continuous delivery (CI/CD) pipeline for this repository. The primary goals of this setup are to ensure code quality, maintain security, and automate the build, test, and containerization processes efficiently.

The pipeline is designed to provide fast feedback to developers, enforce coding standards, and produce secure, production-ready artifacts.

## 2. Technology Stack and Rationale

The following tools have been selected to form the foundation of our development and CI/CD workflow:

-   **Dependency Management: Poetry**
    -   **Rationale:** `pyproject.toml` already specified Poetry as the dependency manager. It provides a robust, modern, and deterministic way to manage project dependencies and virtual environments. It is the single source of truth for all Python packages.

-   **Linting & Formatting: Ruff**
    -   **Rationale:** Ruff is an extremely fast, all-in-one tool that replaces the need for separate tools like `black`, `isort`, and `flake8`. Consolidating on Ruff simplifies the configuration, significantly speeds up the linting process, and ensures consistent code style across the project.

-   **Static Analysis: Mypy**
    -   **Rationale:** Mypy provides static type checking, which helps catch a wide range of bugs before runtime. It is configured to run in strict mode to enforce high-quality, type-safe code.

-   **Testing: Pytest**
    -   **Rationale:** The existing test suite is built on `pytest`. It is a powerful and flexible testing framework with a rich ecosystem of plugins, making it the standard for Python testing.

-   **Containerization: Docker**
    -   **Rationale:** Docker provides a consistent and reproducible environment for the application, simplifying development and deployment. The `Dockerfile` is optimized for security and efficiency.

-   **Vulnerability Scanning: Trivy**
    -   **Rationale:** Trivy is a comprehensive and easy-to-use vulnerability scanner for container images. It is integrated directly into our Docker build workflow to ensure that all images are scanned for known vulnerabilities before they can be considered for deployment.

## 3. Proactive Improvements Made

Several proactive improvements were made to modernize the repository, remove ambiguity, and establish best practices:

1.  **Consolidated Dependency Management:**
    -   The `requirements.txt` file was **deleted**. This was a source of conflicting dependency information and is now superseded entirely by `pyproject.toml`, which is managed by Poetry.

2.  **Modernized Linting and Formatting:**
    -   The `.pre-commit-config.yaml` was **refactored** to use `ruff` for both linting and formatting. This replaced `black`, `isort`, and `flake8`, resulting in a simpler, faster, and more unified developer experience.
    -   Legacy configuration files (`.flake8`, `.mypy.ini`) were **deleted** as their configurations are now managed within `pyproject.toml`.

3.  **Added Containerization Support:**
    -   A multi-stage `Dockerfile` was **created**. This ensures a lean, secure final image by separating the build environment from the runtime environment. The final image runs as a non-root user for enhanced security.
    -   A comprehensive `.dockerignore` file was **added** to minimize the Docker build context, which speeds up image builds and prevents sensitive information from being included in the image.

## 4. Workflow Architecture

The CI/CD pipeline is defined in two separate GitHub Actions workflow files located in `.github/workflows/`:

-   `ci.yml`: Handles continuous integration (linting and testing).
-   `docker.yml`: Handles Docker image building and security scanning.

### `ci.yml` (Lint & Test)

This workflow is structured for fast feedback and runs on every `push` and `pull_request` to the `main` and `develop` branches.

-   **Job 1: `lint`**
    -   **Purpose:** Provides immediate feedback on code quality and style.
    -   **Process:** This job runs first on an `ubuntu-latest` runner. It uses the `pre-commit/action` to execute all configured hooks (`ruff`, `mypy`, etc.). A failure here indicates a style or type error that must be fixed before proceeding.

-   **Job 2: `test`**
    -   **Purpose:** Ensures the application functions correctly across different environments.
    -   **Dependency:** This job `needs: [lint]`, meaning it will only run if the `lint` job succeeds.
    -   **Process:** It runs a test matrix across multiple operating systems (`ubuntu-latest`, `macos-latest`, `windows-latest`) and all supported Python versions (`3.10`, `3.11`, `3.12`).

### `docker.yml` (Build & Scan)

This workflow ensures that a valid and secure Docker image can always be built from the main branches.

-   **Job: `build-and-scan`**
    -   **Process:**
        1.  Sets up Docker Buildx for efficient builds.
        2.  Builds the Docker image using the multi-stage `Dockerfile`. On pull requests, the image is built for verification but **not pushed**. On pushes to `main` or `develop`, the image is pushed.
        3.  The built image is loaded into the local Docker daemon.
        4.  **Trivy** is used to scan the local image for vulnerabilities, failing the build if any `HIGH` or `CRITICAL` issues are found.

## 5. Testing Strategy

-   **Framework:** `pytest` is used to execute all tests.
-   **Execution:** Tests are run via `poetry run pytest`.
-   **Coverage:** Code coverage is collected during the test run and uploaded to [Codecov](https://codecov.io/). Reports are flagged with the operating system and Python version (`${{ matrix.os }}-py${{ matrix.python-version }}`) to provide detailed insights into coverage across all environments.
-   **Test Types:** The current test suite does not formally distinguish between unit and integration tests. The CI runs all tests together. A future improvement could be to separate these into distinct steps (e.g., using `pytest` markers) for more granular feedback.

## 6. Dependency Management and Caching

-   **Installation:** The `actions/setup-python` action is configured with `cache: 'poetry'`. This automatically handles the caching of downloaded dependencies, speeding up subsequent workflow runs.
-   **Environment Setup:** Poetry is installed using `pipx`, which is the recommended approach for installing Python command-line tools in isolated environments, preventing any potential conflicts.

## 7. Security Hardening

Security is a core principle of this CI/CD pipeline, implemented through the following measures:

-   **Least Privilege Principle (PoLP):** All workflow jobs are configured with `permissions: contents: read` by default, granting only the necessary permissions.
-   **Action Pinning:** All third-party GitHub Actions (e.g., `actions/checkout`, `docker/login-action`) are pinned to their full 40-character commit SHA. This prevents malicious actors from hijacking a mutable tag (like `@v4`) and injecting malicious code into the pipeline.
-   **Runner Hardening:** The `step-security/harden-runner` action is used as the first step in every job to monitor for anomalous network traffic, file writes, and process execution, providing an extra layer of defense against supply chain attacks.
-   **Non-Root Docker Container:** The `Dockerfile` is configured to run the application as a dedicated, non-root user (`appuser`), which is a critical security best practice to limit the blast radius of a potential container compromise.
-   **Vulnerability Scanning:** The `aquasecurity/trivy-action` is integrated into the `docker.yml` workflow to automatically scan every built image for known vulnerabilities. The workflow will fail if any `HIGH` or `CRITICAL` severity issues are discovered.
-   **Secure Docker Login:** The `docker/login-action` is configured to only attempt a login if the required `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are present, preventing failures in forked repositories where secrets are not available.

## 8. Docker Strategy

-   **Multi-Stage Builds:** The `Dockerfile` uses a multi-stage build pattern. The `builder` stage installs all dependencies (including dev dependencies) needed to create a `requirements.txt` file. The `final` stage is a lean production image that copies this `requirements.txt` and the application source code, installing only the necessary production dependencies. This results in a smaller, more secure final image.
-   **Build Caching:** The `docker/build-push-action` is configured to use the GitHub Actions cache (`type=gha`) to store Docker image layers. This significantly speeds up subsequent builds, as unchanged layers can be retrieved from the cache instead of being rebuilt.
-   **Verification, Not Pushing on PRs:** For pull requests, the Docker image is built and scanned but **not** pushed to a registry. This verifies that the `Dockerfile` is valid and the resulting image is secure without polluting the registry with transient images.

## 9. How to Run Locally

Developers can replicate the CI checks locally to ensure their changes will pass before pushing.

-   **Linting and Static Analysis:**
    -   First, install `pre-commit` and set up the hooks:
        ```bash
        pip install pre-commit
        pre-commit install
        ```
    -   Run all checks against all files:
        ```bash
        pre-commit run --all-files
        ```

-   **Running Tests:**
    -   Ensure you have Poetry installed and have created the virtual environment:
        ```bash
        poetry install --with dev
        ```
    -   Run the `pytest` suite:
        ```bash
        poetry run pytest
        ```
