# Azure AI Calendar Agent

A sophisticated AI agent that integrates with Microsoft Graph API to manage calendar operations using Azure AI Foundry.

## 🔒 Security Setup (IMPORTANT)

### 1. Environment Configuration

This project requires sensitive credentials. **NEVER commit actual credentials to git.**

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Fill in your actual credentials in `.env`:
   - `PROJECT_ENDPOINT`: Your Azure AI Foundry project endpoint
   - `MODEL_DEPLOYMENT_NAME`: Your deployed model name (e.g., gpt-4o)
   - `GRAPH_TENANT_ID`: Your Azure AD tenant ID
   - `GRAPH_CLIENT_ID`: Your application client ID
   - `GRAPH_CLIENT_SECRET`: Your application client secret
   - `DEFAULT_USER_UPN`: Email address for calendar operations
   - `DEFAULT_TZ`: Your timezone (Windows format)

### 2. Azure App Registration

You need to register an application in Azure AD with the following permissions:
- `Calendars.ReadWrite`
- `Mail.Send` (if using email features)
- Application permissions (not delegated)

### 3. Required Dependencies

Install dependencies:
```bash
pip install -r req.txt
```

## 🚀 Usage

### Basic Chat Interface
```bash
python src/interactive_chat.py
```

### Direct Agent Usage
```python
from src.enhanced_agent import EnhancedCalendarAgent

agent = EnhancedCalendarAgent()
result = agent.process_request("Show me my meetings today")
```

## 📁 Project Structure

```
├── src/
│   ├── enhanced_agent.py      # Main AI agent implementation
│   ├── improved_tools.py      # Microsoft Graph API tools
│   ├── datetime_tool.py       # Date/time utilities
│   └── interactive_chat.py    # Chat interface
├── .env.template              # Environment template (safe)
├── .gitignore                 # Git ignore rules
├── req.txt                    # Python dependencies
└── SETUP_GUIDE.md            # Detailed setup instructions
```

## ⚠️ Security Notes

- Never commit `.env` files
- Rotate credentials regularly
- Use principle of least privilege for app permissions
- Monitor usage through Azure portal
- Keep dependencies updated

## 🛠️ Development

The agent supports:
- Natural language calendar queries
- Meeting creation and management
- Time zone handling
- Comprehensive logging
- Error handling and recovery

## 📝 License

[Add your license information here]
