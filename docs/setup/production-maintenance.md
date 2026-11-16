# Production Maintenance Guide

## 1. Overview

This document describes routine maintenance, monitoring, updates and backup considerations for the production GeoNode Huginn deployment.

The production application runs using Docker Compose in:

```text
/opt/geonode-huginn
```

Persistent application data is stored under:

```text
/data/geonode/
```

Always execute Docker Compose commands from the project directory unless explicitly stated otherwise.

```bash
cd /opt/geonode-huginn
```

## 2. Check deployment status

### 2.1 Container status

List all services and their current status:

```bash
docker compose ps
```

Check running containers:

```bash
docker ps
```

Services with health checks should report `healthy` after successful initialization.

### 2.2 Resource usage

Check Docker container resource usage:

```bash
docker stats
```

Check disk usage:

```bash
df -h
```

Check the size of persistent application data:

```bash
sudo du -sh /data/geonode/*
```

Monitor available space, especially in the PostgreSQL and GeoServer data directories.

### 2.3 Service logs

Display recent logs for all services:

```bash
docker compose logs --tail=100
```

Follow logs in real time:

```bash
docker compose logs -f
```

Inspect an individual service:

```bash
docker compose logs --tail=200 django
docker compose logs --tail=200 celery
docker compose logs --tail=200 db
docker compose logs --tail=200 geoserver
docker compose logs --tail=200 nginx
docker compose logs --tail=200 redis
```

Stop following logs with `Ctrl+C`. This does not stop the containers.

## 3. Restart services

Restart one service:

```bash
docker compose restart django
```

Restart the complete application stack:

```bash
docker compose restart
```

Check the service status after restarting:

```bash
docker compose ps
```

Restarting containers does not intentionally delete persistent data.

## 4. Stop and start the application

Stop all services:

```bash
docker compose stop
```

Start stopped services:

```bash
docker compose start
```

Alternatively, recreate and start services using the current Compose configuration:

```bash
docker compose up -d
```

Do not use volume deletion options when stopping or recreating production services.

## 5. Update the application

### 5.1 Before updating

Before every production update:

1. Review the changes planned for deployment.
2. Confirm the target Git branch and commit.
3. Verify that a recent recoverable backup exists.
4. Check available disk space.
5. Review changes to `.env`, Docker Compose and Dockerfiles.
6. Check whether database migrations or other manual steps are required.

Do not update production directly from an untested local working tree.

### 5.2 Check the current Git version

```bash
git status
git branch --show-current
git log -1 --oneline
```

The current production deployment uses the `master` branch.

### 5.3 Fetch and review changes

```bash
git fetch origin
git log --oneline HEAD..origin/master
```

Review the commits before applying them.

Check whether local modifications exist:

```bash
git status
```

Do not overwrite local production configuration or modifications without understanding their purpose.

### 5.4 Update the repository

When the update has been reviewed and approved:

```bash
git pull --ff-only origin master
```

Check the resulting version:

```bash
git log -1 --oneline
git status
```

### 5.5 Rebuild and deploy

Rebuild the application and custom images:

```bash
docker compose build
```

Apply the updated Compose configuration:

```bash
docker compose up -d
```

Docker Compose recreates services when their configuration or image changes require it.

### 5.6 Verify the update

```bash
docker compose ps
docker compose logs --tail=200 django
docker compose logs --tail=200 celery
docker compose logs --tail=200 db
docker compose logs --tail=200 geoserver
```

Verify the following:

- All required services are running.
- Health checks pass.
- GeoNode is accessible.
- Login works.
- GeoServer integration works.
- Important application functions operate correctly.
- No unexpected errors appear in the logs.

### 5.7 Important version considerations

The project and GeoNode core have separate versioning.

The GeoNode core dependency is pinned in:

```text
src/pyproject.toml
```

Currently, it references the `5.1.0` tag.

Changing the GeoNode dependency or Docker base image should be treated as a separate upgrade, not as a routine project update.

Review and test such changes in a non-production environment before deploying them.

## 6. Database and application backups

### 6.1 Persistent data locations

The production Compose configuration uses the following persistent directories:

| Directory | Content |
|---|---|
| `/data/geonode/db` | PostgreSQL database files |
| `/data/geonode/dbbackups` | PostgreSQL backup files |
| `/data/geonode/geoserver` | GeoServer data |
| `/data/geonode/data` | Application data |
| `/data/geonode/backup-restore` | GeoNode backup and restore files |
| `/data/geonode/statics` | Static application files |
| `/data/geonode/redis` | Redis persistent data |
| `/data/geonode/nginx-certificates` | TLS certificates |

Persistent storage is not a substitute for a backup.

### 6.2 GeoNode backup and restore scripts

The repository README documents GeoNode backup and restore scripts:

