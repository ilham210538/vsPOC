# Logic App Integration Setup Guide

## 🎯 Overview
This guide explains how to connect your existing Logic App approval workflow to the Calendar Agent, enabling automated approval processes for leave requests and meeting approvals.

## 🏗️ Architecture

```
Calendar Agent → Logic App → Approval Email → Manager Decision → Callback → Agent Response
     ↓              ↓                            ↓              ↓
1. User Request  2. Send Email    3. Manager    4. Update     5. Notify User
   (Leave/Meet)     with Approve/   Clicks       Agent via     (Approved/
                    Reject Buttons  Button       Webhook       Rejected)
```

## 📋 Prerequisites

### 1. Existing Logic App
✅ You already have a Logic App named "ApprovalWorkflow" (or similar)
✅ Your Logic App has the HTTP trigger: "When_an_HTTP_request_is_received"
✅ Your Logic App expects this payload format:
```json
{
  "message": {
    "to": "approver@company.com",
    "subject": "Subject",
    "bodyText": "Plain text body"
  },
  "callbackUrl": "https://your-callback-endpoint"
}
```

### 2. Azure Resources
- Azure subscription with your Logic App
- Resource group containing the Logic App
- Proper permissions to manage Logic Apps

## 🛠️ Setup Steps

### Step 1: Configure Environment Variables

Add these to your `.env` file:

```bash
# Logic App Integration
SUBSCRIPTION_ID=your-azure-subscription-id
RESOURCE_GROUP_NAME=your-resource-group-name
LOGIC_APP_NAME=ApprovalWorkflow
LOGIC_APP_TRIGGER_NAME=When_an_HTTP_request_is_received

# Callback Configuration
CALLBACK_BASE_URL=http://localhost:5000
CALLBACK_PORT=5000
```

### Step 2: Install Additional Dependencies

Update your requirements:
```bash
pip install azure-mgmt-logic flask
```

### Step 3: Get Your Logic App Details

1. Go to Azure Portal → Your Logic App
2. Copy the **subscription ID** from the URL or Overview page
3. Copy the **resource group name** 
4. Note the **Logic App name** (should match your actual name)
5. In Logic App Designer, find your HTTP trigger and copy the **trigger name**

### Step 4: Update Logic App Callback (Important!)

Your Logic App needs to call back to the agent. Update the HTTP actions in your Logic App:

**For Approved Branch:**
```json
{
  "uri": "@triggerBody()?['callbackUrl']",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "status": "APPROVED",
    "selectedOption": "@{body('Send_approval_email')?['SelectedOption']}",
    "message": "@{outputs('Compose_-_Agent_Message_(Approved)')}"
  }
}
```

**For Rejected Branch:**
```json
{
  "uri": "@triggerBody()?['callbackUrl']",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "status": "REJECTED", 
    "selectedOption": "@{body('Send_approval_email')?['SelectedOption']}",
    "message": "@{outputs('Compose_-_Agent_Message_(Rejected)')}"
  }
}
```

## 🚀 Testing the Integration

### Test 1: Start the Enhanced Agent
```bash
python src/interactive_chat.py
```

### Test 2: Request Leave Approval
```
User: I want to request leave from October 15 to October 17 for a family vacation
```

The agent should:
1. Check your current calendar for conflicts
2. Ask for your manager's email if not provided
3. Send the approval request to Logic App
4. Provide you with a tracking ID
5. Wait for the Logic App callback

### Test 3: Check Approval Status
```
User: What's the status of my leave request?
```

## 🔧 Advanced Configuration

### Production Deployment

For production, replace the callback service with a proper web application:

1. **Deploy to Azure App Service:**
   - Upload the `approval_callback_service.py` as a Flask app
   - Update `CALLBACK_BASE_URL` to your App Service URL
   - Configure proper authentication and HTTPS

2. **Use Azure Function:**
   - Create an Azure Function to handle callbacks
   - Update Logic App to call the Function URL

### Security Considerations

1. **Authentication:** Add authentication to your callback endpoints
2. **HTTPS:** Use HTTPS for all callback URLs in production
3. **Validation:** Validate incoming callback payloads
4. **Secrets:** Use Azure Key Vault for sensitive configuration

## 🚨 Troubleshooting

### Common Issues

1. **Logic App not registered:**
   ```
   Error: Logic App 'ApprovalWorkflow' not registered
   ```
   - Check subscription ID and resource group name
   - Verify Logic App exists and you have permissions
   - Check the trigger name matches exactly

2. **Callback not received:**
   ```
   Approval sent but no response received
   ```
   - Check if callback service is running (port 5000)
   - Verify callback URL is accessible from Logic App
   - Check Logic App run history for errors

3. **Permission errors:**
   ```
   Error: Insufficient privileges to complete the operation
   ```
   - Your Azure account needs Logic App Contributor role
   - Check if the Logic App is in the correct resource group

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Logic App Run History

1. Go to Azure Portal → Your Logic App
2. Click "Overview" → "Runs history"
3. Check recent runs for errors
4. Verify the payload received matches expected format

## 📝 Example Workflows

### Leave Request Flow
```
1. User: "I need leave Dec 20-22 for holiday"
2. Agent: Checks calendar, finds meetings on Dec 21
3. Agent: "You have a client meeting on Dec 21. Proceed with leave request?"
4. User: "Yes, I'll reschedule the meeting"
5. Agent: "What's your manager's email?"
6. User: "manager@company.com"
7. Agent: Sends to Logic App → Email sent → Manager approves
8. Agent: "✅ Your leave request has been approved!"
```

### Meeting Approval Flow
```
1. User: "Schedule exec meeting with CEO next Friday 2pm"
2. Agent: "This requires approval. Manager's email?"
3. User: "director@company.com" 
4. Agent: Sends approval request → Email sent → Director approves
5. Agent: "✅ Meeting approved and created in calendar"
```

## 📈 Monitoring & Analytics

### Key Metrics to Track
- Approval request volume
- Approval/rejection rates
- Response time from managers
- Failed callback attempts

### Azure Application Insights
Configure Application Insights to monitor:
- Logic App execution time
- Callback service performance
- Error rates and exceptions

## 🔄 Next Steps

1. **Test the basic integration** with your existing Logic App
2. **Customize approval email templates** in Logic App
3. **Add more approval types** (meeting rooms, equipment, etc.)
4. **Integrate with HR systems** for automatic leave balance updates
5. **Create approval dashboards** for managers

---

*This integration allows your Calendar Agent to seamlessly connect with your existing approval processes, making it a truly enterprise-ready solution.*
