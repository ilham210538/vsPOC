# Azure AI Foundry Calendar Agent - Complete Setup Guide

## 🎯 Overview
This guide provides step-by-step instructions to implement an AI-powered calendar assistant that integrates with Microsoft 365 calendars using Azure AI Foundry and Microsoft Graph API.

## 🛠️ What We're Building
- **AI Calendar Assistant**: Intelligent agent that can read schedules, check availability, and create meetings
- **Microsoft Graph Integration**: Direct access to user calendars and mailbox data
- **Natural Language Processing**: Users can interact using plain English queries
- **Interactive Terminal Chat**: Real-time conversation interface with full API visibility
- **Production-Ready**: Secure, scalable, and enterprise-grade solution

## 🏗️ Architecture Overview

### Current Implementation (Local Development)
```
User Terminal Chat ←→ Enhanced Agent ←→ Microsoft Graph API
                           ↓
                    Azure AI Foundry (GPT-4o)
                           ↓
                    Calendar Tools (Python Functions)
```

### Future Production Deployment Options
```
Option 1: Azure App Service API
User Interface ←→ App Service ←→ Graph API
                     ↓
              Azure AI Foundry

Option 2: Azure Functions
User Interface ←→ Azure Functions ←→ Graph API
                     ↓
              Azure AI Foundry
``` Foundry Calendar Agent - Complete Setup Guide

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

## Phase 4: Agent Implementation & Interactive Chat

### Step 10: Implement Core Components

#### A. Calendar Tools (`improved_tools.py`)
The tools handle Microsoft Graph API interactions:
- **read_schedule()**: Fetches calendar events for specified time ranges
- **create_meeting()**: Creates new calendar events with attendees
- **get_current_datetime()**: Provides real-time date/time in correct timezone
- **Authentication**: Uses app-only authentication with client credentials

#### B. AI Agent (`enhanced_agent.py`)
The main agent orchestrates AI interactions:
- **Agent Creation**: Initializes AI assistant with calendar capabilities
- **Message Processing**: Handles user queries and tool calls
- **Response Management**: Returns formatted responses to users
- **Human-in-the-Loop**: Requires confirmation before creating meetings

#### C. Interactive Chat Interface (`interactive_chat.py`)
Real-time terminal chat interface:
- **Live Conversation**: Chat with your AI agent like a chatbot
- **Full API Visibility**: See all Graph API calls, responses, and token validation
- **Professional UI**: Clean formatting with emojis and separators
- **Sample Queries**: Pre-written examples for easy testing

### Step 11: Test Interactive Chat
Run the interactive chat interface:
```bash
python src/interactive_chat.py
```

Expected interface:
```
=================================================================
🗓️   CALENDAR AGENT CHAT INTERFACE
=================================================================
📅 Today: Thursday, September 04, 2025

💡 SAMPLE QUERIES:
─────────────────────────────────────────────
1️⃣   What does my schedule look like next week?
2️⃣   Am I free next Thursday 12:00–14:00?
3️⃣   Book a meeting with john@company.com tomorrow at 3pm
     for 1 hour, title 'Project Discussion'

ℹ️   Commands: 'quit', 'exit', 'bye' to end session
ℹ️   All API calls will be shown with full visibility
=================================================================

🚀 Azure AI Foundry Calendar Agent - Initializing...
⚙️  Initializing calendar agent...
🤖 Creating agent instance...
✅ Agent created successfully. Agent ID: asst_xxxxx
🧵 Creating conversation thread...
✅ Thread created successfully. Thread ID: thread_xxxxx

🎉 Ready! You can start chatting now.
─────────────────────────────────────────────────────────────────

👤 User: what is on my schedule today?
🔄 Processing request... 📅 API Call: get_current_datetime()
📅 Current Date/Time: September 04, 2025 at 18:30:15 SGT | UTC: September 04, 2025 at 10:30:15 UTC
API Call: GET https://graph.microsoft.com/v1.0/users/user@domain.com/calendarView?startDateTime=2025-09-04T00:00:00+08:00&endDateTime=2025-09-04T23:59:59+08:00&$select=id,subject,start,end,location&$top=10
Timezone: Singapore Standard Time
✅ Response Status: 200 | Events retrieved: 3
✅ Success
🤖 Agent: Here is your schedule for today, September 4, 2025:

1. **Morning Standup**
   - **Time**: 9:00 AM - 9:30 AM (Singapore Standard Time)
   - **Location**: Microsoft Teams Meeting

2. **Client Presentation**  
   - **Time**: 2:00 PM - 3:00 PM (Singapore Standard Time)
   - **Location**: Conference Room A

3. **Project Review**
   - **Time**: 4:00 PM - 5:00 PM (Singapore Standard Time)
   - **Location**: Microsoft Teams Meeting

─────────────────────────────────────────────────────────────────

👤 User: quit
```

