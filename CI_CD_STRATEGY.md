# CI/CD Strategy Document

This document outlines the architecture and strategy for the Continuous Integration and Continuous Deployment (CI/CD) pipeline implemented in this repository. The primary goal is to establish a robust, secure, and efficient automated workflow that ensures code quality and container security.

## 1. Technology Stack

The following tools have been standardized for dependency management and code quality:

*   **Dependency Manager**: **Poetry** is the definitive tool for managing Python dependencies. It provides deterministic builds and a clear project structure via the `pyproject.toml` file. The legacy `requirements.txt` has been removed to enforce a single source of truth.
*   **Linters & Formatters**: Code quality is enforced using a suite of tools managed by **pre-commit**. This includes:
    *   **Ruff**: For high-speed linting and formatting.
    *   **Mypy**: For static type checking to catch type-related errors.
    *   **pre-commit-hooks**: For general repository hygiene, such as fixing trailing whitespace and checking YAML files.

## 2. Foundational Improvements

To support a modern CI/CD pipeline, the following foundational files were created or optimized:

*   **`.pre-commit-config.yaml`**: A new configuration was added to automate code quality checks before commits. This ensures that all code pushed to the repository adheres to consistent standards.
*   **`Dockerfile`**: A new, multi-stage `Dockerfile` was implemented.
    *   **Builder Stage**: This stage uses a standard Python image to install dependencies with Poetry and exports them into a `requirements.txt` file.
    *   **Runtime Stage**: This stage uses a lean `python-slim` base image, installs dependencies from the exported `requirements.txt` using `pip`, and creates a non-root user (`appuser`) to run the application, adhering to security best practices. The full Poetry toolchain is not included in the final image, keeping it lightweight.
*   **`.dockerignore`**: A comprehensive `.dockerignore` file was added to minimize the Docker build context. This excludes version control directories, virtual environments, caches, and documentation, resulting in faster and more secure builds.

## 3. Workflow Architecture

The CI/CD pipeline is defined in two separate GitHub Actions workflows: `ci.yml` and `docker.yml`.

### `ci.yml` (Linting & Testing)

This workflow validates code quality and correctness. It is triggered on every `push` and `pull_request` to the `main` and `develop` branches.

*   **Job Structure**:
    1.  **`lint`**: This job runs first and uses `pre-commit/action` to execute all configured linters and formatters. It provides a fast feedback loop on code style and quality.
    2.  **`test`**: This job runs only after the `lint` job succeeds. It is responsible for running the test suite.

*   **Testing and Coverage Strategy**:
    *   **Matrix Testing**: Tests are executed across a matrix of operating systems (`ubuntu-latest`, `macos-latest`, `windows-latest`) and Python versions (`3.11`, `3.12`) to ensure broad compatibility.
    *   **Dependency Caching**: The `actions/setup-python` action is configured to cache Poetry dependencies, significantly speeding up subsequent builds.
    *   **Code Coverage**: Test coverage is measured using `pytest-cov`, and the results are uploaded to **Codecov**. Unique flags (`${{ matrix.os }}-py${{ matrix.python-version }}`) are used for each job in the test matrix to prevent coverage reports from being overwritten.

### `docker.yml` (Docker Build & Scan)

This workflow builds the Docker image and scans it for vulnerabilities. It is also triggered on `push` and `pull_request` events.

*   **Workflow Steps**:
    1.  **Authentication**: Securely logs into Docker Hub to prevent rate-limiting issues. This step is skipped for forks, which do not have access to secrets.
    2.  **Setup Buildx**: Initializes Docker Buildx to enable advanced building features like caching.
    3.  **Build and Cache**: Uses `docker/build-push-action` to build the Docker image. It leverages the GitHub Actions cache (`type=gha`) to store and reuse image layers, speeding up build times. The image is loaded locally for scanning but is not pushed during the CI run.
    4.  **Security Scanning**: Uses **Trivy** (`aquasecurity/trivy-action`) to scan the newly built image for vulnerabilities. The workflow will fail if any `CRITICAL` or `HIGH` severity vulnerabilities are detected.

## 4. Security Measures

Security is a core principle of this CI/CD pipeline. The following measures have been implemented:

*   **Action Pinning**: All third-party GitHub Actions are pinned to their full-length commit SHA. This prevents the execution of malicious or unstable code from a mutable tag (e.g., `@v3`).
*   **Principle of Least Privilege (PoLP)**: Workflows are configured with `permissions: contents: read` at the top level, granting only the minimum permissions required. More permissive tokens are only requested for specific steps when necessary.
*   **Non-Root Container**: The runtime stage of the `Dockerfile` creates and switches to a non-root user (`appuser`), reducing the potential impact of a container breakout vulnerability.
*   **Vulnerability Scanning**: The `docker.yml` workflow includes a mandatory Trivy scan that fails the build if critical or high-severity vulnerabilities are found in the container image.
*   **Secret Management**: The Docker Hub login credentials are stored as encrypted secrets in GitHub and are only used in a conditional step, ensuring they are not exposed in logs or accessible to forks.
