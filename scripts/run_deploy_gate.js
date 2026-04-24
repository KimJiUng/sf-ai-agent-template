#!/usr/bin/env node
/**
 * Cross-platform Deploy Gate runner.
 *
 * The template keeps PowerShell and Bash wrappers for direct use, while npm
 * scripts call this file so Codex/Claude can run the same command on Windows,
 * macOS, and Linux.
 */
const { spawnSync } = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const action = process.argv[2] || 'check';
const args = process.argv.slice(3);

function run(command, commandArgs, options = {}) {
  const result = spawnSync(command, commandArgs, {
    cwd: options.cwd || root,
    stdio: 'inherit',
    shell: false,
  });

  if (result.error) {
    if (result.error.code === 'ENOENT') {
      return { status: 127 };
    }
    console.error(result.error.message);
    return { status: 1 };
  }

  return { status: result.status ?? 0 };
}

function canRun(command, commandArgs) {
  const result = spawnSync(command, commandArgs, {
    cwd: root,
    stdio: 'ignore',
    shell: false,
  });
  return !result.error && result.status === 0;
}

function findPython() {
  const candidates = process.platform === 'win32'
    ? [['python', ['--version']], ['py', ['-3', '--version']], ['python3', ['--version']]]
    : [['python3', ['--version']], ['python', ['--version']]];

  for (const [command, commandArgs] of candidates) {
    if (canRun(command, commandArgs)) {
      return { command, prefixArgs: command === 'py' ? ['-3'] : [] };
    }
  }

  console.error('Python 3 is required for Deploy Gate, but no python command was found.');
  process.exit(2);
}

function parseDeployArgs(inputArgs) {
  const deployArgs = [];
  let targetOrg = '';
  let sessionDir = '';

  for (let i = 0; i < inputArgs.length; i += 1) {
    const value = inputArgs[i];

    if (value === '--session-dir') {
      sessionDir = inputArgs[i + 1] || '';
      i += 1;
      continue;
    }

    if (value.startsWith('--session-dir=')) {
      sessionDir = value.slice('--session-dir='.length);
      continue;
    }

    if (value === '-TargetOrg' || value === '--target-org' || value === '-o') {
      targetOrg = inputArgs[i + 1] || '';
      i += 1;
      continue;
    }

    if (value.startsWith('--target-org=')) {
      targetOrg = value.slice('--target-org='.length);
      continue;
    }

    if (!targetOrg && !value.startsWith('-')) {
      targetOrg = value;
      continue;
    }

    deployArgs.push(value);
  }

  return { targetOrg, sessionDir, deployArgs };
}

const python = findPython();
const pyArgs = (...parts) => [...python.prefixArgs, ...parts];

if (action === 'check') {
  const result = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'deploy_gate_check.py'), root),
  );
  if (result.status !== 0) {
    process.exit(result.status);
  }

  const review = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'debt_scan.py'), root),
  );
  if (review.status !== 0) {
    console.error('Review Gate debt scan failed, but this does not block static validation.');
  }
  process.exit(0);
}

if (action === 'snapshot') {
  const result = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'work_snapshot.py'), ...args),
  );
  process.exit(result.status);
}

if (action === 'debt-scan') {
  const result = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'debt_scan.py'), root, ...args),
  );
  process.exit(result.status);
}

if (action === 'test-scripts') {
  const result = run(
    python.command,
    pyArgs('-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_*.py'),
  );
  process.exit(result.status);
}

if (action === 'deploy') {
  const { targetOrg, sessionDir, deployArgs } = parseDeployArgs(args);

  if (!targetOrg) {
    console.error('Usage: npm run deploy:safe -- --target-org <ORG_ALIAS> [additional sf deploy args]');
    process.exit(2);
  }

  console.log('Running Deploy Gate pre-deploy validation...');
  let result = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'deploy_gate_check.py'), root),
  );
  if (result.status !== 0) {
    console.error('Validation failed. Deployment will be stopped.');
    process.exit(result.status);
  }

  console.log('Validation passed. Running org-aware pre-deploy check...');
  const orgCheckArgs = [path.join(root, 'scripts', 'deploy_org_check.py'), root, targetOrg];
  if (sessionDir) {
    orgCheckArgs.push('--session-dir', sessionDir);
  }
  result = run(
    python.command,
    pyArgs(...orgCheckArgs, ...deployArgs),
  );
  if (result.status !== 0) {
    console.error('Org-aware check failed. Deployment will be stopped.');
    process.exit(result.status);
  }

  console.log('Running Review Gate debt scan...');
  result = run(
    python.command,
    pyArgs(path.join(root, 'scripts', 'debt_scan.py'), root),
  );
  if (result.status !== 0) {
    console.error('Review Gate debt scan failed. Deployment will be stopped for review.');
    process.exit(result.status);
  }

  console.log('All checks passed. Starting Salesforce deployment...');
  result = run('sf', ['project', 'deploy', 'start', '--target-org', targetOrg, ...deployArgs]);
  process.exit(result.status);
}

console.error(`Unknown Deploy Gate action: ${action}`);
process.exit(2);
