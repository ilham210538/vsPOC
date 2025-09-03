# Azure AI Foundry Calendar Agent - Complete Setup Guide

## � Overview
This guide provides step-by-step instructions to implement an AI-powered calendar assistant that integrates with Microsoft 365 calendars using Azure AI Foundry and Microsoft Graph API.

## 🎯 What We're Building
- **AI Calendar Assistant**: Intelligent agent that can read schedules, check availability, and create meetings
- **Microsoft Graph Integration**: Direct access to user calendars and mailbox data
- **Natural Language Processing**: Users can interact using plain English queries
- **Production-Ready**: Secure, scalable, and enterprise-grade solution

---

## Phase 1: Azure App Registration Setup

### Step 1: Create Azure App Registration
1. Navigate to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **"New registration"**
3. Configure the application:
   ```
   Name: Calendar-Agent-App
   Supported account types: Single tenant
   Redirect URI: Leave blank for now
   ```
4. Click **"Register"**
5. **Copy and save** the following values:
   - Application (client) ID
   - Directory (tenant) ID

### Step 2: Create Client Secret
1. In your app registration, go to **"Certificates & secrets"**
2. Click **"New client secret"**
3. Add description: `Calendar-Agent-Secret`
4. Set expiration: `24 months` (recommended)
5. Click **"Add"**
6. **⚠️ IMPORTANT**: Copy the secret value immediately (it won't be shown again)

### Step 3: Configure API Permissions
1. Go to **"API permissions"** in your app registration
2. Click **"Add a permission"** → **"Microsoft Graph"** → **"Application permissions"**
3. Add the following permissions:
   ```
   ✅ Calendars.Read.All
   ✅ Calendars.ReadWrite.All
   ✅ User.Read.All
   ✅ MailboxSettings.Read
   ```
4. Click **"Add permissions"**
5. **⚠️ CRITICAL**: Click **"Grant admin consent for [Your Organization]"**
6. Verify all permissions show **"Granted for [Your Organization]"**

---

## Phase 2: Azure AI Foundry Project Setup

### Step 4: Create Azure AI Foundry Project
1. Navigate to **Azure AI Foundry** portal: `ai.azure.com`
2. Click **"New project"**
3. Configure project settings:
   ```
   Project name: calendar-agent-project
   Resource group: Create new or use existing
   Region: East US (or your preferred region)
   ```
4. Click **"Create project"**

### Step 5: Deploy GPT-4o Model
1. In your AI Foundry project, go to **"Deployments"**
2. Click **"Deploy model"** → **"GPT-4o"**
3. Configure deployment:
   ```
   Deployment name: gpt-4o-calendar
   Model version: Latest
   Tokens per minute rate limit: 30K (adjust based on needs)
   ```
4. Click **"Deploy"**
5. **Copy the deployment name** for later use

### Step 6: Get Project Endpoint
1. In your AI Foundry project, go to **"Settings"** → **"Properties"**
2. **Copy the Project Endpoint URL** (looks like: `https://your-resource.services.ai.azure.com/api/projects/your-project`)

---

## Phase 3: Development Environment Setup

### Step 7: Clone and Setup Code
1. Clone the repository or create new folder:
   ```bash
   mkdir calendar-agent
   cd calendar-agent
   ```

2. Create the required Python files:
   ```
   calendar-agent/
   ├── .env
   ├── req.txt
   └── src/
       ├── enhanced_agent.py
       └── improved_tools.py
   ```

### Step 8: Configure Environment Variables
Create a `.env` file with your actual values:
```bash
# Azure AI Foundry Configuration
PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
MODEL_DEPLOYMENT_NAME=gpt-4o-calendar

# Microsoft Graph API Configuration
GRAPH_TENANT_ID=your-tenant-id-from-step1
GRAPH_CLIENT_ID=your-client-id-from-step1
GRAPH_CLIENT_SECRET=your-client-secret-from-step2

# Default User Settings
DEFAULT_USER_UPN=user@yourdomain.com
DEFAULT_TZ=UTC
```

### Step 9: Install Dependencies
Create `req.txt`:
```
azure-ai-projects==1.0.0b4
azure-identity>=1.15.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

Install packages:
```bash
pip install -r req.txt
```

---

## Phase 4: Agent Implementation

### Step 10: Implement Core Components

#### A. Calendar Tools (`improved_tools.py`)
The tools handle Microsoft Graph API interactions:
- **read_schedule()**: Fetches calendar events for specified time ranges
- **create_meeting()**: Creates new calendar events with attendees
- **Authentication**: Uses app-only authentication with client credentials

#### B. AI Agent (`enhanced_agent.py`)
The main agent orchestrates AI interactions:
- **Agent Creation**: Initializes AI assistant with calendar capabilities
- **Message Processing**: Handles user queries and tool calls
- **Response Management**: Returns formatted responses to users

### Step 11: Test Basic Functionality
Run initial test:
```bash
python src/enhanced_agent.py
```

Expected output:
```
Azure AI Foundry Calendar Agent - Initializing...
Initializing calendar agent...
Creating agent instance...
Agent created successfully. Agent ID: asst_xxxxx
Creating conversation thread...
Thread created successfully. Thread ID: thread_xxxxx

Running 2 test interactions...

[1/2] User: What does my schedule look like next week?
Processing request... ✅ Success
Agent: [Calendar response with events]

[2/2] User: Am I free tomorrow at 2pm?
Processing request... ✅ Success
Agent: [Availability response]
```

---

## Phase 5: Production Configuration

### Step 12: Security Hardening
1. **Credential Management**:
   ```bash
   # Remove .env from version control
   echo ".env" >> .gitignore
   ```

2. **Permission Validation**:
   - Verify app permissions are granted
   - Test with actual user accounts
   - Confirm timezone handling

### Step 13: Error Handling & Monitoring
The solution includes:
- **Comprehensive logging** to `agent_operations.log`
- **Rate limit handling** for both Graph API and AI service
- **Graceful error recovery** with detailed error messages
- **Agent cleanup** to prevent resource accumulation

### Step 14: Performance Optimization
Built-in optimizations:
- **Minimal field selection** in Graph API calls (`$select`)
- **Result limiting** to prevent large payloads (`$top=10`)
- **Efficient message parsing** for AI responses
- **Connection pooling** for HTTP requests

---

## Phase 6: Client Integration Options

### Option A: Direct Integration
```python
# Example integration code
from src.enhanced_agent import CalendarAgent

agent = CalendarAgent()
agent_id = agent.create_agent()
thread_id = agent.create_conversation_thread()

response = agent.process_message(
    thread_id, 
    "Schedule a meeting with john@company.com tomorrow at 3pm"
)
print(response["message"])
```

### Option B: API Wrapper
Create a simple web API using FastAPI or Flask:
```python
from flask import Flask, request, jsonify
from src.enhanced_agent import CalendarAgent

app = Flask(__name__)
agent = CalendarAgent()

@app.route("/calendar/query", methods=["POST"])
def handle_calendar_query():
    user_message = request.json["message"]
    response = agent.process_message(thread_id, user_message)
    return jsonify(response)
```

### Option C: Teams Bot Integration
Integrate with Microsoft Teams using Bot Framework.

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. Authentication Errors
```
Error: Authentication failed. Check credentials.
```
**Solution**: Verify client secret is correct and hasn't expired

#### 2. Permission Denied
```
Error: App lacks required Application permissions.
```
**Solution**: Ensure admin consent was granted for all Graph API permissions

#### 3. Rate Limiting
```
Error: Graph API rate limit exceeded. Retry after: 60 seconds
```
**Solution**: Implement exponential backoff (already included in code)

#### 4. Agent Creation Failures
```
Error: Failed to create agent
```
**Solution**: Check AI Foundry project endpoint and model deployment name

### Testing Checklist
- [ ] App registration permissions granted
- [ ] Client secret is valid and copied correctly
- [ ] AI Foundry project is accessible
- [ ] Model deployment is active
- [ ] Environment variables are set correctly
- [ ] Target user email exists in tenant
- [ ] Network connectivity to Azure services

---

## 📊 Success Metrics

After successful setup, you should achieve:
- **Instant calendar queries**: "What's on my schedule today?"
- **Availability checks**: "Am I free next Tuesday at 3pm?"
- **Meeting creation**: "Book a meeting with sarah@company.com tomorrow at 2pm"
- **Natural language processing**: Users can ask in plain English
- **Enterprise security**: App-level permissions, secure authentication

---

## 🎯 Next Steps

1. **Pilot Testing**: Start with a small group of users
2. **Feature Expansion**: Add more calendar operations (delete, update)
3. **UI Development**: Create user-friendly interface
4. **Teams Integration**: Deploy as Microsoft Teams bot
5. **Analytics**: Implement usage tracking and optimization

---

## 💡 Client Presentation Tips

### Demo Flow:
1. **Show Azure setup** (App registration, permissions)
2. **Demonstrate AI Foundry** (Project, model deployment)
3. **Walk through code structure** (Tools, agent, integration)
4. **Live demonstration** (Calendar queries, meeting creation)
5. **Discuss customization** (Branding, additional features)
6. **Present deployment options** (Integration paths)

### Key Selling Points:
- **Enterprise Security**: Uses Microsoft's own authentication
- **Scalable Architecture**: Built on Azure cloud infrastructure  
- **Natural Language**: No complex commands or training needed
- **Quick Implementation**: Can be deployed in days, not months
- **Cost Effective**: Pay-per-use model with Azure services
