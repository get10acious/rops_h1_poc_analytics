# RewardOps AI Fluency - Makefile for project management

.PHONY: help install install_uv run setup-backend setup-frontend setup-mcp init-db start-backend start-frontend start dev clean test

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Variables
VENV_NAME := venv
PYTHON ?= python3
UV ?= uv
NOTEBOOKS_DIR := backend/notebooks

COMMAND ?= "--version"

help: ## Show this help message
	@echo "$(CYAN)RewardOps AI Fluency - Available Commands:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

install_uv: ## Install uv package manager
	@echo "$(CYAN)Installing uv package manager...$(RESET)"
	@if command -v uv >/dev/null 2>&1; then \
		echo "$(GREEN)>>> uv is already installed at: $(shell which uv)$(RESET)"; \
		uv --version; \
	else \
		echo "$(YELLOW)>>> Installing uv...$(RESET)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)>>> uv installed successfully!$(RESET)"; \
		echo "$(YELLOW)>>> Please restart your terminal or run: source ~/.bashrc$(RESET)"; \
	fi

install: install_uv ## Install all dependencies (backend + frontend)
	@echo "$(CYAN)Installing all dependencies...$(RESET)"
	$(MAKE) setup-backend
	$(MAKE) setup-frontend
	@echo "$(GREEN)All dependencies installed successfully!$(RESET)"

setup-backend: ## Setup Python virtual environment and install backend dependencies
	@echo "$(CYAN)Setting up backend...$(RESET)"
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "$(RED)>>> uv not found. Please run 'make install_uv' first.$(RESET)"; \
		exit 1; \
	fi
	cd backend && $(UV) venv $(VENV_NAME) --python $(PYTHON)
	cd backend && . $(VENV_NAME)/bin/activate && $(UV) pip install --upgrade pip
	cd backend && . $(VENV_NAME)/bin/activate && $(UV) pip install -r requirements.txt
	@echo "$(GREEN)Backend setup complete!$(RESET)"

setup-mcp: ## Setup MCP servers (PostgreSQL Toolbox and Vizro)
	@echo "$(CYAN)Setting up MCP servers...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && python -c "import asyncio; from mcp_multi_client import mcp_manager; asyncio.run(mcp_manager.initialize())"
	@echo "$(GREEN)MCP setup complete!$(RESET)"

setup-frontend: ## Setup Node.js dependencies for frontend
	@echo "$(CYAN)Setting up frontend...$(RESET)"
	cd frontend && npm install
	cd frontend && npm install ws @types/ws lucide-react recharts
	@echo "$(GREEN)Frontend setup complete!$(RESET)"

init-db: ## Initialize database with sample data
	@echo "$(CYAN)Initializing database...$(RESET)"
	@if ! docker ps | grep rewardops-postgres >/dev/null; then \
		echo "$(YELLOW)>>> Starting PostgreSQL container...$(RESET)"; \
		docker-compose up -d postgres; \
		sleep 10; \
	fi
	@echo "$(GREEN)Database initialized successfully!$(RESET)"

start-backend: ## Start the FastAPI backend server
	@echo "$(CYAN)Starting backend server...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && python main.py

run: ## Run a custom command in the backend environment
	@echo "$(CYAN)Running command: $(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && $(COMMAND)

start-frontend: ## Start the Next.js frontend development server
	@echo "$(CYAN)Starting frontend server...$(RESET)"
	cd frontend && npm run dev

start: ## Start both backend and frontend servers concurrently
	@echo "$(CYAN)Starting full application...$(RESET)"
	@echo "$(YELLOW)Backend will start on http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Frontend will start on http://localhost:3000$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop both servers$(RESET)"
	$(MAKE) start-backend & $(MAKE) start-frontend

dev: init-db start ## Initialize database and start development servers

test-backend: ## Run backend tests
	@echo "$(CYAN)Running backend tests...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && pytest tests/ -v

test-mcp: ## Test MCP integration with PostgreSQL Toolbox
	@echo "$(CYAN)Testing MCP integration...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && python -c "import asyncio; from test_mcp_integration import test_mcp_connection; asyncio.run(test_mcp_connection())"

test-mcp-ui: ## Test MCP UI integration
	@echo "$(CYAN)Testing MCP UI integration...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && python test_mcp_ui_integration.py

test-frontend: ## Run frontend tests
	@echo "$(CYAN)Running frontend tests...$(RESET)"
	cd frontend && npm test

test: ## Run all tests
	$(MAKE) test-backend
	$(MAKE) test-frontend

