
# Set environment variables
ENV BUILD_ENVIRONMENT=production
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set work directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
    -r ${BUILD_ENVIRONMENT}.txt

# Copy the Django project
COPY . /usr/src/app/

# Start script for Celery Worker
COPY ./compose/production/django/celery/worker/start /start-celeryworker
RUN chmod +x /start-celeryworker

CMD ["/start-celeryworker"]
