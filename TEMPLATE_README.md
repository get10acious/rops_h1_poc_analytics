# Template Management Guide

This document provides instructions for managing the RewardOps Analytics POC Template repository.

## Overview

This repository serves as a cookie-cutter template for students to build natural language analytics systems with MCP integration. The template includes comprehensive documentation, boilerplate code, and AI assistant guidance.

## Template Management Commands

Use the `Makefile.github` to manage the template repository:

### Setup and Validation

```bash
# Complete template setup (validates structure and files)
make -f Makefile.github full-setup

# Validate template structure and required files
make -f Makefile.github validate-template
```

### Repository Management

```bash
# Create GitHub repository (run once)
make -f Makefile.github create-template-repo

# Push code to GitHub template repository
make -f Makefile.github push-template

# Update existing template with new changes
make -f Makefile.github update-template
```

### Template Feature

```bash
# Enable template feature on GitHub (manual step required)
make -f Makefile.github enable-template
```

This will open the GitHub repository settings where you need to:
1. Go to the repository settings
2. Scroll down to "Repository name" section
3. Check "Template repository"
4. Save changes

### Cleanup

```bash
# Clean up template files (removes .github, template.json, .templateignore)
make -f Makefile.github clean-template
```

## Initial Setup Process

1. **Initialize Git Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: RewardOps Analytics POC Template"
   ```

2. **Set Up Template:**
   ```bash
   make -f Makefile.github full-setup
   ```

3. **Create GitHub Repository:**
   ```bash
   make -f Makefile.github create-template-repo
   ```

4. **Push to GitHub:**
   ```bash
   make -f Makefile.github push-template
   ```

5. **Enable Template Feature:**
   ```bash
   make -f Makefile.github enable-template
   ```

## Template Structure

The template includes:

- **Documentation**: Comprehensive guides for AI assistants and students
- **Backend**: FastAPI boilerplate with WebSocket and MCP integration
- **Frontend**: React/TypeScript boilerplate with Tailwind CSS
- **Database**: PostgreSQL setup with sample RewardOps data
- **Docker**: Containerization for all services
- **GitHub**: Workflows, issue templates, and PR templates
- **Development**: Makefiles for easy development workflow

## Files Excluded from Template

The following files are excluded when users create repositories from this template (via `.templateignore`):

- `Makefile.github` - Template management commands
- `TEMPLATE_README.md` - This file
- `.github/` - GitHub workflows and templates
- `template.json` - Template metadata
- `.templateignore` - Template ignore file

## Updating the Template

When you make changes to the template:

1. **Make your changes** to the source files
2. **Test locally** to ensure everything works
3. **Update the template:**
   ```bash
   make -f Makefile.github update-template
   ```

## Student Usage

Students will:

1. Click "Use this template" on GitHub
2. Create a new repository from the template
3. Clone their new repository
4. Follow the `README.md` for setup instructions
5. Use the `docs/AI_GUIDE.md` for AI assistant collaboration
6. Follow the `docs/CHALLENGE_BRIEF.md` for implementation guidance

## Repository Information

- **Template Repository**: https://github.com/get10acious/rewardops-analytics-poc-template
- **Organization**: get10acious
- **Template Name**: rewardops-analytics-poc-template
- **Description**: Cookie-cutter template for building natural language analytics systems with MCP integration

## Troubleshooting

### GitHub CLI Issues
- Ensure you're authenticated: `gh auth status`
- Check permissions to the organization
- Verify repository access

### Template Feature Not Available
- Make sure you have admin/write permissions to the repository
- Check that the repository is public
- Verify the template feature is enabled in repository settings

### Validation Failures
- Run `make -f Makefile.github validate-template` to check for missing files
- Ensure all required directories and files are present
- Check file permissions and structure
