# Azure AI Foundry Calendar Agent - Production Deployment Guide

## 🔧 Prerequisites and Setup

### 1. Azure Resources Required
- **Azure AI Foundry Project**: With GPT-4o model deployed
- **Azure App Registration**: For Microsoft Graph API access
- **Compute Environment**: Azure Container Instances, Azure Functions, or VM

### 2. Required Permissions

#### Microsoft Graph API Permissions (Application-level):
```
- Calendars.Read.All
- Calendars.ReadWrite.All  
- User.Read.All (for user lookup)
- MailboxSettings.Read (for timezone info)
```

#### Azure RBAC Permissions:
```
- Azure AI Developer (on AI Foundry project)
- Contributor (on resource group)
```

### 3. Environment Configuration

Create a `.env` file with the following variables:
```bash
# Azure AI Foundry
PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
MODEL_DEPLOYMENT_NAME=gpt-4o

# Microsoft Graph API
GRAPH_TENANT_ID=your-tenant-id
GRAPH_CLIENT_ID=your-app-registration-id
GRAPH_CLIENT_SECRET=your-client-secret

# Default Settings
DEFAULT_USER_UPN=primary-user@yourdomain.com
DEFAULT_TZ=Singapore Standard Time
```

## 🚀 Deployment Options

### Option 1: Azure Container Instances (Recommended)

1. **Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY req.txt .
RUN pip install -r req.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "src/enhanced_agent.py"]
```

2. **Deploy to ACI:**
```bash
az container create \
  --resource-group your-rg \
  --name calendar-agent \
  --image your-registry.azurecr.io/calendar-agent:latest \
  --cpu 1 --memory 2 \
  --environment-variables PROJECT_ENDPOINT=... GRAPH_TENANT_ID=... \
  --secure-environment-variables GRAPH_CLIENT_SECRET=...
```

### Option 2: Azure Functions (Serverless)

1. **Function App Structure:**
```
FunctionApp/
├── requirements.txt
├── host.json
├── function_app.py
└── calendar_function/
    ├── __init__.py
    └── function.json
```

2. **Deploy via CLI:**
```bash
func azure functionapp publish your-function-app-name
```

### Option 3: Azure Web App

1. **Create App Service:**
```bash
az webapp create \
  --resource-group your-rg \
  --plan your-app-service-plan \
  --name calendar-agent-api \
  --runtime "PYTHON|3.11"
```

2. **Configure App Settings:**
```bash
az webapp config appsettings set \
  --resource-group your-rg \
  --name calendar-agent-api \
  --settings @appsettings.json
```

## 🔒 Security Best Practices

### 1. Credential Management
- Use **Azure Key Vault** for sensitive credentials
- Implement **Managed Identity** where possible
- Rotate secrets regularly (90-day cycle recommended)

### 2. Network Security
- Configure **Virtual Network** integration
- Use **Private Endpoints** for Azure services
- Implement **API Gateway** for rate limiting

### 3. Application Security
```python
# Add input validation and sanitization
def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Implement request rate limiting
from functools import wraps
import time

def rate_limit(calls_per_minute=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Implementation here
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

## 📊 Monitoring and Observability

### 1. Azure Application Insights Integration

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

# Configure Application Insights
configure_azure_monitor(
    connection_string="your-appinsights-connection-string"
)

tracer = trace.get_tracer(__name__)

# Add tracing to key functions
@tracer.start_as_current_span("calendar_operation")
def traced_calendar_operation():
    # Your function logic
    pass
```

### 2. Custom Metrics Dashboard

**Key Metrics to Track:**
- API response times
- Success/failure rates
- Tool call frequency
- User interaction patterns
- Error types and frequencies

### 3. Alerting Rules

```json
{
  "alertRules": [
    {
      "name": "High Error Rate",
      "condition": "ErrorRate > 5%",
      "action": "Send email to ops team"
    },
    {
      "name": "Slow Response Time", 
      "condition": "AvgResponseTime > 30s",
      "action": "Scale up resources"
    }
  ]
}
```

## 🔄 CI/CD Pipeline

### Azure DevOps Pipeline (azure-pipelines.yml):

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'

stages:
- stage: Test
  jobs:
  - job: RunTests
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    - script: |
        pip install -r req.txt
        python -m pytest tests/
      displayName: 'Run tests'

- stage: Build
  dependsOn: Test
  jobs:
  - job: BuildImage
    steps:
    - task: Docker@2
      inputs:
        command: 'buildAndPush'
        repository: 'calendar-agent'
        dockerfile: 'Dockerfile'
        containerRegistry: 'your-acr-connection'
        tags: '$(Build.BuildId)'

- stage: Deploy
  dependsOn: Build
  jobs:
  - deployment: DeployToProduction
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureContainerInstances@0
            inputs:
              azureSubscription: 'your-azure-connection'
              resourceGroupName: 'your-rg'
              location: 'East US'
              imageSource: 'Container Registry'
              azureContainerRegistry: 'your-registry.azurecr.io'
              repositoryName: 'calendar-agent'
              tag: '$(Build.BuildId)'
```

## 🧪 Testing Strategy

### 1. Unit Tests
```python
import pytest
from src.improved_tools import read_schedule, create_meeting

def test_read_schedule_validation():
    result = read_schedule(user_upn=None)
    assert result["error"] == "validation_error"

def test_create_meeting_invalid_email():
    result = create_meeting(
        user_upn="test@domain.com",
        subject="Test",
        start_iso="2024-01-01T10:00:00Z",
        end_iso="2024-01-01T11:00:00Z",
        attendees=["invalid-email"]
    )
    assert result["error"] == "validation_error"
```

### 2. Integration Tests
```python
def test_agent_calendar_integration():
    agent = CalendarAgent()
    agent_id = agent.create_agent()
    thread_id = agent.create_conversation_thread()
    
    response = agent.process_message(
        thread_id, 
        "What's on my calendar today?"
    )
    
    assert response["status"] in ["success", "error"]
```

### 3. Load Testing
```bash
# Using Azure Load Testing
az load test create \
  --test-id calendar-agent-load-test \
  --load-test-config-file loadtest.yaml
```

## 📈 Scaling Considerations

### Auto-scaling Rules:
```json
{
  "rules": [
    {
      "metricTrigger": {
        "metricName": "CpuPercentage",
        "threshold": 70,
        "timeGrain": "PT1M",
        "statistic": "Average",
        "timeWindow": "PT5M"
      },
      "scaleAction": {
        "direction": "Increase",
        "value": "1"
      }
    }
  ]
}
```

## 🚨 Disaster Recovery

### Backup Strategy:
1. **Configuration Backup**: Store all configurations in Azure DevOps Git
2. **Data Backup**: No persistent data, stateless design
3. **Service Recovery**: Multi-region deployment capability

### Recovery Procedures:
```bash
# Quick recovery script
#!/bin/bash
az group deployment create \
  --resource-group backup-rg \
  --template-file infrastructure.json \
  --parameters @parameters.json
```

## 📞 Support and Maintenance

### Monitoring Checklist:
- [ ] Application Insights configured
- [ ] Custom dashboards created  
- [ ] Alert rules configured
- [ ] Log retention policies set
- [ ] Performance baselines established

### Maintenance Schedule:
- **Daily**: Monitor dashboards and alerts
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Capacity planning and cost optimization

## 🎯 Success Metrics

### Technical KPIs:
- 99.9% uptime SLA
- < 30 second average response time
- < 1% error rate
- 100% security compliance

### Business KPIs:
- User adoption rate
- Calendar automation efficiency
- Cost per transaction
- Customer satisfaction scores