### Step 12: Test Meeting Creation (Human-in-the-Loop)
The agent implements safety controls for meeting creation:

```
👤 User: book a meeting with sarah@company.com tomorrow at 2pm for 1 hour, title 'Project Discussion'
🔄 Processing request... ✅ Success
🤖 Agent: I'll create a meeting with these details:

**Meeting Details:**
- **Subject**: Project Discussion
- **Date/Time**: September 5, 2025, 2:00 PM - 3:00 PM (Singapore Standard Time)
- **Attendees**: sarah@company.com
- **Location**: Microsoft Teams Meeting (online)

Would you like me to create this meeting? Please type YES to confirm or NO to cancel.

👤 User: YES
🔄 Processing request... API Call: POST https://graph.microsoft.com/v1.0/users/user@domain.com/events
Meeting Subject: Project Discussion
Event created successfully: AAMkADI1NTM...
✅ Success
🤖 Agent: ✅ Meeting "Project Discussion" has been successfully created for tomorrow, September 5, 2025, from 2:00 PM to 3:00 PM. An invitation has been sent to sarah@company.com.
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

## 🚀 Production Deployment Strategies

### Why Azure AI Foundry Portal Doesn't Work Directly

**Current Issue**: The Azure AI Foundry web portal cannot access your local Python tools (`read_schedule`, `create_meeting`, `get_current_datetime`). The portal only has access to:
- Built-in tools (web search, code interpreter)
- Azure Functions (when properly configured)
- Public API endpoints

**Terminal vs Portal Behavior**:
- **Terminal**: ✅ Runs complete Python application with all tools locally
- **Portal**: ❌ Shows tool calls but cannot execute your custom Python functions

### Solution: Deploy Tools as Services

#### Option 1: Azure App Service (Recommended)
Deploy your entire application as a REST API:

```python
# Example: app_service_wrapper.py
from flask import Flask, request, jsonify
from src.enhanced_agent import CalendarAgent

app = Flask(__name__)

@app.route('/api/calendar/query', methods=['POST'])
def calendar_query():
    user_message = request.json['message']
    # Process with your existing agent logic
    return jsonify(response)

@app.route('/api/calendar/read_schedule', methods=['POST'])
def api_read_schedule():
    # Wrapper for your read_schedule function
    return jsonify(read_schedule(**request.json))

@app.route('/api/calendar/create_meeting', methods=['POST'])  
def api_create_meeting():
    # Wrapper for your create_meeting function
    return jsonify(create_meeting(**request.json))
```

**Deployment Process**:
1. Create Azure App Service
2. Deploy your Python application
3. Configure environment variables
4. Update Azure AI Foundry agent to call your API endpoints

#### Option 2: Azure Functions
Deploy each tool as a separate serverless function:

```python
# Function: read-schedule
import azure.functions as func
from src.improved_tools import read_schedule

def main(req: func.HttpRequest) -> func.HttpResponse:
    params = req.get_json()
    result = read_schedule(**params)
    return func.HttpResponse(json.dumps(result))
```

**Benefits**:
- ✅ Serverless scaling
- ✅ Pay-per-execution
- ✅ Integrated with Azure ecosystem
- ✅ Easy monitoring and logging

#### Option 3: Hybrid Approach (Current + Future)
**Development**: Use local terminal chat for testing and development
**Production**: Deploy to App Service or Functions for external access

### Integration Architecture

```
User Application/Interface
         ↓
    Azure App Service API
         ↓
┌────────────────────────┐
│  Your Python Tools     │
│  ├── read_schedule     │
│  ├── create_meeting    │  
│  └── get_current_time  │
└────────────────────────┘
         ↓
   Microsoft Graph API