clean: ## Clean up build artifacts and dependencies
	@echo "$(CYAN)Cleaning up...$(RESET)"
	rm -rf backend/$(VENV_NAME)
	rm -rf backend/__pycache__
	rm -rf backend/**/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	@echo "$(GREEN)Cleanup complete!$(RESET)"

check-db: ## Check database connection and show sample data
	@echo "$(CYAN)Checking database connection...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && python -c "import asyncio; from database_operations import db_ops; asyncio.run(db_ops.test_connection())"

logs-backend: ## Show backend server logs
	@echo "$(CYAN)Backend server logs:$(RESET)"
	tail -f backend/app.log

status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(RESET)"
	@echo "$(YELLOW)PostgreSQL:$(RESET) $(shell docker ps | grep rewardops-postgres >/dev/null && echo '$(GREEN)Running$(RESET)' || echo '$(RED)Not Running$(RESET)')"
	@echo "$(YELLOW)Backend:$(RESET) $(shell lsof -ti:8000 >/dev/null && echo '$(GREEN)Running$(RESET)' || echo '$(RED)Not Running$(RESET)')"
	@echo "$(YELLOW)Frontend:$(RESET) $(shell lsof -ti:3000 >/dev/null && echo '$(GREEN)Running$(RESET)' || echo '$(RED)Not Running$(RESET)')"

docker-up: ## Start PostgreSQL database in Docker
	@echo "$(CYAN)Starting PostgreSQL database...$(RESET)"
	docker-compose up -d postgres
	@echo "$(GREEN)Database started!$(RESET)"

docker-down: ## Stop PostgreSQL database
	@echo "$(CYAN)Stopping PostgreSQL database...$(RESET)"
	docker-compose down
	@echo "$(GREEN)Database stopped!$(RESET)"

docker-logs: ## Show PostgreSQL database logs
	docker-compose logs -f postgres

docker-full: ## Start all services with Docker Compose
	@echo "$(CYAN)Starting all services with Docker Compose...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)All services started!$(RESET)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(RESET)"

#------------------------------------------------------
# Jupyter Notebooks
#------------------------------------------------------

# Start Jupyter Notebook
.PHONY: jupyter
jupyter: ## Start Jupyter Notebook
	@echo "$(CYAN)>>> Starting Jupyter Notebook...$(RESET)"
	@echo "$(YELLOW)>>> Make sure to select 'rewardops-analytics' kernel in your notebooks$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && jupyter notebook --notebook-dir=$(NOTEBOOKS_DIR)

# Start Jupyter Lab
.PHONY: jupyter-lab
jupyter-lab: ## Start Jupyter Lab
	@echo "$(CYAN)>>> Starting Jupyter Lab...$(RESET)"
	@echo "$(YELLOW)>>> Make sure to select 'rewardops-analytics' kernel in your notebooks$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && jupyter lab --notebook-dir=$(NOTEBOOKS_DIR)

# Install Jupyter kernel for this environment
.PHONY: install-kernel
install-kernel: ## Install Jupyter kernel for this environment
	@echo "$(CYAN)>>> Installing Jupyter kernel for rewardops-analytics environment...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && $(UV) pip install ipykernel
	cd backend && . $(VENV_NAME)/bin/activate && python -m ipykernel install --user --name=rewardops-analytics --display-name="RewardOps Analytics"
	@echo "$(GREEN)>>> Kernel installed successfully!$(RESET)"
	@echo "$(YELLOW)>>> Available kernels:$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && jupyter kernelspec list

# List available Jupyter kernels
.PHONY: list-kernels
list-kernels: ## List available Jupyter kernels
	@echo "$(CYAN)>>> Available Jupyter kernels:$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && jupyter kernelspec list

# Install Jupyter dependencies
.PHONY: setup-jupyter
setup-jupyter: ## Install Jupyter dependencies
	@echo "$(CYAN)>>> Installing Jupyter dependencies...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && $(UV) pip install jupyter jupyterlab ipykernel
	@echo "$(GREEN)>>> Jupyter dependencies installed!$(RESET)"
	$(MAKE) install-kernel

# Run MCP UI integration tests in Jupyter
.PHONY: test-notebook
test-notebook: ## Run MCP UI integration tests in Jupyter
	@echo "$(CYAN)>>> Running MCP UI integration tests in Jupyter...$(RESET)"
	cd backend && . $(VENV_NAME)/bin/activate && jupyter nbconvert --to notebook --execute $(NOTEBOOKS_DIR)/mcp_ui_integration_tests.ipynb --output $(NOTEBOOKS_DIR)/mcp_ui_integration_tests_executed.ipynb

# Default target
.DEFAULT_GOAL := help
