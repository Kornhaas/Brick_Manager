# Bricks Manager - Docker Deployment Guide

This guide explains how to deploy the Bricks Manager application using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+ 
- Docker Compose 2.0+

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd Bricks_Manager

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings (especially REBRICKABLE_TOKEN)
```

### 2. Start the Application
```bash
# Build and start the application
docker-compose up -d

# Check the logs
docker-compose logs -f bricks-manager

# The application will be available at http://localhost:5000
```

## 📁 Data Persistence

The following directories are mounted outside the container for persistence:

```
./data/
├── instance/        # SQLite database storage
├── uploads/         # User uploaded files (images, etc.)
├── output/          # Generated files (labels, exports)
├── cache/          # Application cache
└── logs/           # Application logs
```

These directories are automatically created when you first run the container.

## 🗄️ Database Management

### Automatic Database Creation
The container automatically:
- Creates a new SQLite database if none exists
- Runs database migrations on startup
- Loads master lookup data

### Manual Database Operations
```bash
# Access the container shell
docker-compose exec bricks-manager bash

# Run Flask commands
cd /app/brick_manager
flask db upgrade    # Apply migrations
flask shell         # Interactive Python shell
```

## ⚙️ Configuration

### Environment Variables (.env file)
```bash
# Required - Get from rebrickable.com
REBRICKABLE_TOKEN=your-rebrickable-api-token-here

# Security - Change in production
SECRET_KEY=your-very-secure-secret-key-here

# Optional
FLASK_ENV=production
LOG_LEVEL=INFO
```

### Docker Compose Override
Create `docker-compose.override.yml` for custom settings:

```yaml
version: '3.8'
services:
  bricks-manager:
    ports:
      - "8080:5000"  # Change port
    environment:
      - CUSTOM_ENV_VAR=value
```

## 🔧 Advanced Usage

### Production Deployment with Nginx
```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d
```

### Backup Data
```bash
# Backup all persistent data
tar -czf bricks-manager-backup-$(date +%Y%m%d).tar.gz data/

# Restore backup
tar -xzf bricks-manager-backup-YYYYMMDD.tar.gz
```

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Scaling and Resources
```yaml
# In docker-compose.yml
services:
  bricks-manager:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🐛 Troubleshooting

### Common Issues

1. **Permission Issues**
   ```bash
   # Fix data directory permissions
   sudo chown -R 1000:1000 data/
   ```

2. **Database Locked**
   ```bash
   # Stop all containers accessing the database
   docker-compose down
   # Restart
   docker-compose up -d
   ```

3. **Port Already in Use**
   ```bash
   # Check what's using port 5000
   sudo lsof -i :5000
   # Change port in docker-compose.yml or stop the conflicting service
   ```

### Logging
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f bricks-manager

# View specific container logs
docker logs bricks-manager-app
```

### Health Check
```bash
# Check application health
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","message":"Application is running properly","database":"connected"}
```

## 🔄 Development Mode

For development with live code reloading:

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  bricks-manager:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./brick_manager:/app/brick_manager  # Mount source code
      - ./data:/app/data
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
```

```bash
# Run in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 📊 Monitoring

### Resource Usage
```bash
# Monitor container resource usage
docker stats bricks-manager-app

# Container information
docker inspect bricks-manager-app
```

### Application Metrics
The application exposes a health endpoint at `/health` for monitoring tools like:
- Prometheus
- Nagios
- Custom monitoring scripts

## 🛡️ Security Considerations

1. **Change default secrets** in production
2. **Use environment variables** for sensitive data
3. **Regular backups** of the data directory
4. **Keep Docker images updated**
5. **Consider using Docker secrets** for production

## 📞 Support

For issues and questions:
1. Check the application logs: `docker-compose logs bricks-manager`
2. Verify configuration in `.env` file
3. Ensure data directory permissions are correct
4. Check Docker and Docker Compose versions