import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pythonExe = path.resolve(__dirname, '..', 'venv', 'Scripts', 'python.exe');
const serverPy = path.resolve(__dirname, '..', 'backend', 'server.py');

console.log('Spawning Edufeedia FastAPI backend on http://127.0.0.1:8000 ...');

const child = spawn(pythonExe, [serverPy], {
  cwd: path.resolve(__dirname, '..', 'backend'),
  stdio: ['ignore', 'pipe', 'pipe'],
  env: { ...process.env, PYTHONPATH: path.resolve(__dirname, '..', 'backend') }
});

child.stdout.on('data', (data) => {
  process.stdout.write(data);
});

child.stderr.on('data', (data) => {
  process.stderr.write(data);
});

child.on('error', (err) => {
  console.error('Backend spawn error:', err);
});

child.on('exit', (code, signal) => {
  console.log(`Backend server exited with code ${code}, signal ${signal}`);
});
