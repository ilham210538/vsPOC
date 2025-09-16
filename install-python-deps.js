const { execSync } = require('child_process');
const fs = require('fs');

console.log('🐍 Installing Python dependencies...');

try {
  // Check if req.txt exists
  if (!fs.existsSync('req.txt')) {
    console.log('❌ req.txt not found');
    process.exit(1);
  }

  // Try different Python commands
  const pythonCommands = ['python3', 'python', '/opt/python/3.11/bin/python3'];
  
  for (const pythonCmd of pythonCommands) {
    try {
      console.log(`🔍 Trying ${pythonCmd}...`);
      execSync(`${pythonCmd} --version`, { stdio: 'inherit' });
      
      console.log(`✅ Using ${pythonCmd} to install packages`);
      execSync(`${pythonCmd} -m pip install -r req.txt`, { stdio: 'inherit' });
      
      console.log('✅ Python dependencies installed successfully!');
      process.exit(0);
    } catch (error) {
      console.log(`❌ ${pythonCmd} failed:`, error.message);
    }
  }
  
  console.log('❌ No working Python installation found');
  process.exit(1);
  
} catch (error) {
  console.error('❌ Installation failed:', error.message);
  process.exit(1);
}
