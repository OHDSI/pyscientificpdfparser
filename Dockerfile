# ---- Builder Stage ----
# This stage installs dependencies and builds the requirements file.
FROM python:3.12-slim as builder

# Prevent Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal without buffering.
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install Poetry, the dependency manager.
# We use pipx to install it in an isolated environment, which is a best practice.
RUN pip install pipx
RUN pipx install poetry

# Copy the dependency definition files.
COPY pyproject.toml poetry.lock* ./

# Install project dependencies using Poetry.
# --no-root: Do not install the project itself, only dependencies.
# --no-interaction: Do not ask any interactive questions.
# --only main: Only install production dependencies.
# We need to generate a requirements.txt, so we actually need dev dependencies to run the export.
# Let's install all dependencies first.
RUN poetry install --no-interaction --no-root

# Export the production dependencies to a requirements.txt file.
# This file will be used in the final, lean image.
# Using --without-hashes can improve compatibility in some environments.
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# ---- Final Stage ----
# This stage creates the final, lean production image.
FROM python:3.12-slim

# Prevent Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal without buffering.
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Create a non-root user ('appuser') and group ('appgroup') to run the application.
# This is a critical security best practice.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy the exported requirements.txt from the builder stage.
COPY --from=builder /app/requirements.txt .

# Install the production dependencies using pip.
# --no-cache-dir: Reduces image size by not storing the download cache.
# --user: Installs packages for the current user, which is root at this stage.
# We will install system-wide and then switch user.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container.
COPY ./src ./src
COPY ./run.py .

# Change the ownership of the application directory to the non-root user.
# This ensures the application runs with the least privileges required.
RUN chown -R appuser:appgroup /app

# Switch the user context to the non-root user.
USER appuser

# Set the entrypoint for the container.
# This command will be executed when the container starts.
# It runs the main CLI script defined in the project.
ENTRYPOINT ["python", "run.py"]