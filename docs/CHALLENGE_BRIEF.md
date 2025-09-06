# MCP UI Chat Analytics Hackathon Challenge Brief

## 🎯 Mission Statement

Transform an admin homepage from a static welcome screen into a dynamic, intelligent "mission control" for business analytics. Build a high-fidelity, working Proof of Concept (POC) that allows non-technical users to ask plain English questions and receive interactive data visualizations in real-time.

## 📋 Challenge Overview

### Business Context
- **Company**: Analytics Platform - A data analytics platform
- **Current State**: Static admin homepage, business team bottlenecked by engineering dependencies
- **Vision**: Real-time, self-service analytics for business users
- **Timeline**: One-day hackathon implementation

### Success Criteria
- ✅ Users can ask natural language questions (e.g., "Show me the top 10 merchants by redemption volume this month")
- ✅ System queries real database and returns accurate results
- ✅ Interactive data visualizations are generated and displayed
- ✅ Real-time chat interface provides instant responses
- ✅ System handles edge cases and provides helpful error messages

## 🏗️ Technical Requirements

### Architecture Components

#### 1. Backend Service (FastAPI/Node.js)
- **Role**: MCP Host & Orchestrator
- **Responsibilities**:
  - WebSocket communication with frontend
  - MCP client management (Database Toolbox + Vizro)
  - ReAct agent orchestration using LangGraph
  - Query processing and response handling

#### 2. ReAct Agent (LangGraph)
- **Role**: Natural Language Query Processor
- **Flow**:
  1. **Reason**: Analyze user intent and determine required actions
  2. **Act**: Execute database queries using MCP Database Toolbox
  3. **Observe**: Process query results and determine next steps
  4. **Act**: Generate visualizations using Vizro MCP
  5. **Respond**: Return structured response to frontend

#### 3. Frontend Chatbot (React)
- **Role**: Real-time Analytics Interface
- **Features**:
  - WebSocket connection to backend
  - Message history and display
  - Vizro dashboard rendering
  - User input handling and validation

#### 4. MCP Integration
- **Database Toolbox**: PostgreSQL query execution
- **Vizro MCP**: Chart and dashboard generation
- **Communication**: Standard MCP protocol

## 📊 Database Schema

### Core Tables

```sql
-- Merchants
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    total_points INTEGER DEFAULT 0,
    tier VARCHAR(50) DEFAULT 'bronze'
);

-- Redemptions
CREATE TABLE redemptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    merchant_id INTEGER REFERENCES merchants(id),
    amount DECIMAL(10,2) NOT NULL,
    points_used INTEGER NOT NULL,
    redemption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed',
    transaction_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Campaign Participation
CREATE TABLE user_campaigns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    campaign_id INTEGER REFERENCES campaigns(id),
    points_earned INTEGER DEFAULT 0,
    participation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, campaign_id)
);
```

### Sample Data Queries

#### Business Questions to Support
1. **Merchant Analytics**
   - "Show me the top 10 merchants by redemption volume"
   - "Which merchants have the highest average redemption value?"
   - "What are the most popular merchant categories?"

2. **User Analytics**
   - "How many users redeemed rewards this month?"
   - "What's the average redemption value per user?"
   - "Show me user engagement by tier"

3. **Campaign Analytics**
   - "Which campaigns are performing best?"
   - "How many users participated in each campaign?"
   - "What's the ROI for our recent campaigns?"

4. **Trend Analysis**
   - "Show me redemption trends over the last 6 months"
   - "What's the growth rate of our user base?"
   - "Which time periods have the highest redemption activity?"

## 🛠️ Implementation Phases

### Phase 1: Foundation (2-3 hours)
1. **Environment Setup**
   - Clone template repository
   - Install dependencies (Docker, Python, Node.js)
   - Configure MCP servers
   - Initialize database with sample data

2. **Basic WebSocket Communication**
   - Backend WebSocket endpoint
   - Frontend WebSocket client
   - Message protocol definition
   - Connection handling and error management

### Phase 2: Core Functionality (4-5 hours)
1. **MCP Integration**
   - Database Toolbox configuration
   - Vizro MCP setup
   - Client connection and testing
   - Tool discovery and validation

2. **ReAct Agent Implementation**
   - LangGraph workflow setup
   - Natural language processing
   - SQL query generation
   - Visualization parameter extraction

3. **Query Processing Pipeline**
   - User query analysis
   - Database query execution
   - Result processing and formatting
   - Visualization generation

### Phase 3: Frontend Integration (2-3 hours)
1. **Chat Interface**
   - Message display and history
   - Input handling and validation
   - Loading states and error handling
   - Real-time message updates

2. **Visualization Rendering**
   - Vizro component integration
   - Chart display and interaction
   - Responsive design
   - Export functionality

### Phase 4: Testing & Polish (1-2 hours)
1. **Testing**
   - Unit tests for core functions
   - Integration tests for MCP tools
   - End-to-end testing
   - Error scenario testing

