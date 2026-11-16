# Production Installation Guide

## 1. Overview

This document describes how to install and deploy the Level2 GeoNode Huginn project in a production environment using Docker Compose.

The deployment consists of seven services:

| Service | Description |
|---|---|
| `django` | GeoNode application served by uWSGI |
| `celery` | Background task processing |
| `nginx` | Reverse proxy and HTTP/HTTPS entry point |
| `letsencrypt` | TLS certificate management |
| `geoserver` | GeoServer backend |
| `db` | PostgreSQL with PostGIS |
| `redis` | Redis service used by Celery |

The deployment is based on two repositories:

- **Application project:** https://github.com/level2-gis/geonode-huginn
- **GeoNode core:** https://github.com/level2-gis/geonode

The GeoNode dependency is pinned to tag `5.1.0` in `src/pyproject.toml`.

## 2. System requirements

### 2.1 Host operating system

The current production deployment uses:

- Ubuntu Server 24.04 LTS
- Docker Engine
- Docker Compose plugin
- Git

The Dockerfile uses the following application base image:

```dockerfile
FROM geonode/geonode-base:latest-ubuntu-26.04
```

The operating system inside the application container is independent of the host operating system.

### 2.2 Network requirements

For a public production deployment:

- Configure a DNS record pointing to the server.
- Allow inbound TCP port 80 for HTTP.
- Allow inbound TCP port 443 for HTTPS.
- Ensure that the server can access external repositories and image registries.

PostgreSQL is not publicly exposed in the current Docker Compose configuration.

## 3. Clone the project repository

The production project directory used by the current deployment is `/opt/geonode-huginn`.

```bash
sudo install -d -o "$USER" -g "$USER" /opt/geonode-huginn

git clone https://github.com/level2-gis/geonode-huginn.git /opt/geonode-huginn

cd /opt/geonode-huginn
```

Check the repository state:

```bash
git status
git branch --show-current
git remote -v
```

The current production deployment uses the `master` branch of `geonode-huginn`.

## 4. Configure the environment

The project uses a `.env` file located in the repository root.

This file contains deployment-specific configuration, including:

- Domain and public URLs.
- Database names and credentials.
- GeoNode and GeoServer administrator credentials.
- Django secret key.
- OAuth credentials.
- Docker image versions.
- Redis and Celery configuration.
- HTTP and HTTPS settings.

The `.env` file must never be committed to Git.

### 4.1 Generate the environment file

The repository includes `create-envfile.py`, which generates `.env` using `.env.sample` as a template.

For an HTTPS production deployment:

```bash
python3 create-envfile.py \
  --hostname geo.example.com \
  --https \
  --email admin@example.com \
  --env_type prod
```

Replace the example hostname and email address with the actual production values.

The script prompts for confirmation before overwriting an existing `.env` file.

### 4.2 Provide production credentials

The script supports the following parameters:

| Parameter | Description |
|---|---|
| `--geonodepwd` | GeoNode administrator password |
| `--geoserverpwd` | GeoServer administrator password |
| `--pgpwd` | PostgreSQL password |
| `--dbpwd` | GeoNode database user password |
| `--geodbpwd` | Geodatabase user password |
| `--clientid` | OAuth2 client ID |
| `--clientsecret` | OAuth2 client secret |
| `--authapikey` | OAuth2 API key |
| `--secret_key` | Django secret key |

For production, use strong, unique credentials generated with a cryptographically secure password generator.

The script generates random values for parameters that are not provided. Do not rely on automatically generated defaults as the production secret-management strategy.

### 4.3 JSON configuration

Configuration can also be provided through a JSON file.

Example structure:

```json
{
  "hostname": "geo.example.com",
  "https": true,
  "email": "admin@example.com",
  "env_type": "prod",
  "geonodepwd": "REPLACE_WITH_SECURE_PASSWORD",
  "geoserverpwd": "REPLACE_WITH_SECURE_PASSWORD",
  "pgpwd": "REPLACE_WITH_SECURE_PASSWORD",
  "dbpwd": "REPLACE_WITH_SECURE_PASSWORD",
  "geodbpwd": "REPLACE_WITH_SECURE_PASSWORD",
  "clientid": "REPLACE_WITH_CLIENT_ID",
  "clientsecret": "REPLACE_WITH_SECURE_SECRET",
  "authapikey": "REPLACE_WITH_SECURE_API_KEY",
  "secret_key": "REPLACE_WITH_SECURE_DJANGO_SECRET"
}
```

Generate `.env` using:

```bash
python3 create-envfile.py --file /secure/path/production.json
```

The JSON file must be stored outside the Git repository and protected appropriately.

Do not commit the JSON file or share it through an unsecured channel.

### 4.4 Review the generated configuration

Before starting the deployment, verify the following:

- Correct hostname and site URL.
- Correct HTTP/HTTPS configuration.
- `DEBUG=False`.
- Correct database names and users.
- Strong database and administrator passwords.
- Correct Docker image versions.
- Correct Redis and Celery configuration.
- Correct PostgreSQL connection settings.

Do not publish the contents of `.env` in logs, issue trackers or documentation.

## 5. Prepare persistent storage

The Docker Compose configuration stores application data outside the containers under `/data/geonode/`.

