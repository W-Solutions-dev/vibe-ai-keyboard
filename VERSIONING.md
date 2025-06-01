# Versioning & Release Strategy

## Overview

This document outlines the versioning and release strategy for the Speech-to-Text Keyboard project. We follow a simple but effective approach that balances stability with rapid development.

## Semantic Versioning

We use [Semantic Versioning](https://semver.org/) (SemVer) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes or major feature overhauls
- **MINOR**: New features in a backwards-compatible manner
- **PATCH**: Backwards-compatible bug fixes

Current version: `0.2.1` (Pre-release/Beta)

## Branch Strategy

### Main Branches

```
main (stable)
  ├── develop (active development)
  ├── feature/* (new features)
  ├── fix/* (bug fixes)
  └── release/* (release preparation)
```

### Branch Descriptions

- **`main`**: Production-ready code. All commits are tagged releases.
- **`develop`**: Integration branch for features. Always ahead of main.
- **`feature/*`**: New features (e.g., `feature/voice-ui-control`)
- **`fix/*`**: Bug fixes (e.g., `fix/audio-device-detection`)
- **`release/*`**: Release preparation (e.g., `release/v1.0.0`)

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/voice-feedback

# Work on feature
git add .
git commit -m "feat: add text-to-speech feedback system"

# Push and create PR
git push origin feature/voice-feedback
```

### 2. Bug Fixes
```bash
# For development fixes
git checkout -b fix/audio-latency develop

# For production hotfixes
git checkout -b fix/critical-bug main
```

### 3. Release Process
```bash
# Create release branch
git checkout -b release/v1.0.0 develop

# Update version numbers
# - setup.py
# - __version__ in main module
# - README.md badges

# Create PR to main
git push origin release/v1.0.0
```

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Test additions/modifications
- **chore**: Maintenance tasks

### Examples
```bash
feat(commands): add screenshot analysis for UI control
fix(audio): resolve microphone detection on Ubuntu 22.04
docs: update installation instructions for Docker
refactor(logging): implement structured JSON logging
```

## Release Checklist

### Pre-release
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Security audit completed

### Release
1. Merge release branch to main
2. Tag the release: `git tag -a v1.0.0 -m "Release version 1.0.0"`
3. Push tags: `git push origin v1.0.0`
4. Create GitHub release with changelog

### Post-release
- [ ] Publish to PyPI
- [ ] Update Docker images
- [ ] Announce on project channels
- [ ] Merge main back to develop

## Version History Format

Maintain a `CHANGELOG.md` file:

```markdown
# Changelog

## [1.0.0] - 2024-01-15
### Added
- Voice UI control with screenshot analysis
- Text-to-speech feedback system

### Changed
- Improved audio latency by 50%

### Fixed
- Microphone detection on Ubuntu 22.04
```

## Backporting Policy

- Security fixes: Backport to all supported versions
- Critical bugs: Backport to latest minor version
- Features: No backporting (develop only)

## Deprecation Policy

1. Mark as deprecated in code with warnings
2. Document in CHANGELOG and README
3. Maintain for 2 minor versions
4. Remove in next major version

## Quick Commands

```bash
# View current version
git describe --tags --always

# List all versions
git tag -l

# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push specific tag
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0
```

## First Release Milestone

Target for v1.0.0:
- [x] Core speech-to-text functionality
- [x] Security-first command system
- [x] Comprehensive logging
- [ ] Voice UI control
- [ ] Text-to-speech feedback
- [ ] PyPI package
- [ ] Docker image
- [ ] Documentation website 