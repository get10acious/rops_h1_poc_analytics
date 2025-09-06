# LoyaltyAnalytics - Natural Language Analytics POC

A complete implementation of an intelligent admin homepage with natural language analytics capabilities. This project demonstrates a fully functional real-time analytics chatbot that can query loyalty program databases and generate visualizations using natural language, built with modern MCP (Model Context Protocol) integration.

## 🎯 Project Overview

This is a **working implementation** of a dynamic, intelligent "mission control" for loyalty program analytics. The system allows non-technical users to ask plain English questions about merchants, users, and redemption data, receiving interactive data visualizations in real-time.

### Key Features

- **Natural Language Queries**: Ask questions like "Show me the top 10 merchants by redemption volume this month"
- **Interactive Chart.js Visualizations**: Automatic chart and table generation with export/fullscreen capabilities
- **Complete Tool Ecosystem**: Database queries, Python code execution, and MCP-UI visualization generation
- **Real-time Chat Interface**: WebSocket-based communication for instant responses
- **Database Integration**: Direct PostgreSQL connection with loyalty program data
- **MCP Integration**: Model Context Protocol with automated PostgreSQL Toolbox setup
- **Advanced AI Agent**: LangGraph-based ReAct agent with multi-iteration reasoning and composite tools
- **Code Sandbox**: Python code execution for custom analytics and data processing
- **Environment-Based Configuration**: Flexible configuration using environment variables
- **Automated Setup**: One-command setup for MCP servers and database initialization

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    MCP     ┌─────────────────┐
│   Frontend      │◄──────────────►│    Backend      │◄──────────►│   MCP Servers    │
│   (React)       │                 │   (FastAPI)     │            │                 │
│                 │                 │                 │            │ • DB Toolbox    │
│ Chat Interface  │                 │ ReAct Agent     │            │ • MCP-UI        │
│ MCPUI UIResource|
|  Charts         │                 │ WebSocket Hub   │            │                 │
└─────────────────┘                 └─────────────────┘            └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   PostgreSQL    │
                                    │                 │
                                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd rops_h1_poc_analytics
```

### 2. Install Dependencies

```bash
# Install all dependencies (backend + frontend)
make install

# Or install individually:
make setup-backend    # Creates .env file automatically
make setup-frontend
```

### 3. Setup MCP Servers

```bash
# Download and configure MCP Toolbox
make setup-mcp
```

### 4. Initialize Database

```bash
# Start PostgreSQL and initialize with sample data
make docker-up
make init-db
```

### 5. Start Development Environment

```bash
# Start both backend and frontend
make start
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## ✨ Recent Updates

This project has been updated with several key improvements:

### 🔧 Enhanced Configuration
- **Environment-Based Setup**: All configuration now uses environment variables
- **Automatic .env Creation**: Template file created during setup
- **Flexible Database Configuration**: Individual postgres connection parameters

### 🤖 Improved MCP Integration  
- **Automated MCP Setup**: `mcp_setup.py` downloads and configures PostgreSQL Toolbox
- **Working MCP Configuration**: Uses proven format from mcpui-sandbox-chat
- **Environment-Driven Config**: MCP servers configured from environment variables

### 🗄️ Database Improvements
- **Loyalty Program Schema**: Complete loyalty program database with realistic data
- **Environment-Driven Init**: Database initialization uses environment settings
- **Better Error Handling**: Improved logging and error management

### 🚀 Streamlined Setup
- **One-Command Setup**: `make install && make setup-mcp && make init-db && make start`
- **Automatic Downloads**: MCP Toolbox downloaded automatically
- **Consistent Naming**: Fixed case sensitivity issues across the codebase

## 📋 Original Challenge Brief

This project demonstrates a complete implementation of the **MCP UI Chat Analytics** system. It serves as both a working example and a foundation for further development.

### Learning Objectives

- Architect a real-time, full-stack application using WebSockets
- Integrate and orchestrate multiple MCP servers
- Translate natural language queries into database queries and visualizations
- Utilize AI agents to accelerate development

### Competencies Assessed

- **Description & Delegation**: Clear, context-rich instructions for complex systems
- **Discernment & Diligence**: Critical evaluation of generated code and queries
- **Problem-solving Style**: Adaptive vs. Innovative approaches

## 🛠️ Development Workflow

### AI-Assisted Development Pattern

This template follows a structured approach for AI-assisted development:

1. **Plan First**: Provide context and collaboratively refine architecture
2. **IDE Configuration**: Use AI to configure MCP toolchain
3. **TDD Setup**: Convert plans into failing tests
4. **Implementation**: Build minimal code to pass tests
5. **Integration**: Connect frontend and backend
6. **Validation**: End-to-end testing and documentation

