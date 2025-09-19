# Calendar Agent Web Application - Azure Deployment

This is the web version of the Calendar Agent that replaces the terminal-based `interactive_chat.py`.

## 🚀 Local Development

### Prerequisites
- Node.js 18+ 
- Python 3.8+
- All Python dependencies from `req.txt`

### Setup
1. Install Node.js dependencies:
```bash
npm install
```

2. Install Python dependencies:
```bash
pip install -r req.txt
```

3. Set up your environment variables (same as before):
```bash
# Copy your existing .env file with:
# PROJECT_ENDPOINT=...
# MODEL_DEPLOYMENT_NAME=...
# etc.
```

### Running Locally
```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

The app will be available at `http://localhost:3000`

## 📦 Azure Deployment

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
2. **Create Azure Web App:**
   - Go to Azure Portal
   - Create new Web App
   - Choose Node.js runtime
   - Connect to your GitHub repository
   - Set branch to deploy from

3. **Configure Environment Variables:**
   In Azure Portal → Your Web App → Configuration → Application Settings:
   ```
   PROJECT_ENDPOINT=your_azure_ai_endpoint
   MODEL_DEPLOYMENT_NAME=your_model_name
   SCM_DO_BUILD_DURING_DEPLOYMENT=true
   ```

### Method 2: Direct Deployment

1. **Install Azure CLI**
2. **Login to Azure:**
```bash
az login
```

3. **Create Resource Group:**
```bash
az group create --name calendar-agent-rg --location "East US"
```

4. **Create App Service Plan:**
```bash
az appservice plan create --name calendar-agent-plan --resource-group calendar-agent-rg --sku F1 --is-linux
```

5. **Create Web App:**
```bash
az webapp create --resource-group calendar-agent-rg --plan calendar-agent-plan --name your-calendar-agent --runtime "NODE|18-lts"
```

6. **Deploy Code:**
```bash
az webapp deployment source config --name your-calendar-agent --resource-group calendar-agent-rg --repo-url https://github.com/yourusername/vsPOC --branch main
```

7. **Configure Environment Variables:**
```bash
az webapp config appsettings set --resource-group calendar-agent-rg --name your-calendar-agent --settings PROJECT_ENDPOINT="your_endpoint" MODEL_DEPLOYMENT_NAME="your_model"
```

## 🔧 Project Structure

```
vsPOC/
├── package.json          # Main package.json for Azure
├── server.js            # Express server (entry point)
├── web.config           # IIS configuration for Windows
├── src/                 # Python backend code
│   ├── agent_cli.py     # CLI wrapper for Node.js integration
│   ├── enhanced_agent.py # Main agent logic
│   └── tools/           # Agent tools
├── frontend/            # React source code
│   ├── package.json
│   ├── src/
│   └── public/
├── public/              # Built React frontend (auto-generated)
└── deployment/          # Azure deployment configs
```

## 🎯 Key Features

- **Simple Chat Interface**: Clean, mobile-friendly React UI
- **Real-time Communication**: Direct integration with your Python agent
- **Azure-Ready**: Optimized for Azure Web App deployment
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Proper error states and connection status

## 🔄 Replacing Terminal Chat

This web app completely replaces `interactive_chat.py`. The same agent functionality is available through the web interface:
- Calendar queries
- Meeting scheduling  
- Leave approval workflows
- All existing tools and features

## 🐛 Troubleshooting

### Common Issues:

1. **Python not found**: Ensure Python is installed and in PATH on Azure
2. **Module import errors**: Check that all dependencies are in `req.txt`
3. **Build failures**: Check Azure build logs in Portal → Deployment Center
4. **Environment variables**: Verify all required variables are set in Azure

### Logs:
```bash
# View Azure logs
az webapp log tail --name your-calendar-agent --resource-group calendar-agent-rg
```

## 📚 Additional Resources

- [Azure App Service Node.js Guide](https://docs.microsoft.com/en-us/azure/app-service/quickstart-nodejs)
- [Azure Environment Variables](https://docs.microsoft.com/en-us/azure/app-service/configure-common)
- [GitHub Deployment](https://docs.microsoft.com/en-us/azure/app-service/deploy-github-actions)
