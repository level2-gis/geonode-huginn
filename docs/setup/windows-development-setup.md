# Windows Development Setup

## 1. Overview

This document describes how to set up a local GeoNode development environment on Windows using Python, PostgreSQL/PostGIS and Visual Studio Code.

The environment is intended for developing and debugging the GeoNode application without deploying the complete production Docker stack.

The local setup uses:

- Windows 10/11
- Python 3.13
- GeoNode 5.1.0
- PostgreSQL 14 with PostGIS
- GDAL Windows wheels
- Visual Studio Code

GeoServer, Redis, Nginx and Celery are not part of the basic local setup described here.

## 2. Repositories and Git configuration

The local GeoNode repository is:

```text
C:\Users\<USERNAME>\VSCodeProjects\geonode
```

The repository uses two Git remotes:

| Remote | Repository |
|---|---|
| `origin` | `https://github.com/level2-gis/geonode.git` |
| `upstream` | `https://github.com/GeoNode/geonode.git` |

The local development branch is:

```text
development/geonode-5.1.0
```

This branch is based on the upstream GeoNode `5.1.0` tag and contains Windows-specific development changes.

### 2.1 Clone the repository

```powershell
cd C:\Users\<USERNAME>\VSCodeProjects

git clone https://github.com/level2-gis/geonode.git

cd geonode
```

### 2.2 Configure remotes

If the remotes are not already configured:

```powershell
git remote add upstream https://github.com/GeoNode/geonode.git
git remote set-url origin https://github.com/level2-gis/geonode.git
```

Check the configuration:

```powershell
git remote -v
```

### 2.3 Checkout the development branch

```powershell
git fetch origin
git checkout development/geonode-5.1.0
```

If the branch does not exist locally but is available remotely:

```powershell
git checkout -b development/geonode-5.1.0 origin/development/geonode-5.1.0
```

Verify the branch:

```powershell
git status
git log -1 --oneline
```

The development branch should remain separate from the production `master` branch.

## 3. Python environment

### 3.1 Install Python

Install Python 3.13 for Windows.

Verify the installation:

```powershell
python --version
```

The tested local environment used Python 3.13.2.

### 3.2 Create a virtual environment

From the GeoNode repository root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify that the virtual environment is active:

```powershell
python --version
where.exe python
```

The first Python executable should point to the repository's `.venv` directory.

### 3.3 Upgrade Python packaging tools

```powershell
python -m pip install --upgrade pip setuptools wheel
```

## 4. Install GeoNode dependencies

Install the local GeoNode project:

```powershell
pip install --no-build-isolation .
```

The project metadata is defined in `pyproject.toml`.

The Windows development branch includes operating-system-specific dependency configuration.

Important differences include:

- Windows uses `gdal-wheel`.
- Windows uses `python-magic-bin`.
- Linux-only dependencies such as `pylibmc`, `sherlock`, `uwsgi` and `pdok-geopackage-validator` are excluded where appropriate.
- NumPy uses a Windows-specific version constraint.

Some packages do not provide Windows wheels for the selected Python version. Do not attempt to install Linux-only packages as part of the standard Windows environment.

### 4.1 GDAL

The tested Windows environment uses:

```text
gdal-wheel==3.13.3
```

The Windows-specific GDAL configuration is implemented in `geonode/settings.py`.

It locates the GDAL DLL directory relative to the installed `osgeo` package.

Do not replace this configuration with hard-coded paths unless the GDAL installation layout changes.

### 4.2 Verify GIS dependencies

Check GDAL:

```powershell
python -c "from django.contrib.gis.gdal import GDAL_VERSION; print(GDAL_VERSION)"
```

Check GEOS:

```powershell
python -c "from django.contrib.gis.geos import Point; p=Point(1, 2); print(p)"
```

Check PyProj:

```powershell
python -c "from pyproj import Transformer; t=Transformer.from_crs(4326, 3794, always_xy=True); print(t.transform(15.0, 46.0))"
```

These tests verify that the main GIS libraries can be imported and used.

## 5. PostgreSQL and PostGIS

### 5.1 Install PostgreSQL

Install PostgreSQL 14 for Windows and enable the PostGIS extension.

The tested local environment used:

- PostgreSQL 14.6
- PostGIS 3.2.1
- Default PostgreSQL port: `5432`

Ensure that the PostgreSQL Windows service is running.

### 5.2 Create development databases

The local environment uses two databases:

| Database | Purpose |
|---|---|
| `geonode_dev` | GeoNode application database |
| `geonode_data_dev` | GeoNode data store |

A dedicated database role is used:

```text
geonode_dev
```

Create the role and databases using PostgreSQL administration tools.

Use a local development password and do not reuse production credentials.

Enable PostGIS in both databases:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Verify the extension:

```sql
SELECT PostGIS_Full_Version();
```

Run the verification in each database.

## 6. Environment configuration

GeoNode requires environment variables for database connections, application settings and other services.

The local environment uses a `.env` file in the repository root.

### 6.1 Create the local environment file

Create `.env` from the local environment template:

