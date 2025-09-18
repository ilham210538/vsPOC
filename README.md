# Visual Solutions POC

A modern AI-powered calendar assistant with an exciting React frontend and Python backend.

## 🚀 Quick Start Commands

### For UI Development (Recommended)
```bash
# Terminal 1: Start backend server
npm start

# Terminal 2: Start frontend with hot reload
frontend-dev.bat
```
- **Frontend**: http://localhost:5173 (with instant UI updates)
- **Backend**: http://localhost:8080 (API server)

### For Full Testing
```bash
# One command - builds everything and starts production-like server
full-dev.bat
```
- **Complete App**: http://localhost:8080 (production simulation)

### For Production
```bash
# Just the backend serving built frontend
npm start
```
- **Application**: http://localhost:8080

---

## 📁 Project Structure

```
vsPOC/
├── 🎨 frontend/              # React + TypeScript UI
│   ├── src/
│   │   ├── components/       # Chat components
│   │   ├── hooks/           # React hooks
│   │   └── lib/             # Utilities
│   └── package.json
├── 🐍 src/                   # Python AI agent
│   ├── enhanced_agent.py    # Main AI logic
│   ├── tools/               # Calendar tools
│   └── agent_cli.py         # Terminal interface
├── 🌐 server.js             # Express backend
├── package.json             # Backend dependencies
└── *.bat                    # Easy startup scripts
```

---

## 🛠️ Development Commands Explained

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `frontend-dev.bat` | Start React dev server with hot reload | UI development & styling |
| `full-dev.bat` | Build + start complete application | Testing full integration |
| `npm start` | Production server only | Final testing |

### Development Workflow

**1. Working on UI/Frontend:**
```bash
npm start           # Start backend once
frontend-dev.bat    # Start frontend with hot reload
```

**2. Testing Everything:**
```bash
full-dev.bat        # Builds and starts complete app
```

**3. Quick Backend Testing:**
```bash
npm start           # Backend only (if frontend already built)
```

---

## ✨ Features

### 🎨 Modern UI
- **Exciting Design**: Glassmorphism effects, gradients, animations
- **Visual Solutions Branding**: Professional brand identity
- **Responsive**: Works on desktop and mobile
- **Real-time**: Live chat with thinking animations

### 🤖 AI Assistant
- **Smart Calendar Agent**: Understands natural language
- **Microsoft Graph Integration**: Real calendar access
- **Safety Controls**: Confirms before creating meetings
- **Tool Integration**: Python backend with calendar tools

### 🔧 Developer Experience
- **Hot Reload**: Instant UI updates during development
- **TypeScript**: Type safety and better IDE support
- **Modern Stack**: React 18, Vite, Tailwind CSS
- **Easy Deployment**: Ready for Azure App Service

---

## 📋 Dependencies

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Vite**: Fast build tool

### Backend
- **Express.js**: Web server
- **Python**: AI agent and calendar tools
- **Azure AI**: GPT-4 integration
- **Microsoft Graph**: Calendar API

---

## 🚀 Deployment

### Local Development
1. Install dependencies: `npm install`
2. Start development: `frontend-dev.bat`
3. Open: http://localhost:5173

### Production (Azure)
1. Build: `npm run build`
2. Deploy to Azure App Service
3. Set environment variables
4. Application runs on Azure URL

---

## 🔧 Configuration

### Environment Variables
```bash
# Azure AI Configuration
PROJECT_ENDPOINT=your-azure-ai-endpoint
MODEL_DEPLOYMENT_NAME=gpt-4o-calendar

# Microsoft Graph
GRAPH_TENANT_ID=your-tenant-id
GRAPH_CLIENT_ID=your-client-id
GRAPH_CLIENT_SECRET=your-client-secret

# User Settings
DEFAULT_USER_UPN=user@yourdomain.com
```

### Development Setup
1. Clone repository
2. Install dependencies: `npm install`
3. Configure `.env` file
4. Run: `frontend-dev.bat`

---

## 🎯 Architecture

```
React Frontend (Vite) ←→ Express.js Server ←→ Python AI Agent
       ↓                        ↓                    ↓
  Tailwind CSS            Static Files         Azure AI + Graph
```

**Development**: Frontend and backend run separately for fast development
**Production**: Express serves built React app as static files

---

## 📝 Scripts Reference

### Batch Files
- `frontend-dev.bat`: Frontend development server
- `full-dev.bat`: Complete development environment

### NPM Scripts
- `npm start`: Start production server
- `npm run build`: Build frontend for production
- `npm run dev`: Start backend in development mode

---

## 🔍 Troubleshooting

### Common Issues

**Port conflicts:**
- Frontend: Change port in `vite.config.ts`
- Backend: Change PORT in `server.js`

**Build errors:**
- Run `npm install` in both root and `frontend/`
- Check TypeScript errors: `npm run build`

**Python errors:**
- Ensure Python dependencies installed
- Check `.env` configuration

### Debug Mode
```bash
# Enable detailed logging
DEBUG=* npm start

# Check Python agent logs
cat debugging_logs/agent.log
```

---

## 📞 Support

For issues or questions:
1. Check logs in `debugging_logs/`
2. Verify environment variables
3. Test with `frontend-dev.bat` for development
4. Use `full-dev.bat` for complete testing

---