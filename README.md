# YeastRegulatoryDB

A Django app which defines a database and API to data related to yeast gene regulation

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![CI](https://github.com/cmatKhan/yeastregulatorydb/actions/workflows/ci.yml/badge.svg)](https://github.com/cmatKhan/yeastregulatorydb/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/cmatKhan/yeastregulatorydb/graph/badge.svg?token=5DO8PKVWME)](https://codecov.io/gh/cmatKhan/yeastregulatorydb)

License: GPLv3

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

```bash
  python manage.py createsuperuser
```

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

```bash
  mypy yeastregulatorydb
```

#### mypy caveats

- there is an issue accessing `Models.objects` that is unresolved. See
  [issue 1684](https://github.com/typeddjango/django-stubs/issues/1684). I
  choose to resolve this by ignoring the attr-defined error when accessing
  `Model.objects` (see any viewset for an example). Note that in cases where
  a custom manager is defined, I use _default_manager
  ([see django docs](https://docs.djangoproject.com/en/4.2/topics/db/managers/#django.db.models.Model._default_manager)). This raises a "accessing private method" warning in pylint,
  which is also ignored.

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

```bash
  coverage run -m pytest
  coverage html
  open htmlcov/index.html
```

#### Running tests with pytest

```bash
  pytest
```

**NOTE**: if major changes are made to the database, it may be necesary to
remove `--reuse-db` from the `addopts` key of the pytest section of
`pyproject.toml`. It can be added back after a run without it.

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd yeastregulatorydb
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd yeastregulatorydb
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd yeastregulatorydb
celery -A config.celery_app worker -B -l info
```

## Github CI

To run the CI that is in this repo, you need to transform the `.envs` directory
into a binary string and save it as a secret. This can be done like so:

```bash
tar -czvf envs.tar.gz .envs
base64 envs.tar.gz > .tmp.txt
```

Then, go to the settings of the repo, and add a secret called `ENV_FILE` with
the string in .tmp.txt. Make sure that and the .tar.gz does not get pushed to
git.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

## Using cookiecutter to re-create the project

I am using version 2023.12.06 and set the following options:

```raw
➜  code cookiecutter https://github.com/cookiecutter/cookiecutter-django
You've downloaded /home/oguzkhan/.cookiecutters/cookiecutter-django before. Is
it okay to delete and re-download it? [y/n] (y): y
  [1/27] project_name (My Awesome Project): YeastRegulatoryDB
  [2/27] project_slug (yeastregulatorydb):
  [3/27] description (Behold My Awesome Project!): A Django app which defines a database and API to data related to yeast gene regulation
  [4/27] author_name (Daniel Roy Greenfeld): Chase Mateusiak
  [5/27] domain_name (example.com): example.com
  [6/27] email (chase-mateusiak@example.com): chasem@wustl.edu
  [7/27] version (0.1.0): 0.0.0dev
  [8/27] Select open_source_license
    1 - MIT
    2 - BSD
    3 - GPLv3
    4 - Apache Software License 2.0
    5 - Not open source
    Choose from [1/2/3/4/5] (1): 3
  [9/27] Select username_type
    1 - username
    2 - email
    Choose from [1/2] (1): 1
  [10/27] timezone (UTC): America/Chicago
  [11/27] windows (n): n
  [12/27] Select editor
    1 - None
    2 - PyCharm
    3 - VS Code
    Choose from [1/2/3] (1): 3
  [13/27] use_docker (n): y
  [14/27] Select postgresql_version
    1 - 15
    2 - 14
    3 - 13
    4 - 12
    5 - 11
    6 - 10
    Choose from [1/2/3/4/5/6] (1): 1
  [15/27] Select cloud_provider
    1 - AWS
    2 - GCP
    3 - Azure
    4 - None
    Choose from [1/2/3/4] (1): 1
  [16/27] Select mail_service
    1 - Mailgun
    2 - Amazon SES
    3 - Mailjet
    4 - Mandrill
    5 - Postmark
    6 - Sendgrid
    7 - SendinBlue
    8 - SparkPost
    9 - Other SMTP
    Choose from [1/2/3/4/5/6/7/8/9] (1): 2
  [17/27] use_async (n): y
  [18/27] use_drf (n): y
  [19/27] Select frontend_pipeline
    1 - None
    2 - Django Compressor
    3 - Gulp
    4 - Webpack
    Choose from [1/2/3/4] (1): 1
  [20/27] use_celery (n): y
  [21/27] use_mailpit (n): n
  [22/27] use_sentry (n): n
  [23/27] use_whitenoise (n): y
  [24/27] use_heroku (n): n
  [25/27] Select ci_tool
    1 - None
    2 - Travis
    3 - Gitlab
    4 - Github
    5 - Drone
    Choose from [1/2/3/4/5] (1): 4
  [26/27] keep_local_envs_in_vcs (y): n
  [27/27] debug (n): n
```

## notes

- See callingcardsbackground for use of the serializer context. This is useful for
  passing additional arguments to the validation steps in the serializer

- See callingcardsbackground or binding to see how to use transaction to ensure that
  the instance/database are ready before kicking off celery tasks

- to use the celery retry functionality, add the following decorator:

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def my_tast(self, arg1, arg2):
    try:
        # do something
    except Exception as exc:
        raise self.retry(exc=exc)
```