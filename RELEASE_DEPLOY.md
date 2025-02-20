# Release and Deployment Process

This document explains the automated release and deployment process for the Python Virtual Environment Manager package.

## Workflow Overview

The process is split into two separate workflows:

1. **Release Workflow** (`release.yml`)
2. **Deploy Workflow** (`deploy.yml`)

### Release Workflow

The release workflow handles building and versioning of the package.

#### Triggering a Release
1. Go to GitHub Actions
2. Select "Release Workflow"
3. Click "Run workflow"
4. Choose release type:
   - `production`: For main branch releases
   - `beta`: For development releases

#### What the Release Workflow Does
1. Sets up Python environment
2. Manages version using bump2version
   - Production: Increments patch version (X.Y.Z)
   - Beta: Adds beta suffix (X.Y.Z.beta)
3. Builds distribution package
4. Stores artifacts in:
   - Production: `distribution/release/`
   - Beta: `distribution/beta/`

### Deploy Workflow

The deploy workflow handles publishing packages to PyPI or TestPyPI.

#### Triggering a Deployment
1. Go to GitHub Actions
2. Select "Deploy Package"
3. Click "Run workflow"
4. Choose:
   - Deploy Target:
     * `production-pypi`: Official PyPI repository
     * `test-pypi`: TestPyPI repository

#### What the Deploy Workflow Does
1. Lists all available artifacts with details:
   - Name (production-release or beta-release)
   - Creation date
   - Size
2. Downloads selected artifact
3. Validates deployment combination
   - Prevents deploying beta releases to production PyPI
4. Publishes to chosen repository

## Required Secrets

The following secrets must be configured in your GitHub repository:

- For Production PyPI:
  * `PYPI_USERNAME`
  * `PYPI_PASSWORD`

- For TestPyPI:
  * `TEST_PYPI_USERNAME`
  * `TEST_PYPI_PASSWORD`

## Version Management

Versions are managed automatically using bump2version:

- Production releases:
  * Format: X.Y.Z
  * Example: 1.2.3

- Beta releases:
  * Format: X.Y.Z.beta
  * Example: 1.2.3.beta

## Best Practices

1. **Release Process**
   - Create beta releases first for testing
   - Verify beta functionality in TestPyPI
   - Only deploy to production after thorough testing

2. **Version Control**
   - Keep main branch stable
   - Use feature branches for development
   - Merge to main only for production releases

3. **Deployment**
   - Always review artifact details before deployment
   - Verify the correct combination of artifact and target
   - Monitor deployment status and package visibility

## Troubleshooting

1. **Release Issues**
   - Check git configuration
   - Verify branch permissions
   - Ensure version files are properly configured

2. **Deployment Issues**
   - Verify correct secrets are configured
   - Check if version already exists in repository
   - Ensure package name is available

3. **Artifact Issues**
   - Verify release workflow completed successfully
   - Check artifact retention period
   - Ensure artifact size is within limits