Create the required directories:

```bash
sudo mkdir -p \
  /data/geonode/statics \
  /data/geonode/geoserver \
  /data/geonode/backup-restore \
  /data/geonode/data \
  /data/geonode/tmp \
  /data/geonode/nginx-certificates \
  /data/geonode/db \
  /data/geonode/dbbackups \
  /data/geonode/redis
```

### 5.1 Directory structure

| Directory | Purpose |
|---|---|
| `/data/geonode/statics` | Static application files |
| `/data/geonode/geoserver` | GeoServer configuration and data |
| `/data/geonode/backup-restore` | GeoNode backup and restore files |
| `/data/geonode/data` | Persistent application data |
| `/data/geonode/tmp` | Temporary application files |
| `/data/geonode/nginx-certificates` | TLS certificates |
| `/data/geonode/db` | PostgreSQL database files |
| `/data/geonode/dbbackups` | PostgreSQL backup files |
| `/data/geonode/redis` | Redis persistent data |

The Compose configuration also creates a named Docker volume for Nginx configuration.

### 5.2 Permissions

Ensure that container processes have the required access to their mounted directories.

Do not apply arbitrary ownership or permission changes recursively to existing data directories. In particular, do not change PostgreSQL data directory ownership without checking the requirements of the PostgreSQL container image.

Persistent directories must be retained when containers are recreated or application images are updated.

## 6. Validate Docker Compose configuration

Before building the images, validate the Compose configuration:

```bash
docker compose config --quiet
```

Resolve any reported configuration errors before proceeding.

The fully resolved Compose configuration may contain sensitive environment values. Do not publish its full output.

## 7. Build Docker images

Build the application and supporting custom images:

```bash
docker compose build
```

The application image is built using the root `Dockerfile`.

During the build:

1. The GeoNode base image is used.
2. Required system packages are installed.
3. Project source files are copied into the image.
4. Python dependencies are installed.
5. GeoNode is installed from the configured `level2-gis/geonode` repository tag.

The Compose configuration also builds custom images for:

- Nginx
- GeoServer
- PostgreSQL/PostGIS
- Let's Encrypt

Redis uses the official `redis:8-alpine` image.

## 8. Start the services

Start the complete application stack:

```bash
docker compose up -d
```

Docker Compose starts the services according to their configured dependencies and health checks.

The dependency structure includes:

- Django waits for PostgreSQL and Redis.
- Celery waits for PostgreSQL and Redis.
- GeoServer waits for Django to become healthy.
- Let's Encrypt waits for Nginx to become healthy.

## 9. Verify the deployment

Check container status:

```bash
docker compose ps
```

Check individual service logs:

```bash
docker compose logs --tail=100 django
docker compose logs --tail=100 celery
docker compose logs --tail=100 db
docker compose logs --tail=100 geoserver
docker compose logs --tail=100 nginx
docker compose logs --tail=100 letsencrypt
```

Verify that:

- All expected containers are running.
- Services with health checks report healthy status.
- The public domain resolves to the production server.
- HTTP/HTTPS access works as configured.
- The GeoNode login page is accessible.
- GeoServer is accessible through the configured GeoNode integration.
- Persistent database and GeoServer data are available.

For HTTPS deployments, verify that the Let's Encrypt certificate has been issued and that the browser reports a valid certificate.

## 10. Network and security considerations

The production deployment exposes HTTP and HTTPS through Nginx.

The PostgreSQL service is not publicly exposed in the current Compose configuration. Its port mapping is commented out and should remain disabled unless remote database access is specifically required.

Recommended security practices:

- Keep `.env` and all secret files outside version control.
- Use strong, unique passwords for all services.
- Restrict SSH access to trusted administrators.
- Keep Docker Engine and the host operating system updated.
- Expose only the required public ports.
- Use HTTPS for public access.
- Restrict database access to the internal Docker network.
- Maintain regular backups of persistent application data.

## 11. Version management

The project repository and GeoNode core have separate versioning:

| Component | Current configuration |
|---|---|
| GeoNode Huginn project | `master` branch |
| GeoNode core | Tag `5.1.0` |
| GeoServer image | Configured through `GEOSERVER_BASE_IMAGE_VERSION` |
| Nginx image | Configured through `NGINX_BASE_IMAGE_VERSION` |
| PostgreSQL/PostGIS image | Configured through `POSTGRES_BASE_IMAGE_VERSION` |
| Let's Encrypt image | Configured through `LETSENCRYPT_BASE_IMAGE_VERSION` |

The GeoNode dependency is defined in `src/pyproject.toml`.

The Docker image versions are controlled through `.env`. Review these values before changing or rebuilding production images.

## 12. Post-installation checklist

- [ ] Host operating system and Docker prerequisites installed.
- [ ] Project repository cloned.
- [ ] Production `.env` generated and reviewed.
- [ ] Secrets securely stored.
- [ ] Persistent directories created.
- [ ] Docker Compose configuration validated.
- [ ] Docker images built successfully.
- [ ] All services started.
- [ ] Container health checks passed.
- [ ] Public domain and HTTPS verified.
- [ ] GeoNode login verified.
- [ ] GeoServer integration verified.
- [ ] Backup and restore procedures established.