```powershell
Copy-Item .env_local .env
```

Review the local configuration and adjust the database connection settings.

The local configuration should use:

- PostgreSQL host: `localhost`
- PostgreSQL port: `5432`
- Database: `geonode_dev`
- Geodatabase: `geonode_data_dev`
- Database user: `geonode_dev`

Use local development credentials.

Never copy the production `.env` file into the Windows development environment.

The `.env` file is excluded from Git through `.gitignore`.

### 6.2 Load environment variables

The Django management command does not automatically load `.env` in this setup.

Use `python-dotenv` to load the environment file when running management commands:

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py check
```

This pattern should be used for the remaining Django management commands as well.

If a database password contains special characters and is included in a database URL, ensure that the password is URL-encoded correctly.

## 7. Initialize the database

### 7.1 Check Django configuration

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py check
```

The expected result is a successful system check.

### 7.2 Run migrations

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py migrate
```

This creates the required Django database tables.

### 7.3 Create a superuser

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py createsuperuser
```

Follow the interactive prompts.

Use a local development account.

## 8. Collect static files

Run:

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py collectstatic --noinput --clear
```

The static files are collected into the configured `STATIC_ROOT` directory.

Verify that the generated static files include the required GeoNode and MapStore assets.

The static output directory is excluded from Git.

## 9. Run the development server

Start the Django development server:

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open the application:

```text
http://127.0.0.1:8000/
```

Use the superuser account created earlier to log in.

Stop the development server with `Ctrl+C`.

## 10. Development environment limitations

The Windows setup is intended for GeoNode core development and does not reproduce the complete production infrastructure.

The following services are not included in the basic setup:

| Service | Local setup |
|---|---|
| Django | Local Python process |
| PostgreSQL/PostGIS | Local Windows service |
| GeoServer | Not configured |
| Redis | Not configured |
| Celery | Not configured |
| Nginx | Not configured |
| Let's Encrypt | Not configured |

Some GeoNode features require these external services and may not work fully in the basic local environment.

If development requires GeoServer integration, background processing or production-like behavior, configure the additional services separately.

## 11. Git workflow

Use the development branch for Windows-specific development:

```powershell
git checkout development/geonode-5.1.0
```

Before committing changes:

```powershell
git status
git diff
git diff --check
```

Commit changes:

```powershell
git add .
git commit -m "Describe the change"
```

Push the development branch:

```powershell
git push origin development/geonode-5.1.0
```

Do not commit:

- `.env`
- `.venv`
- Local database files
- Generated static files
- Local logs
- Temporary build artifacts

The repository `.gitignore` already excludes the main local development files.

## 12. Troubleshooting

### 12.1 GDAL DLL loading errors

Verify that the virtual environment is active:

```powershell
where.exe python
```

Check the installed GDAL package:

```powershell
pip show gdal-wheel
```

Run the GDAL import test:

```powershell
python -c "from osgeo import gdal; print(gdal.VersionInfo())"
```

Check that the Windows-specific GDAL configuration in `geonode/settings.py` is present.

### 12.2 PostgreSQL connection errors

Verify that the PostgreSQL service is running.

Check that the database names, username, host and port in `.env` match the local PostgreSQL installation.

Verify database connectivity independently using PostgreSQL tools.

Do not share database passwords in logs or support requests.

### 12.3 Django does not load `.env`

Use the documented `python-dotenv` command:

```powershell
python -m dotenv -f .env run -- .\.venv\Scripts\python.exe manage.py check
```

Running `manage.py` directly may not load the environment variables.

### 12.4 Missing external services

If a feature requires GeoServer, Redis or Celery, verify whether the service is configured and running.

The basic Windows environment does not include the complete production service stack.

## 13. Verified local environment

The following versions were used in the tested local environment:

| Component | Version |
|---|---|
| Python | 3.13.2 |
| Django | 5.2.15 |
| NumPy | 2.3.1 |
| GDAL | 3.13.3 |
| Shapely | 2.1.2 |
| PyProj | 3.7.2 |
| psycopg2 | 2.9.12 |
| PostgreSQL | 14.6 |
| PostGIS | 3.2.1 |

The following checks were successful:

- Python virtual environment created.
- GeoNode dependencies installed.
- GDAL, GEOS and PROJ imports verified.
- PostgreSQL connections verified.
- Django system check passed.
- Database migrations completed.
- Superuser created.
- Static files collected.
- Django development server started successfully.
- GeoNode login page accessible locally.

## 14. Development setup checklist

- [ ] Python installed.
- [ ] GeoNode repository cloned.
- [ ] `development/geonode-5.1.0` checked out.
- [ ] Python virtual environment created and activated.
- [ ] Python dependencies installed.
- [ ] GDAL and GIS libraries verified.
- [ ] PostgreSQL installed and running.
- [ ] PostGIS enabled in both databases.
- [ ] Local `.env` configured.
- [ ] Django system check passed.
- [ ] Database migrations completed.
- [ ] Superuser created.
- [ ] Static files collected.
- [ ] Local development server started.
- [ ] GeoNode login verified.
