# � GitHub Actions Workflow Status

This document provides an overview of all GitHub Actions workflows in the Bricks Manager project.

## 🔄 Active Workflows

### 1. 🐳 Docker Build and Deploy
[![Docker Image CI](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/docker-image.yml)

**Purpose**: Complete CI/CD pipeline with Docker image building, testing, and deployment preparation.

**Triggers**: 
- Push to `main`, `develop` branches
- Version tags (`v*.*.*`)
- Pull requests to `main`

**Jobs**:
- 🧪 **Test** - Run linting and tests
- 🔨 **Build & Push** - Multi-platform Docker image build
- 🔒 **Security Scan** - Vulnerability scanning with Trivy
- 🚀 **Deploy** - Deployment preparation

### 2. 🧪 Python Tests
[![Python Tests](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/python-app.yml/badge.svg)](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/python-app.yml)

**Purpose**: Fast feedback on code changes with comprehensive testing across multiple Python versions.

**Triggers**: 
- Push/PR with Python file changes
- Changes to `pyproject.toml`, `poetry.lock`, or test files

**Features**:
- Multi-version testing (Python 3.11, 3.12)
- Code coverage reporting
- Integration with Codecov
- Fast dependency caching

### 3. 🧹 Code Quality (Pylint)
[![Pylint](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/pylint.yml/badge.svg)](https://github.com/Kornhaas/Bricks_Manager/actions/workflows/pylint.yml)

**Purpose**: Continuous code quality monitoring with linting across multiple Python versions.

**Triggers**: 
- Push/PR with Python file changes
- Changes to `pyproject.toml` or `poetry.lock`

**Features**:
- Multi-version linting (Python 3.11, 3.12)
- Quality score reporting
- Non-blocking warnings for code quality issues
- Detailed reports as artifacts

## 🎯 Workflow Strategy

### Parallel Execution
The workflows are designed to run efficiently:

```
┌─ 🧹 Code Quality ─────┐
│  (Fast feedback)      │
├─ 🧪 Python Tests ─────┤ ─── Parallel execution for quick feedback
│  (Multi-version)      │
└─ 🐳 Docker Build ─────┘
   (Complete pipeline)
```

### Trigger Optimization
- **Path-based triggers** prevent unnecessary runs
- **Python-specific workflows** only run on relevant changes
- **Docker workflow** runs on all changes for complete validation

### Caching Strategy
- **Poetry dependencies** cached across runs
- **Docker layers** cached using GitHub Actions cache
- **Multi-version cache** keys for different Python versions

## 📈 Workflow Performance

### Expected Run Times
- 🧹 **Code Quality**: ~2-3 minutes
- 🧪 **Python Tests**: ~3-5 minutes  
- 🐳 **Docker Build**: ~8-12 minutes (includes multi-platform build)

### Resource Optimization
- **Conditional job execution** based on event type
- **Matrix builds** for efficient multi-version testing
- **Artifact retention** (30 days) for debugging

## 🔧 Configuration

### Required Repository Secrets
```
DOCKER_USERNAME     # Docker Hub username
DOCKER_TOKEN        # Docker Hub access token
```

### Optional Secrets (for automatic deployment)
```
DEPLOY_HOST         # Production server hostname
DEPLOY_USER         # SSH username for deployment  
DEPLOY_SSH_KEY      # Private SSH key for server access
```

### Branch Protection Rules (Recommended)
```yaml
main:
  required_status_checks:
    - "🧪 Test Python 3.12"
    - "🔨 Build & Push Docker Image"
    - "🔍 Lint Python Code"
  enforce_admins: true
  required_pull_request_reviews:
    required_approving_review_count: 1
```

## 🏷️ Generated Artifacts

### Docker Images
Available on Docker Hub: `kornhaas/bricks_manager`

**Tags**:
- `latest` - Latest stable release (main branch)
- `main` - Latest development build
- `v1.2.3` - Specific version releases
- `pr-123` - Pull request builds

### Test Reports
- **Coverage reports** uploaded to Codecov
- **Pylint reports** as workflow artifacts
- **Test results** for debugging failures

### Security Reports
- **Trivy vulnerability scans** in GitHub Security tab
- **SARIF format** for integration with security tools

## 🐛 Troubleshooting

### Common Issues

1. **Docker Hub Authentication**
   ```bash
   # Check secrets configuration
   Settings → Secrets and variables → Actions
   ```

2. **Test Failures**
   ```bash
   # Run tests locally to debug
   poetry run pytest brick_manager/tests/ -v
   ```

3. **Linting Issues**
   ```bash
   # Check code quality locally
   poetry run pylint brick_manager/
   ```

4. **Build Cache Issues**
   ```bash
   # Clear GitHub Actions cache
   Settings → Actions → Caches → Delete relevant caches
   ```

### Debug Commands

```bash
# Local testing equivalent to CI
poetry install --with dev
poetry run pylint brick_manager/
poetry run pytest brick_manager/tests/ --cov=brick_manager
docker build -t test-image .
```

## 📊 Monitoring & Alerts

### GitHub Integration
- **Status checks** on pull requests
- **Email notifications** for failed workflows
- **Security alerts** for vulnerabilities
- **Deployment notifications** in pull requests

### External Integrations
- **Codecov** for coverage tracking
- **Docker Hub** for image hosting
- **GitHub Security** for vulnerability management

## 🔮 Future Enhancements

### Planned Improvements
- [ ] **Performance testing** in CI pipeline
- [ ] **End-to-end testing** with test containers
- [ ] **Slack/Discord** notifications for deployments
- [ ] **Automatic dependency updates** with Dependabot
- [ ] **Release notes** generation from commits

### Advanced Features
- [ ] **Staging environment** deployments
- [ ] **Blue-green deployment** strategy
- [ ] **Canary releases** for gradual rollouts
- [ ] **Infrastructure as Code** validation
- [ ] **Multi-cloud** deployment support

## 📞 Support

For workflow issues:
1. Check **Actions tab** for detailed logs
2. Review **workflow files** in `.github/workflows/`
3. Verify **secrets configuration** in repository settings
4. Open **issue** with workflow logs for debugging assistance

---

*All workflows are optimized for speed, reliability, and developer experience. Regular monitoring ensures optimal performance and quick issue resolution.*