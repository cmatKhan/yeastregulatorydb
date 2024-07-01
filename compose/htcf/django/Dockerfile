# define an alias for the specific python version used in this file.
FROM python:3.11.7-slim-bullseye AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=htcf

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  libpq-dev \
  zlib1g-dev \
  libbz2-dev \
  liblzma-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
  -r ${BUILD_ENVIRONMENT}.txt

# AWS CLI and maintenance scripts
FROM garland/aws-cli-docker:1.16.140 AS aws

COPY ./compose/production/aws/maintenance /usr/local/aws/maintenance
COPY ./compose/production/postgres/maintenance/_sourced /usr/local/aws/maintenance/_sourced

RUN chmod +x /usr/local/aws/maintenance/*

RUN mv /usr/local/aws/maintenance/* /usr/local/aws \
    && rmdir /usr/local/aws/maintenance

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=htcf
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Create django user and group
RUN addgroup --system django \
    && adduser --system --ingroup django django

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

# Copy AWS CLI and maintenance scripts to a different directory
COPY --from=aws /usr/local/aws /usr/local/aws

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY --chown=django:django ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY --chown=django:django ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

USER django

# Run the original Django command
RUN DATABASE_URL="" \
  CELERY_BROKER_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  python manage.py compilemessages

ENTRYPOINT ["/entrypoint"]
