# ---- Builder Stage ----
# This stage installs dependencies and prepares them for the runtime stage.
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages and for Tesseract
# We do this first to leverage Docker layer caching.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry using the official installer
# Pinning the version for reproducibility
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy only the files necessary for dependency installation
COPY pyproject.toml poetry.lock ./

# Install project dependencies
# --no-root: Don't install the project itself, only its dependencies.
# --only main: Install only main dependencies, excluding dev, etc.
# We export the dependencies to a requirements.txt file for the next stage.
RUN poetry install --no-root --no-interaction --no-ansi --only main && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes

# ---- Runtime Stage ----
# This is the final, lean image that will run the application.
FROM python:3.12-slim as runtime

WORKDIR /app

# Install Tesseract OCR, which is a runtime dependency for pytesseract
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the exported requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .

# Install the Python dependencies using pip, which is faster and lighter than Poetry
# We use --no-cache-dir to keep the image size small.
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy the application source code
COPY src/ /app/src/

# Set the entrypoint for the application's CLI
ENTRYPOINT ["python", "-m", "src.pyscientificpdfparser.cli"]
CMD ["--help"]
