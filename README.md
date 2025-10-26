# 🧱 Bricks Manager

A comprehensive Flask-based web application for managing brick collections, sets, and parts. This application helps brick enthusiasts organize their collection, track missing parts, generate labels, and efficiently manage storage systems with integration to the Rebrickable database.

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0+-green.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents

- [🌟 Features](#-features)
- [🚀 Quick Start](#-quick-start)
  - [Docker Deployment (Recommended)](#docker-deployment-recommended)
  - [Local Development](#local-development)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration](#️-configuration)
- [🔧 Usage Guide](#-usage-guide)
- [🐳 Docker Support](#-docker-support)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🌟 Features

### 📦 **Set Management**
- **Enhanced Set Maintenance Interface** with sortable columns and advanced filtering
- **Automatic Database Creation** for new deployments
- **Progress Tracking** with visual completion indicators
- **Automatic Label Printing** when generating box labels
- **Theme-based Organization** with dynamic theme detection

### 🔍 **Advanced Search & Filtering**
- **Quick Search** across set numbers, names, and themes
- **Expandable Advanced Filters** with multiple criteria:
  - Status filtering (Complete, Missing Parts, etc.)
  - Theme-based filtering
  - Label printing status
  - Parts completion percentage
- **Real-time Filtering** with instant results
- **Filter Combinations** for precise searches

### 🧾 **Part Management**
- **Manual Part Entry** with comprehensive validation
- **Part Lookup** with detailed information and storage location
- **Missing Parts Detection** and tracking
- **Color-coded Status Indicators** for quick visual reference
- **Spare Parts Handling** with dedicated tracking

### 🏷️ **Label Generation**
- **Professional Label Printing** for storage organization
- **Multiple Box Sizes** (Small/Big box support)
- **QR Code Integration** for quick scanning
- **Batch Label Generation** for multiple sets
- **Print Status Tracking** to avoid duplicates

### 📊 **Data Integration**
- **Rebrickable API Integration** for comprehensive brick database access
- **Automatic Data Synchronization** with scheduled updates
- **Local Caching** to reduce API calls and improve performance
- **Master Lookup Data** for offline capabilities

### 🗄️ **Storage Management**
- **Multi-level Storage System** (Cabinet → Shelf → Box)
- **Storage Location Tracking** for every part
- **Box Maintenance** with visual organization tools
- **Location-based Search** and filtering

## 🚀 Quick Start

### Docker Deployment (Recommended)

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Kornhaas/Bricks_Manager.git
   cd Bricks_Manager
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your settings (especially REBRICKABLE_TOKEN)
   ```

2. **Start with Docker Compose**
   ```bash
   # Quick start
   make setup
   
   # Or manually
   docker compose up -d
   ```

3. **Access Application**
   - Main Application: http://localhost:5000
   - Health Check: http://localhost:5000/health

### Local Development

1. **Prerequisites**
   - Python 3.11+
   - Poetry (dependency management)
   - SQLite3

2. **Setup**
   ```bash
   git clone https://github.com/Kornhaas/Bricks_Manager.git
   cd Bricks_Manager
   
   # Install dependencies
   poetry install
   
   # Set up environment
   cp .env.example .env
   # Configure your .env file
   
   # Initialize database
   cd brick_manager
   poetry run flask db upgrade
   
   # Start application
   poetry run flask run
   ```

## 📁 Project Structure

```
Bricks_Manager/
├── 🐳 Docker Configuration
│   ├── Dockerfile                 # Multi-stage container build
│   ├── docker-compose.yml         # Production deployment
│   ├── docker-compose.dev.yml     # Development overrides
│   ├── entrypoint.sh             # Container startup script
│   └── .dockerignore             # Build optimization
├── 
├── 🏠 Application Core
│   └── brick_manager/
│       ├── app.py                # Flask application factory
│       ├── config.py             # Configuration management
│       ├── models.py             # Database models
│       └── manage.py             # CLI management commands
├── 
├── 🛣️ Routes & Views
│   └── brick_manager/routes/
│       ├── main.py               # Home and health endpoints
│       ├── set_maintain.py       # Enhanced set management
│       ├── part_lookup.py        # Part search and details
│       ├── missing_parts.py      # Missing parts tracking
│       ├── dashboard.py          # Analytics dashboard
│       └── ...                   # Additional route modules
├── 
├── 🎨 Frontend Assets
│   └── brick_manager/
│       ├── templates/            # Jinja2 HTML templates
│       │   ├── set_maintain.html # Enhanced with sorting/filtering
│       │   └── ...               # Other UI templates
│       └── static/
│           ├── css/              # Stylesheets
│           ├── js/               # JavaScript functionality
│           └── cache/            # Dynamic cache storage
├── 
├── 🔧 Services & Utilities
│   └── brick_manager/services/
│       ├── rebrickable_service.py    # API integration
│       ├── part_lookup_service.py    # Part search logic
│       ├── label_service.py          # Label generation
│       └── cache_service.py          # Caching system
├── 
├── 📁 Data Storage (Docker Volumes)
│   └── data/
│       ├── instance/             # SQLite database
│       ├── uploads/              # User uploaded files
│       ├── output/               # Generated labels/exports
│       ├── cache/                # Application cache
│       └── logs/                 # Application logs
├── 
├── 🧪 Testing & Quality
│   ├── tests/                    # Unit and integration tests
│   ├── pytest.ini               # Test configuration
│   └── .pylintrc                # Code quality rules
├── 
└── 📚 Documentation & Config
    ├── README.md                 # This file
    ├── DOCKER_README.md          # Docker deployment guide
    ├── Makefile                  # Development commands
    ├── pyproject.toml            # Poetry dependencies
    └── .env.example              # Environment template
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required - Rebrickable API
REBRICKABLE_TOKEN=your-rebrickable-api-token-here

# Security (Change in production!)
SECRET_KEY=your-very-secure-secret-key-here

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=0

# Database (auto-configured for Docker)
SQLALCHEMY_DATABASE_URI=sqlite:///data/instance/brick_manager.db

# Optional
LOG_LEVEL=INFO
```

### Rebrickable API Setup

1. Create account at [rebrickable.com](https://rebrickable.com)
2. Go to Settings → API → Generate API Key
3. Add the token to your `.env` file

## 🔧 Usage Guide

### 📦 Set Management

**Enhanced Interface Features:**
- **Sortable Columns**: Click any header to sort (Set Number, Name, Theme, etc.)
- **Quick Search**: Universal search across all set data
- **Advanced Filters**: Expandable panel with detailed filtering options
- **Status Tracking**: Visual progress bars and completion indicators
- **Bulk Operations**: Select multiple sets for batch operations

**Workflow:**
1. Navigate to "Set Maintenance"
2. Use Quick Search or Advanced Filters to find sets
3. Track completion with visual progress indicators
4. Generate labels automatically when creating storage boxes
5. Monitor printing status to avoid duplicates

### 🔍 Part Lookup & Management

**Features:**
- **Comprehensive Search**: Find parts by number, name, or category
- **Storage Location**: Track exactly where each part is stored
- **Missing Parts**: Identify and track incomplete sets
- **Color Management**: Handle multiple color variants
- **Quantity Tracking**: Monitor collected vs. required quantities

### 🏷️ Label Generation

**Capabilities:**
- **Professional Labels**: Clean, scannable labels for organization
- **Multiple Formats**: Small and large box label sizes
- **QR Codes**: Quick scanning for digital integration
- **Batch Printing**: Generate multiple labels efficiently
- **Status Tracking**: Automatic print status updates

### 📊 Dashboard & Analytics

- **Collection Overview**: Visual statistics and progress tracking
- **Completion Metrics**: Set and part completion percentages
- **Storage Utilization**: Monitor space usage across storage systems
- **Recent Activity**: Track latest additions and changes

## 🐳 Docker Support

### Production Deployment

```bash
# Complete setup with one command
make setup

# Or step by step
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

### Development Mode

```bash
# Start in development mode with live reloading
make dev

# Or manually
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Available Make Commands

```bash
make help           # Show all available commands
make up             # Start application
make down           # Stop application
make logs           # View logs
make logs-f         # Follow logs
make backup         # Backup all data
make restore        # Restore from backup
make health         # Check application health
make shell          # Access container shell
make clean          # Clean Docker resources
make update         # Update and restart
```

### Data Persistence

All user data is stored in mounted volumes:
- **Database**: `./data/instance/` - SQLite database
- **Uploads**: `./data/uploads/` - User uploaded files
- **Output**: `./data/output/` - Generated labels and exports
- **Cache**: `./data/cache/` - Application cache
- **Logs**: `./data/logs/` - Application logs

## 🧪 Testing

### Run Tests

```bash
# Local development
poetry run pytest

# Docker environment
docker compose exec bricks-manager pytest

# With coverage
poetry run pytest --cov=brick_manager
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: API and database integration
- **Service Tests**: Business logic validation
- **Route Tests**: HTTP endpoint testing

## 🤝 Contributing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/Bricks_Manager.git
   cd Bricks_Manager
   ```

2. **Setup Development Environment**
   ```bash
   poetry install
   cp .env.example .env
   # Configure your .env file
   ```

3. **Run in Development Mode**
   ```bash
   make dev  # Docker
   # OR
   cd brick_manager && poetry run flask run  # Local
   ```

### Code Quality

- **Linting**: `poetry run pylint brick_manager/`
- **Type Checking**: Python type hints encouraged
- **Testing**: Add tests for new features
- **Documentation**: Update docs for significant changes

### Pull Request Process

1. Create feature branch (`git checkout -b feature/amazing-feature`)
2. Make changes with proper testing
3. Update documentation if needed
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push branch (`git push origin feature/amazing-feature`)
6. Open Pull Request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support & Help

- **Docker Issues**: See [DOCKER_README.md](DOCKER_README.md)
- **Health Check**: Visit `/health` endpoint for system status
- **Logs**: Use `make logs` or `docker compose logs`
- **Issues**: Open GitHub issues for bugs or feature requests

## 🎯 Roadmap

- [ ] **Web API**: REST API for mobile apps
- [ ] **Advanced Analytics**: Detailed collection insights
- [ ] **Multi-user Support**: User authentication and permissions
- [ ] **Cloud Storage**: Optional cloud backup integration
- [ ] **Mobile App**: Companion mobile application
- [ ] **Barcode Scanning**: Physical barcode integration

---

**Happy Building! 🧱✨**