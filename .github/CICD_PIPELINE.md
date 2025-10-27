# � CI/CD Pipeline Documentation

This document explains the automated CI/CD pipeline for the Bricks Manager project using GitHub Actions.

## 📋 Pipeline Overview

The CI/CD pipeline consists of four main jobs that run in sequence:

1. **🧪 Test** - Run code quality checks and tests
2. **🔨 Build & Push** - Build and push Docker images
3. **🔒 Security Scan** - Vulnerability scanning
4. **🚀 Deploy** - Deployment preparation (manual deployment)

## 🚦 Triggers

The workflow is triggered by:

- **Push to main/develop branches** - Full pipeline execution
- **Tags (v*.*.*)** - Release builds with semantic versioning
- **Pull Requests to main** - Test and build (no push/deploy)

## 🛠️ Job Details

### 1. 🧪 Test Job

**Purpose**: Ensure code quality and functionality before building Docker images.

**Steps**:
- Checkout code
- Set up Python 3.12
- Install Poetry for dependency management
- Install project dependencies
- Run linting with pylint
- Execute test suite with pytest

**Requirements**: All tests must pass for the pipeline to continue.

### 2. 🔨 Build & Push Job

**Purpose**: Build multi-architecture Docker images and push to Docker Hub.

**Features**:
- **Multi-platform builds** (linux/amd64, linux/arm64)
- **Smart tagging strategy**:
  - Branch names for development builds
  - Semantic versioning for releases (v1.2.3 → 1.2.3, 1.2, 1, latest)
  - PR numbers for pull request builds
- **Layer caching** using GitHub Actions cache
- **Metadata extraction** for proper labeling
- **Container testing** with health checks

**Tags Generated**:
```
kornhaas/bricks_manager:main
kornhaas/bricks_manager:latest (for main branch)
kornhaas/bricks_manager:v1.2.3 (for version tags)
kornhaas/bricks_manager:pr-123 (for pull requests)
```

### 3. 🔒 Security Scan Job

**Purpose**: Scan Docker images for vulnerabilities using Trivy.

**Features**:
- **Vulnerability scanning** of the built Docker image
- **SARIF output** integrated with GitHub Security tab
- **Automatic security alerts** for found vulnerabilities
- **CVE database** updates for latest threat intelligence

### 4. 🚀 Deploy Job

**Purpose**: Prepare for deployment and provide deployment guidance.

**Current Implementation**:
- Manual deployment with clear instructions
- Deployment readiness notification
- Step-by-step deployment guide

**Future Enhancements** (commented out):
- Automatic SSH deployment to production servers
- Integration with cloud platforms
- Rollback capabilities

## 🔧 Required Secrets

Configure these secrets in your GitHub repository settings:

### Docker Hub Integration
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_TOKEN` - Docker Hub access token (not password!)

### Optional: Automatic Deployment
- `DEPLOY_HOST` - Production server hostname/IP
- `DEPLOY_USER` - SSH username for deployment
- `DEPLOY_SSH_KEY` - Private SSH key for server access

## 📊 Workflow Status

### Success Indicators
- ✅ All tests pass
- ✅ Docker image builds successfully
- ✅ Security scan completes
- ✅ Image is pushed to registry

### Failure Scenarios
- ❌ Test failures (linting, unit tests)
- ❌ Docker build errors
- ❌ Security vulnerabilities (configurable)
- ❌ Registry push failures

## 🏷️ Image Tagging Strategy

### Development Builds
```
kornhaas/bricks_manager:main
kornhaas/bricks_manager:develop
```

### Release Builds
```
kornhaas/bricks_manager:v1.2.3    # Full version
kornhaas/bricks_manager:1.2       # Minor version
kornhaas/bricks_manager:1         # Major version
kornhaas/bricks_manager:latest    # Latest stable
```

### Pull Request Builds
```
kornhaas/bricks_manager:pr-123    # PR number
```

## 🚀 Using Built Images

### Latest Stable Release
```bash
docker pull kornhaas/bricks_manager:latest
docker run -p 5000:5000 -v ./data:/app/data kornhaas/bricks_manager:latest
```

### Specific Version
```bash
docker pull kornhaas/bricks_manager:v1.2.3
docker run -p 5000:5000 -v ./data:/app/data kornhaas/bricks_manager:v1.2.3
```

### Development Build
```bash
docker pull kornhaas/bricks_manager:main
docker run -p 5000:5000 -v ./data:/app/data kornhaas/bricks_manager:main
```

## 🔄 Pipeline Optimization

### Build Cache
- **GitHub Actions cache** for Docker layers
- **Multi-stage builds** for optimal image size
- **Dependency caching** for faster Poetry installs

### Parallel Execution
- Tests run independently of Docker builds where possible
- Security scanning runs in parallel with deployment preparation
- Multi-platform builds use BuildKit for efficiency

### Resource Management
- **Conditional job execution** (skip on PR for security/deploy)
- **Environment-specific deployments** with manual approval
- **Efficient resource usage** with optimized runners

## 🐛 Troubleshooting

### Common Issues

1. **Docker Hub Authentication Failure**
   ```
   Solution: Verify DOCKER_USERNAME and DOCKER_TOKEN secrets
   ```

2. **Test Failures**
   ```
   Solution: Check test output in the Test job logs
   ```

3. **Build Failures**
   ```
   Solution: Review Dockerfile and build context
   ```

4. **Security Scan Failures**
   ```
   Solution: Review Trivy output for vulnerabilities
   ```

### Debug Steps

1. **Check Action Logs**: Click on failed job for detailed logs
2. **Local Testing**: Run tests locally with `poetry run pytest`
3. **Docker Build**: Test Docker build locally with `docker build .`
4. **Secrets Verification**: Ensure all required secrets are set

## 📈 Monitoring & Metrics

### Available Metrics
- **Build success rate** over time
- **Build duration** trends
- **Security vulnerabilities** detected
- **Image size** optimization

### GitHub Integration
- **Status checks** on pull requests
- **Security alerts** in Security tab
- **Package registry** integration
- **Deployment environment** tracking

## 🔮 Future Enhancements

### Planned Improvements
- [ ] **Automatic deployment** to staging/production
- [ ] **Release automation** with changelog generation
- [ ] **Performance testing** integration
- [ ] **Multi-environment** deployment support
- [ ] **Slack/Discord** notifications for deployments
- [ ] **Rollback capabilities** for failed deployments

### Advanced Features
- [ ] **Blue-green deployments** for zero downtime
- [ ] **Canary releases** for gradual rollouts
- [ ] **Infrastructure as Code** with Terraform
- [ ] **Kubernetes** deployment manifests
- [ ] **Helm charts** for Kubernetes deployments

## 📞 Support

For pipeline issues:
1. Check the **Actions tab** in GitHub for detailed logs
2. Review **secrets configuration** in repository settings
3. Verify **branch protection rules** if applicable
4. Open an **issue** with pipeline logs for support