const fs = require('fs');
const path = require('path');

class RotatingLogger {
  constructor(logDir = 'debugging_logs', maxLines = 30) {
    this.logDir = path.join(process.cwd(), logDir);
    this.maxLines = maxLines;
    
    // Ensure log directory exists
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  log(filename, message) {
    const logFile = path.join(this.logDir, `${filename}.log`);
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}`;
    
    try {
      // Read existing lines if file exists
      let existingLines = [];
      if (fs.existsSync(logFile)) {
        const content = fs.readFileSync(logFile, 'utf8');
        existingLines = content.split('\n').filter(line => line.trim());
      }
      
      // Add separator line for new sessions (when server starts)
      if (message.includes('server started') || message.includes('Calendar Agent server')) {
        existingLines.push(''); // Add blank line
        existingLines.push('='.repeat(80));
        existingLines.push(`NEW SESSION - ${timestamp}`);
        existingLines.push('='.repeat(80));
      }
      
      // Add new line
      existingLines.push(logEntry);
      
      // Keep only last maxLines
      if (existingLines.length > this.maxLines) {
        existingLines = existingLines.slice(-this.maxLines);
      }
      
      // Write back to file with proper spacing
      fs.writeFileSync(logFile, existingLines.join('\n') + '\n');
      
    } catch (error) {
      console.error(`Failed to write to log file ${filename}:`, error);
    }
  }

  // Only 2 log files: server.log and agent.log
  server(message) {
    this.log('server', `SERVER: ${message}`);
  }

  agent(message) {
    this.log('agent', `AGENT: ${message}`);
  }
}

module.exports = RotatingLogger;
