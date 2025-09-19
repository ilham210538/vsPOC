const express = require('express');
const cors = require('cors');
const path = require('path');
const { spawn, execSync } = require('child_process');
const RotatingLogger = require('./src/logger');

const app = express();
const PORT = process.env.PORT || 8080;

// Initialize rotating logger
const logger = new RotatingLogger('debugging_logs', 30);

// Detect Python executable based on environment
let pythonPath;
if (process.env.WEBSITE_INSTANCE_ID) {
  // Azure App Service (Linux) - use system python3
  pythonPath = 'python3';
  console.log('🐍 Running on Azure App Service - using python3');
} else {
  // Local development - try different Python executables
  try {
    execSync('python --version', { stdio: 'ignore' });
    pythonPath = 'python';
    console.log('🐍 Local development - using python');
  } catch {
    try {
      execSync('python3 --version', { stdio: 'ignore' });
      pythonPath = 'python3';
      console.log('🐍 Local development - using python3');
    } catch {
      try {
        execSync('py --version', { stdio: 'ignore' });
        pythonPath = 'py';
        console.log('🐍 Local development - using py launcher');
      } catch {
        console.error('❌ No Python executable found! Install Python or activate your virtual environment.');
        process.exit(1);
      }
    }
  }
}

console.log('🐍 Python dependencies pre-installed in py_deps folder via GitHub Actions');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Session management - store sessions per client (simplified to single session for now)
let currentSession = {
  threadId: null,
  initialized: false
};

// Helper function to communicate with Python agent session
function sendToAgentSession(action, message = null) {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'src', 'agent_session.py');
    
    // Use detected python executable - dependencies are in py_deps folder via PYTHONPATH
    const python_cmd = pythonPath;
    
    // Build command arguments
    const args = ['--action', action, '--json'];
    if (message) {
      args.push('--message', message);
    }
    
    // Spawn Python process
    const python = spawn(python_cmd, [pythonScript, ...args], {
      env: {
        ...process.env,
        PYTHONPATH: path.join(__dirname, 'py_deps')
      }
    });
    
    let output = '';
    let errorOutput = '';
    
    python.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      const stderrText = data.toString().trim();
      errorOutput += stderrText;
      
      // Only log actual errors, not debug/info messages from Python
      if (stderrText.includes('ERROR:') || stderrText.includes('CRITICAL:') || stderrText.includes('Exception') || stderrText.includes('Traceback')) {
        console.error('� Python Error:', stderrText);
      } else if (stderrText.includes('WARNING:')) {
        console.warn('⚠️  Python Warning:', stderrText);
      }
      // Suppress debug/info stderr spam in Azure Log Stream
    });
    
    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output.trim());
          if (result.thread_id) {
            currentSession.threadId = result.thread_id;
            currentSession.initialized = true;
          }
          resolve(result);
        } catch (e) {
          console.error('❌ Failed to parse Python output:', e);
          console.error('❌ Raw output:', output);
          logger.server(`Failed to parse Python output: ${output}`);
          resolve({
            status: 'error',
            message: 'Failed to parse agent response',
            thread_id: currentSession.threadId
          });
        }
      } else {
        console.error('❌ Python script failed with code:', code);
        console.error('❌ Error output:', errorOutput);
        logger.server(`Python script error: ${errorOutput}`);
        reject(new Error(errorOutput || 'Python script failed'));
      }
    });
    
    python.on('error', (error) => {
      logger.server(`Python spawn error: ${error.message}`);
      reject(error);
    });
  });
}

// API Routes
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    
    if (!message || typeof message !== 'string') {
      return res.status(400).json({
        status: 'error',
        message: 'Message is required and must be a string'
      });
    }
    
    logger.server(`Received message: ${message}`);
    
    // Send to Python agent session - this will create/reuse the same agent and thread
    const result = await sendToAgentSession('message', message);
    
    logger.server(`Agent response status: ${result.status}, thread: ${result.thread_id}`);
    
    res.json({
      status: result.status || 'success',
      message: result.message || 'Response received',
      thread_id: result.thread_id || currentSession.threadId,
      timestamp: new Date().toISOString(),
      tool_calls: result.tool_calls || []
    });
    
  } catch (error) {
    logger.server(`Chat API error: ${error.message}`);
    res.status(500).json({
      status: 'error',
      message: 'Failed to process message: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    thread_id: currentSession.threadId,
    session_initialized: currentSession.initialized
  });
});

// Reset conversation - creates new thread but keeps same agent
app.post('/api/reset', async (req, res) => {
  try {
    logger.server('Resetting conversation session...');
    
    // Reset the session - this will create a new thread
    const result = await sendToAgentSession('reset');
    
    logger.server(`Session reset successful, new thread: ${result.thread_id}`);
    
    res.json({
      status: result.status || 'success',
      message: result.message || 'Conversation reset - new thread created',
      thread_id: result.thread_id || null,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    logger.server(`Reset API error: ${error.message}`);
    res.status(500).json({
      status: 'error',
      message: 'Failed to reset conversation: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Cleanup session - for when server shuts down
app.post('/api/cleanup', async (req, res) => {
  try {
    logger.server('Cleaning up agent session...');
    
    const result = await sendToAgentSession('cleanup');
    currentSession.threadId = null;
    currentSession.initialized = false;
    
    logger.server('Session cleanup completed');
    
    res.json({
      status: result.status || 'success',
      message: result.message || 'Session cleaned up',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    logger.server(`Cleanup API error: ${error.message}`);
    res.status(500).json({
      status: 'error',
      message: 'Failed to cleanup session: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Serve React app for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
  logger.server(`Calendar Agent server started on port ${PORT}`);
  logger.server(`Frontend available at: http://localhost:${PORT}`);
  logger.server(`API available at: http://localhost:${PORT}/api`);
  logger.server('Session Management: Persistent agent and thread across messages');
  
  console.log(`🚀 Calendar Agent server running on port ${PORT}`);
  console.log(`📱 Frontend: http://localhost:${PORT}`);
  console.log(`🔗 API: http://localhost:${PORT}/api`);
  console.log(`📋 Session Management: Persistent agent and thread across messages`);
  console.log(`📁 Logs: debugging_logs/ folder (max 30 lines per file)`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.server('Received SIGINT, shutting down...');
  console.log('Shutting down server...');
  try {
    // Cleanup agent session before shutdown
    await sendToAgentSession('cleanup');
    logger.server('Cleanup completed during shutdown');
  } catch (error) {
    logger.server(`Error during cleanup: ${error.message}`);
  }
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.server('Received SIGTERM, shutting down gracefully...');
  console.log('Received SIGTERM, shutting down gracefully...');
  try {
    await sendToAgentSession('cleanup');
    logger.server('Cleanup completed during shutdown');
  } catch (error) {
    logger.server(`Error during cleanup: ${error.message}`);
  }
  process.exit(0);
});
