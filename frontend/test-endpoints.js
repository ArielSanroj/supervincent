#!/usr/bin/env node

/**
 * Script para probar todos los endpoints del frontend y backend
 * Uso: node test-endpoints.js [backend_url]
 * Ejemplo: node test-endpoints.js https://your-ngrok-url.ngrok.io
 */

const axios = require('axios');

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

const backendUrl = process.argv[2] || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';
const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3001';

console.log(`${colors.cyan}🧪 Testing Endpoints${colors.reset}`);
console.log(`${colors.blue}Backend URL: ${backendUrl}${colors.reset}`);
console.log(`${colors.blue}Frontend URL: ${frontendUrl}${colors.reset}\n`);

const results = {
  passed: [],
  failed: [],
  skipped: [],
};

async function testEndpoint(name, url, method = 'GET', data = null, isBackend = false) {
  const baseUrl = isBackend ? backendUrl : frontendUrl;
  const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
  
  try {
    const config = {
      method,
      url: fullUrl,
      timeout: 10000,
    };
    
    if (data) {
      config.data = data;
      config.headers = { 'Content-Type': 'application/json' };
    }
    
    const response = await axios(config);
    results.passed.push({ name, url: fullUrl, status: response.status });
    console.log(`${colors.green}✅ PASS${colors.reset} ${name} (${response.status})`);
    return { success: true, status: response.status, data: response.data };
  } catch (error) {
    const status = error.response?.status || 'ERROR';
    const message = error.response?.data?.error || error.response?.data?.message || error.message;
    results.failed.push({ name, url: fullUrl, status, error: message });
    console.log(`${colors.red}❌ FAIL${colors.reset} ${name} (${status}): ${message}`);
    return { success: false, status, error: message };
  }
}

async function runTests() {
  console.log(`${colors.cyan}📡 Testing Backend Endpoints${colors.reset}\n`);
  
  // Backend endpoints
  await testEndpoint('Backend: /processed/recent', '/processed/recent', 'GET', null, true);
  await testEndpoint('Backend: /cache/stats', '/cache/stats', 'GET', null, true);
  await testEndpoint('Backend: /tax/rules', '/tax/rules', 'GET', null, true);
  await testEndpoint('Backend: /reports/general-ledger', '/reports/general-ledger?start_date=2025-01-01&end_date=2025-12-31', 'GET', null, true);
  await testEndpoint('Backend: /reports/trial-balance', '/reports/trial-balance?start_date=2025-01-01&end_date=2025-12-31', 'GET', null, true);
  await testEndpoint('Backend: /reports/aging', '/reports/aging?start_date=2025-01-01&end_date=2025-12-31', 'GET', null, true);
  
  console.log(`\n${colors.cyan}🌐 Testing Frontend API Routes${colors.reset}\n`);
  
  // Frontend API routes (Next.js)
  await testEndpoint('Frontend: /api/finance', '/api/finance', 'GET');
  await testEndpoint('Frontend: /api/finance/recent', '/api/finance/recent', 'GET');
  await testEndpoint('Frontend: /api/finance/withholdings', '/api/finance/withholdings', 'GET');
  await testEndpoint('Frontend: /api/reports/general-ledger', '/api/reports/general-ledger?start_date=2025-01-01&end_date=2025-12-31', 'GET');
  await testEndpoint('Frontend: /api/reports/trial-balance', '/api/reports/trial-balance?start_date=2025-01-01&end_date=2025-12-31', 'GET');
  await testEndpoint('Frontend: /api/reports/aging', '/api/reports/aging?start_date=2025-01-01&end_date=2025-12-31', 'GET');
  await testEndpoint('Frontend: /api/tax/rules', '/api/tax/rules', 'GET');
  
  // Skip POST endpoints that require files/data
  results.skipped.push(
    { name: 'Frontend: /api/finance/bulk-upload', reason: 'Requires multipart form-data' },
    { name: 'Backend: /process/upload', reason: 'Requires file upload' },
    { name: 'Backend: /process', reason: 'Requires file_path' },
    { name: 'Backend: /process/manual', reason: 'Requires invoice data' },
    { name: 'Backend: /process/upload-multiple', reason: 'Requires multiple files' },
    { name: 'Backend: /process/confirm-duplicate', reason: 'Requires duplicate confirmation' }
  );
  
  console.log(`\n${colors.yellow}⏭️  Skipped (require data/files)${colors.reset}`);
  results.skipped.forEach(skip => {
    console.log(`${colors.yellow}⏭️  ${skip.name}: ${skip.reason}${colors.reset}`);
  });
  
  // Summary
  console.log(`\n${colors.cyan}📊 Test Summary${colors.reset}`);
  console.log(`${colors.green}✅ Passed: ${results.passed.length}${colors.reset}`);
  console.log(`${colors.red}❌ Failed: ${results.failed.length}${colors.reset}`);
  console.log(`${colors.yellow}⏭️  Skipped: ${results.skipped.length}${colors.reset}`);
  
  if (results.failed.length > 0) {
    console.log(`\n${colors.red}❌ Failed Tests:${colors.reset}`);
    results.failed.forEach(fail => {
      console.log(`  - ${fail.name}: ${fail.error}`);
    });
    process.exit(1);
  } else {
    console.log(`\n${colors.green}🎉 All tests passed!${colors.reset}`);
    process.exit(0);
  }
}

runTests().catch(error => {
  console.error(`${colors.red}💥 Test runner error: ${error.message}${colors.reset}`);
  process.exit(1);
});

