/**
 * Integration test: health, auth rejection, SSE + POST /messages flow.
 * Run from mcp/: node --import dotenv/config scripts/test-mcp-http.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

function loadEnv() {
  try {
    const raw = readFileSync(join(root, '.env'), 'utf8');
    for (const line of raw.split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const i = t.indexOf('=');
      if (i === -1) continue;
      const k = t.slice(0, i).trim();
      let v = t.slice(i + 1).trim();
      if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
        v = v.slice(1, -1);
      }
      if (!process.env[k]) process.env[k] = v;
    }
  } catch {
    // rely on process.env
  }
}

loadEnv();

const PORT = process.env.PORT || '3000';
const BASE = `http://127.0.0.1:${PORT}`;
const TOKEN = process.env.AUTH_TOKEN;
const clientId = `test-${Date.now()}`;

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  process.exit(1);
}

function ok(msg) {
  console.log(`OK: ${msg}`);
}

async function main() {
  console.log(`\nMCP HTTP integration test → ${BASE}\n`);

  // 1) Health
  const health = await fetch(`${BASE}/health`);
  if (!health.ok) fail(`/health status ${health.status}`);
  const hj = await health.json();
  if (hj.status !== 'healthy') fail(`/health body: ${JSON.stringify(hj)}`);
  ok('/health returns healthy');

  // 2) SSE without auth → 401
  const noAuth = await fetch(`${BASE}/sse?clientId=x`);
  if (noAuth.status !== 401) fail(`/sse without auth expected 401, got ${noAuth.status}`);
  ok('/sse without Bearer returns 401');

  if (!TOKEN) fail('AUTH_TOKEN missing in .env');

  // 3) POST /messages without prior SSE → should error (500) when client unknown
  const orphan = await fetch(`${BASE}/messages?clientId=never-connected`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping' }),
  });
  if (orphan.status !== 500) fail(`orphan POST expected 500, got ${orphan.status}`);
  ok('POST /messages without SSE session returns 500 (expected)');

  // 4) SSE + message (stub response)
  const ac = new AbortController();
  const sseUrl = `${BASE}/sse?clientId=${encodeURIComponent(clientId)}`;
  const sseRes = await fetch(sseUrl, {
    headers: { Authorization: `Bearer ${TOKEN}` },
    signal: ac.signal,
  });
  if (!sseRes.ok) fail(`/sse with auth status ${sseRes.status}`);
  if (!sseRes.body) fail('/sse has no body');

  const reader = sseRes.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  let sawConnected = false;
  let sawMessage = false;
  let messagePayload = null;

  const parseBlocks = () => {
    const blocks = buf.split('\n\n');
    buf = blocks.pop() ?? '';
    for (const block of blocks) {
      let event = 'message';
      let dataLine = null;
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        if (line.startsWith('data:')) dataLine = line.slice(5).trim();
      }
      if (dataLine) {
        try {
          const data = JSON.parse(dataLine);
          if (event === 'connected') sawConnected = true;
          if (event === 'message') {
            sawMessage = true;
            messagePayload = data;
          }
        } catch {
          /* ignore */
        }
      }
    }
  };

  const readUntil = async (predicate, timeoutMs) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      parseBlocks();
      if (predicate()) return;
    }
  };

  await readUntil(() => sawConnected, 5000);
  if (!sawConnected) fail('did not receive SSE "connected" event');
  ok(`SSE connected (clientId=${clientId})`);

  const postRes = await fetch(`${BASE}/messages?clientId=${encodeURIComponent(clientId)}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: 42, method: 'tools/call', params: {} }),
  });
  if (!postRes.ok) fail(`POST /messages status ${postRes.status}: ${await postRes.text()}`);
  const postJ = await postRes.json();
  if (postJ.status !== 'accepted') fail(`POST body unexpected: ${JSON.stringify(postJ)}`);
  ok('POST /messages returns { status: "accepted" }');

  await readUntil(() => sawMessage, 5000);
  ac.abort();
  try {
    await reader.cancel();
  } catch {
    /* ignore */
  }

  if (!sawMessage) fail('did not receive SSE "message" event after POST');
  if (messagePayload?.result?.status !== 'processed') {
    fail(`unexpected SSE message payload: ${JSON.stringify(messagePayload)}`);
  }
  ok('SSE "message" event contains stub result { status: "processed" } (current implementation)');

  console.log('\nAll integration checks passed.\n');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