```

### Azure AI Foundry Integration

Once deployed as an API, configure Azure AI Foundry to use your endpoints:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_schedule",
        "description": "Read calendar schedule",
        "url": "https://your-app.azurewebsites.net/api/calendar/read_schedule"
      }
    }
  ]
}
```

---

## � Quick Start Checklist

### For Development/Demo (Ready Now)
- [ ] Azure App Registration created with proper permissions
- [ ] Azure AI Foundry project setup with GPT-4o deployment
- [ ] Environment variables configured in `.env` file
- [ ] Python dependencies installed (`pip install -r req.txt`)
- [ ] Test enhanced_agent.py works
- [ ] **Run interactive chat**: `python src/interactive_chat.py`
- [ ] Test calendar queries and meeting creation
- [ ] Prepare demo scenarios for client presentation

### For Production Deployment (Future)
- [ ] Choose deployment strategy (App Service vs Functions)
- [ ] Create Azure App Service or Function Apps
- [ ] Deploy Python tools as REST API endpoints
- [ ] Configure Azure AI Foundry to use deployed endpoints
- [ ] Set up monitoring and logging
- [ ] Implement user authentication (if needed)
- [ ] Create web-based user interface
- [ ] Conduct user acceptance testing

---

## 🎯 Success Metrics

### Current Implementation
After successful setup, you should achieve:
- **Real-time chat interface**: Interactive conversation with AI agent
- **Full API visibility**: See all Graph API calls and responses
- **Instant calendar queries**: "What's on my schedule today?"
- **Availability checks**: "Am I free next Tuesday at 3pm?"
- **Safe meeting creation**: Human-in-the-loop confirmation process
- **Natural language processing**: Users can ask in plain English
- **Enterprise security**: App-level permissions, secure authentication

### Production Targets
- **Response time**: < 3 seconds for calendar queries
- **Availability**: 99.9% uptime with Azure infrastructure
- **Concurrency**: Support 100+ simultaneous users
- **User adoption**: 80%+ of target users actively using the system
- **Time savings**: 60%+ reduction in manual calendar management

---

## 🚨 Important Notes

### Current Limitations
1. **Azure AI Foundry Portal**: Cannot directly execute local Python tools
2. **Single User**: Current implementation targets one user (DEFAULT_USER_UPN)
3. **Terminal Interface**: Requires command line access for current demo

### Recommended Next Steps
1. **Immediate**: Use interactive chat for client demos and proof of concept
2. **Short-term**: Deploy tools as Azure services for production use
3. **Long-term**: Build comprehensive web interface and Teams integration

### Security Considerations
- **App Registration**: Use principle of least privilege
- **Client Secrets**: Set proper expiration and rotation policies
- **API Permissions**: Regularly audit granted permissions
- **Network Security**: Consider VNet integration for production
- **Data Privacy**: Ensure compliance with organizational policies

---

## 📞 Support & Troubleshooting

### Common Issues
1. **"Agent doesn't respond in Azure AI Foundry"** → Tools need to be deployed as Azure services
2. **"Authentication failed"** → Check client secret and permissions
3. **"HTTP 400 datetime errors"** → Timezone formatting issues (handled automatically)
4. **"Rate limiting"** → Implement backoff strategies (already included)

### Debug Resources
- Check `agent_operations.log` for detailed error information
- Use interactive chat for real-time debugging
- Monitor Azure AI Foundry project logs
- Verify Graph API permissions in Azure portal

---

*This guide provides a complete pathway from development to production deployment, ensuring both immediate demonstration capabilities and future scalability.*

---

## 💡 Client Presentation Guide

### Current Capabilities Demo

#### 1. **Interactive Terminal Chat** (Ready Now)
- **Live Demo**: Show real-time conversation with AI agent
- **Full Transparency**: Display all API calls, Graph requests, token validation
- **Natural Language**: Demonstrate complex queries in plain English
- **Safety Controls**: Show human-in-the-loop confirmation for meeting creation

#### 2. **Development Workflow** 
```bash
# Start interactive chat
python src/interactive_chat.py

# Example demo flow:
👤 "What's on my schedule today?"
👤 "Am I free next Tuesday at 3pm?"  
👤 "Book a meeting with client@company.com tomorrow at 2pm"
👤 "Show me next week's schedule"
```
