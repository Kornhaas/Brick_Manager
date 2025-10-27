# 🐳 Bricks Manager - Complete Docker Setup

## ✅ What's Been Implemented

Your Bricks Manager application is now fully dockerized with the following features:

### 🏗️ **Multi-stage Dockerfile**
- **Optimized build** with Python 3.12-slim base image
- **Security-focused** with non-root user (`appuser`)
- **Minimal production image** with only necessary dependencies
- **Health check support** for monitoring

### 📁 **External Data Volumes**
All dynamic data is stored outside the container:
```
./data/
├── instance/     # 🗄️ SQLite database (brick_manager.db)
├── uploads/      # 📁 User uploaded files 
├── output/       # 📄 Generated labels and exports
├── cache/        # ⚡ Application cache files
└── logs/         # 📝 Application logs
```

### 🚀 **Smart Entrypoint Script**
- **Automatic database creation** if no database exists
- **Migration handling** for existing databases  
- **Master data loading** for lookup services
- **Symbolic link setup** for mounted volumes
- **Environment validation** and setup

### ⚙️ **Flexible Configuration**
- **Environment-based config** supporting both Docker and local development
- **Dynamic path resolution** (Docker vs local)
- **Comprehensive environment variables** via `.env` file
- **Health check endpoint** at `/health`

### 🔧 **Docker Compose Setup**
- **Production-ready configuration** with restart policies
- **Optional Nginx reverse proxy** for production
- **Health checks** with proper startup timing
- **Network isolation** with custom bridge network
- **Development override** for live code reloading

### 🛠️ **Developer Tools**
- **Makefile** with 15+ common operations
- **Development mode** with live reloading
- **Backup/restore utilities** for data management
- **Shell access** for debugging
- **Resource monitoring** commands

## 🚀 Quick Start Guide

### 1. **Initial Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # Set REBRICKABLE_TOKEN and SECRET_KEY

# Start the application
docker compose up -d
```

### 2. **Using the Makefile (Recommended)**
```bash
# First time setup
make setup

# Start application
make up

# View logs
make logs-f

# Check health
make health

# Backup data
make backup

# See all available commands
make help
```

### 3. **Manual Docker Commands**
```bash
# Build and start
docker compose build
docker compose up -d

# View logs
docker compose logs -f bricks-manager

# Stop
docker compose down
```

## 📋 Key Features

### 🔄 **Automatic Database Management**
- Creates new SQLite database on first run
- Applies migrations automatically
- Loads master lookup data
- Handles database upgrades seamlessly

### 📦 **Volume Management**
- All user data persists outside containers
- Easy backup and restore procedures
- No data loss when updating containers
- Portable data directory structure

### 🏥 **Health Monitoring**
- Health check endpoint: `http://localhost:5000/health`
- Database connectivity verification
- Container health status in Docker
- Ready for production monitoring tools

### 🔐 **Security & Production Ready**
- Non-root container user
- Environment-based secrets
- Minimal attack surface
- Optional SSL/TLS with Nginx
- Resource limits configurable

### 🔧 **Development Support**
- Live code reloading in dev mode
- Source code mounting for development
- Separate development configuration
- Easy debugging with shell access

## 📁 File Structure

```
Bricks_Manager/
├── 🐳 Dockerfile                 # Multi-stage container build
├── 🐳 docker-compose.yml         # Production deployment config  
├── 🐳 docker-compose.dev.yml     # Development overrides
├── 🐳 entrypoint.sh             # Container startup script
├── 🐳 .dockerignore             # Build optimization
├── ⚙️ .env.example               # Environment template
├── 🔧 Makefile                  # Developer commands
├── 📚 DOCKER_README.md          # Comprehensive Docker guide
├── 📁 data/                     # External data volumes
│   ├── instance/               # Database storage
│   ├── uploads/                # File uploads  
│   ├── output/                 # Generated files
│   ├── cache/                  # App cache
│   └── logs/                   # Application logs
└── 🏠 brick_manager/            # Application code
    ├── config.py               # Updated for Docker support
    └── routes/main.py          # Health check endpoint
```

## ✨ Advanced Features

### 🔍 **Production Monitoring**
```bash
# Health check for monitoring tools
curl http://localhost:5000/health

# Container resource usage  
make stats

# Application logs
make logs
```

### 💾 **Data Management**
```bash
# Automated backups
make backup

# Restore from backup
make restore  

# Database shell access
make db-shell
```

### 🔄 **Updates & Maintenance**
```bash
# Update application code
make update

# Clean Docker resources
make clean

# Reset database (careful!)
make reset-db
```

## 🎯 Next Steps

1. **Configure your environment**:
   - Edit `.env` with your Rebrickable API token
   - Set a secure SECRET_KEY for production

2. **Start the application**:
   ```bash
   make setup  # First time
   make up     # Start services
   ```

3. **Access your application**:
   - Main app: http://localhost:5000
   - Health check: http://localhost:5000/health

4. **For production deployment**:
   - Review security settings in `.env`
   - Consider using the Nginx reverse proxy
   - Set up regular backups with `make backup`
   - Monitor with the health endpoint

Your Bricks Manager is now fully containerized and production-ready! 🎉