```text
geonode_project/br/backup.sh
geonode_project/br/restore.sh
```

The scripts accept the following parameters:

- `BKP_FOLDER_NAME`: shared backup folder name; default is `backup_restore`.
- `SOURCE_URL`: source server URL.
- `TARGET_URL`: target server URL.

The documented execution method runs the scripts inside the Django container.

Example command structure:

```bash
docker compose exec django sh -c \
  'SOURCE_URL=<SOURCE_URL> TARGET_URL=<TARGET_URL> ./geonode_project/br/backup.sh backup_restore'
```

The restore script follows the same pattern:

```bash
docker compose exec django sh -c \
  'SOURCE_URL=<SOURCE_URL> TARGET_URL=<TARGET_URL> ./geonode_project/br/restore.sh backup_restore'
```

Replace the placeholders with the correct values for the intended backup or restore operation.

**Important:** These commands describe the interface documented by the project README. Before using them on production, verify the script location inside the current image, the meaning of the source and target URLs for the intended operation, and the resulting backup contents.

Never test a restore directly on production without a recovery plan.

### 6.3 Backup strategy

A complete production backup strategy should cover:

- PostgreSQL database contents.
- GeoServer data directory.
- GeoNode uploaded and application data.
- Relevant configuration files.
- Required credentials and secret material, stored securely.
- TLS certificates, where needed for recovery.

Backups should be stored outside the production server as well as locally.

A backup is only useful if it can be restored. Perform periodic restore tests in a separate environment.

### 6.4 Automated backups

The existence of backup directories or scripts does not mean automated application backups are configured.

Verify the actual backup schedule and monitoring independently.

No GeoNode application-level cron or systemd backup schedule was identified during the initial production server inspection. This should be reviewed when implementing the production backup policy.

## 7. PostgreSQL maintenance

The PostgreSQL service is named `db` in Docker Compose.

Check PostgreSQL logs:

```bash
docker compose logs --tail=200 db
```

Open a PostgreSQL shell:

```bash
docker compose exec db psql -U postgres
```

Useful PostgreSQL queries:

```sql
SELECT version();

SELECT datname
FROM pg_database
ORDER BY datname;

SELECT count(*)
FROM pg_stat_activity;

SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state
ORDER BY state;
```

Exit the PostgreSQL shell:

```sql
\q
```

Do not change PostgreSQL configuration or delete database files without a verified backup and a clear maintenance plan.

## 8. Docker image and disk maintenance

List locally available images:

```bash
docker image ls
```

Check Docker disk usage:

```bash
docker system df
```

Docker images and build cache can consume significant disk space.

Do not run broad cleanup commands such as:

```bash
docker system prune -a
```

on production without first reviewing which images and resources are unused and confirming that they are not required for rollback.

Never use:

```bash
docker compose down -v
```

as a routine maintenance command. The `-v` option can remove named volumes.

## 9. Troubleshooting

### 9.1 Service is unhealthy

Check the service status:

```bash
docker compose ps
```

Inspect its logs:

```bash
docker compose logs --tail=200 <service>
```

Check whether dependent services are healthy.

### 9.2 GeoNode is unavailable

Inspect:

```bash
docker compose logs --tail=200 nginx
docker compose logs --tail=200 django
docker compose logs --tail=200 db
```

Check DNS resolution, firewall rules and the configured HTTP/HTTPS ports.

### 9.3 GeoServer is unavailable

Inspect:

```bash
docker compose logs --tail=200 geoserver
docker compose logs --tail=200 django
```

Check GeoServer health and the persistent GeoServer data directory.

### 9.4 Database connection errors

Inspect:

```bash
docker compose logs --tail=200 db
docker compose logs --tail=200 django
```

Check the database service health, connection settings in `.env` and available disk space.

### 9.5 Disk space problems

Check:

```bash
df -h
docker system df
sudo du -sh /data/geonode/*
```

Do not manually delete files from PostgreSQL, GeoServer or application data directories to free space.

## 10. Maintenance checklist

### Routine checks

- [ ] All containers are running.
- [ ] Health checks are successful.
- [ ] GeoNode is accessible.
- [ ] GeoServer is accessible.
- [ ] No critical errors appear in service logs.
- [ ] Sufficient disk space is available.
- [ ] Backup status has been checked.

### Before deployment

- [ ] Changes reviewed.
- [ ] Current Git commit recorded.
- [ ] Backup verified.
- [ ] Disk space checked.
- [ ] Configuration changes reviewed.
- [ ] Deployment completed.
- [ ] Application functionality verified.
- [ ] Rollback plan available.

### Periodic recovery checks

- [ ] Database backup can be restored.
- [ ] GeoServer data can be restored.
- [ ] Application data can be restored.
- [ ] Required configuration and secrets are available.