2. **Documentation & Deployment**
   - README updates
   - API documentation
   - Deployment instructions
   - Demo preparation

## 🎯 Evaluation Criteria

### Technical Excellence (40%)
- **Code Quality**: Clean, well-documented, follows patterns
- **Architecture**: Proper separation of concerns, scalable design
- **Testing**: Comprehensive test coverage
- **Performance**: Fast response times, efficient resource usage

### Functionality (35%)
- **Core Features**: All required features implemented
- **User Experience**: Intuitive interface, helpful error messages
- **Data Accuracy**: Correct query results and visualizations
- **Real-time Communication**: Stable WebSocket connection

### Innovation (15%)
- **Creative Solutions**: Novel approaches to common problems
- **User Experience**: Enhanced usability beyond requirements
- **Technical Innovation**: Advanced use of AI/ML capabilities
- **Integration**: Seamless MCP server orchestration

### Presentation (10%)
- **Demo Quality**: Clear demonstration of capabilities
- **Documentation**: Comprehensive setup and usage guides
- **Communication**: Clear explanation of technical decisions
- **Business Value**: Clear articulation of business impact

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git
- Code editor (VS Code recommended)

### Quick Start
```bash
# 1. Clone the template
git clone <template-repo-url>
cd rops_h1_poc_analytics

# 2. Install dependencies
make install

# 3. Start development environment
make docker-up
make init-db
make start

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Development Workflow
1. **Plan First**: Review architecture and create implementation plan
2. **TDD Approach**: Write tests first, then implement functionality
3. **Iterative Development**: Build and test incrementally
4. **AI Assistance**: Use AI coding assistants for implementation
5. **Continuous Testing**: Test frequently throughout development

## 📚 Resources

### Documentation
- [AI Assistant Guide](AI_GUIDE.md) - Comprehensive guide for AI coding assistants
- [Development Patterns](DEVELOPMENT_PATTERNS.md) - Coding standards and best practices
- [MCP Integration Guide](MCP_INTEGRATION_GUIDE.md) - MCP server setup and usage

### External Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)
- [Vizro Documentation](https://vizro.mckinsey.com/)
- [React WebSocket Hooks](https://github.com/robtaussig/react-use-websocket)

### Sample Prompts for AI Assistants
```markdown
# Context Setting Prompt
@agent We are building an analytics POC. Here's the context:

BUSINESS DOMAIN: Analytics platform with merchants, users, transactions
TECHNICAL STACK: FastAPI + WebSocket + LangGraph + MCP + React
CURRENT STATE: [Describe what's implemented]
NEXT TASK: [Describe what needs to be built]

Please help me implement [specific feature] following the established patterns.

# Validation Prompt
@agent I've implemented [feature]. Please review the code and:
1. Check for adherence to coding standards
2. Verify error handling is comprehensive
3. Ensure tests cover the functionality
4. Suggest improvements if needed

# Integration Prompt
@agent I need to integrate [component A] with [component B]. Please help me:
1. Identify integration points
2. Handle potential conflicts
3. Ensure proper error handling
4. Test the integration
```

## 🏆 Success Tips

### For Students
1. **Start Early**: Begin with environment setup and basic WebSocket communication
2. **Use AI Effectively**: Provide clear context and follow established patterns
3. **Test Frequently**: Don't wait until the end to test functionality
4. **Focus on Core Features**: Ensure basic functionality works before adding enhancements
5. **Document Decisions**: Keep track of architectural decisions and trade-offs

### For AI Assistants
1. **Provide Context**: Always start with comprehensive system context
2. **Follow Patterns**: Maintain consistency with established coding patterns
3. **Validate Output**: Check generated code for quality and completeness
4. **Suggest Improvements**: Proactively identify potential issues and optimizations
5. **Test Integration**: Ensure components work together seamlessly

## 🎉 Demo Preparation

### Demo Script
1. **Introduction** (2 minutes)
   - Problem statement and business value
   - Technical architecture overview
   - Key features demonstration

2. **Live Demo** (5-7 minutes)
   - Ask natural language questions
   - Show real-time query processing
   - Demonstrate interactive visualizations
   - Handle error scenarios gracefully

3. **Technical Deep Dive** (3-5 minutes)
   - Code architecture walkthrough
   - MCP integration demonstration
   - Testing and quality assurance
   - Future enhancement possibilities

### Demo Questions to Prepare For
- "How does the system handle ambiguous queries?"
- "What happens when the database is unavailable?"
- "How would you scale this system for production?"
- "What security considerations did you implement?"
- "How does the ReAct agent decide which tools to use?"

## 🚀 Next Steps

After completing the hackathon:
1. **Code Review**: Conduct thorough code review and refactoring
2. **Performance Optimization**: Profile and optimize critical paths
3. **Security Audit**: Review security implications and implement safeguards
4. **Production Readiness**: Prepare for production deployment
5. **Feature Enhancement**: Plan additional features and improvements

Remember: The goal is to build a working POC that demonstrates the potential of natural language analytics for business users. Focus on core functionality, user experience, and technical excellence.