### Available Commands

```bash
# Development
make install          # Install all dependencies
make setup-backend    # Setup Python environment
make setup-frontend   # Setup Node.js dependencies
make setup-mcp        # Configure MCP servers

# Running
make start            # Start both servers
make start-backend    # Start backend only
make start-frontend   # Start frontend only
make dev              # Initialize DB and start servers

# Testing
make test             # Run all tests
make test-backend     # Run backend tests
make test-frontend    # Run frontend tests
make test-mcp         # Test MCP integration

# Database
make init-db          # Initialize with sample data
make docker-up        # Start PostgreSQL
make docker-down      # Stop PostgreSQL
make check-db         # Test database connection

# Utilities
make clean            # Clean build artifacts
make status           # Check service status
make logs-backend     # View backend logs
```

## 📁 Project Structure

```
rops_h1_poc_analytics/
├── backend/                    # FastAPI backend
│   ├── models/                # Database models
│   ├── tests/                 # Backend tests
│   ├── mcp_servers/           # MCP server configurations
│   ├── notebooks/             # Jupyter notebooks for testing
│   ├── main.py                # FastAPI application
│   ├── langgraph_agent.py     # ReAct agent implementation
│   ├── mcp_multi_client.py    # MCP client manager
│   ├── websocket_manager.py   # WebSocket handling
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   ├── types/             # TypeScript types
│   │   └── app/               # Next.js app directory
│   ├── package.json           # Node.js dependencies
│   └── next.config.ts         # Next.js configuration
├── docs/                      # Documentation
│   ├── AI_GUIDE.md            # AI assistant instructions
│   ├── CHALLENGE_BRIEF.md     # Hackathon challenge
│   ├── DEVELOPMENT_PATTERNS.md # Coding standards
│   └── MCP_INTEGRATION_GUIDE.md # MCP setup guide
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker services
├── Makefile                   # Development commands
└── README.md                  # This file
```

## 🗄️ Database Schema

The template includes a sample analytics database 

## 🤖 AI Assistant Integration

This template is designed to work seamlessly with AI coding assistants. Key features:

- **Comprehensive Context**: Detailed system documentation for AI understanding
- **Structured Prompts**: Pre-written prompts for common development tasks
- **Clear Patterns**: Consistent coding patterns and architecture
- **Progressive Implementation**: Step-by-step development approach

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://analytics:password@localhost:5432/analytics_db
REDIS_URL=redis://localhost:6379

# API Keys (for production)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# Development
LOG_LEVEL=INFO
DEBUG=true
```

### MCP Server Configuration

The template includes pre-configured MCP servers:
- **Database Toolbox**: For PostgreSQL queries
- **MCP UI**: For visualization generation

## 🧪 Testing

### Backend Tests

```bash
# Run all backend tests
make test-backend

# Run specific test categories
cd backend && python -m pytest tests/ -v
cd backend && python -m pytest tests/test_websocket.py -v
cd backend && python -m pytest tests/test_orchestration.py -v
```

### Frontend Tests

```bash
# Run frontend tests
make test-frontend

# Run component tests
cd frontend && npm test
```

### Integration Tests

```bash
# Test MCP integration
make test-mcp

# Test MCP UI integration
make test-mcp-ui
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

- Configure proper environment variables
- Set up SSL certificates
- Configure reverse proxy (nginx)
- Set up monitoring and logging
- Configure database backups

## 📚 Documentation

- [AI Assistant Guide](docs/AI_GUIDE.md) - Instructions for AI coding assistants
- [Challenge Brief](docs/CHALLENGE_BRIEF.md) - Detailed hackathon requirements
- [Development Patterns](docs/DEVELOPMENT_PATTERNS.md) - Coding standards and patterns
- [MCP Integration Guide](docs/MCP_INTEGRATION_GUIDE.md) - MCP server setup and usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the development patterns
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in the `docs/` directory
- Review the troubleshooting section in the AI Guide
- Create an issue in the repository

## 🙏 Acknowledgments

- [Database Toolbox](https://googleapis.github.io/genai-toolbox/) for multi-database tool integration

- [LLM Sandbox](https://github.com/vndee/llm-sandbox) for secure code execution and agent tool orchestration
- [MCP-UI Specification](https://github.com/idosal/mcp-ui) for unified tool and UI protocol 
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [FastMCP](https://gofastmcp.com/integrations/fastapi) to build MCP servers and clients 
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
