#!/usr/bin/env node
/**
 * Fetch one reviewer's session from Firebase using a local service-account
 * credential. Output matches fetch_reviewer_session.py so downstream
 * refinement analysis is unchanged.
 */

import { createSign } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';

function usage(message) {
  if (message) console.error(`Error: ${message}\n`);
  console.error('Usage: node fetch_firebase_reviewer_session.mjs <studyName> --pid <participantId> --out <directory> [--dev] [--credentials <service-account.json>] [--bucket <bucket-name>]');
  process.exitCode = 2;
}

function parseArgs(argv) {
  const [studyName, ...rest] = argv;
  if (!studyName) {
    usage('missing study name');
    return null;
  }
  const args = { studyName, dev: false };
  for (let index = 0; index < rest.length; index += 1) {
    const argument = rest[index];
    if (argument === '--dev') {
      args.dev = true;
    } else if (argument === '--pid' || argument === '--out' || argument === '--credentials' || argument === '--bucket') {
      const value = rest[index + 1];
      if (!value || value.startsWith('--')) {
        usage(`missing value for ${argument}`);
        return null;
      }
      args[{
        '--pid': 'pid', '--out': 'out', '--credentials': 'credentialsPath', '--bucket': 'bucket',
      }[argument]] = value;
      index += 1;
    } else {
      usage(`unknown argument ${argument}`);
      return null;
    }
  }
  if (!args.pid || !args.out) {
    usage('--pid and --out are required');
    return null;
  }
  return args;
}

function encodeBase64Url(value) {
  return Buffer.from(value).toString('base64url');
}

async function getAccessToken(credentials) {
  const issuedAt = Math.floor(Date.now() / 1000);
  const header = encodeBase64Url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const payload = encodeBase64Url(JSON.stringify({
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/devstorage.read_only https://www.googleapis.com/auth/datastore',
    aud: 'https://oauth2.googleapis.com/token',
    iat: issuedAt,
    exp: issuedAt + 3600,
  }));
  const signer = createSign('RSA-SHA256');
  signer.update(`${header}.${payload}`);
  const assertion = `${header}.${payload}.${signer.sign(credentials.private_key, 'base64url')}`;
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    }),
  });
  if (!response.ok) throw new Error(`Google OAuth failed: ${response.status} ${await response.text()}`);
  return (await response.json()).access_token;
}

async function googleRequest(url, token) {
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(`Google API request failed: ${response.status} ${await response.text()}`);
  return response;
}

async function download(bucket, objectPath, destination, token) {
  const url = `https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(bucket)}/o/${encodeURIComponent(objectPath)}?alt=media`;
  const response = await googleRequest(url, token);
  const bytes = new Uint8Array(await response.arrayBuffer());
  await mkdir(resolve(destination, '..'), { recursive: true });
  await writeFile(destination, bytes);
}

async function listObjects(bucket, prefix, token) {
  const url = new URL(`https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(bucket)}/o`);
  url.searchParams.set('prefix', prefix);
  const response = await googleRequest(url, token);
  return (await response.json()).items || [];
}

async function fetchSequenceAssignment(projectId, studyPrefix, participantId, token, destination) {
  const documentPath = `${studyPrefix}/sequenceAssignment/sequenceAssignment/${participantId}`;
  const url = `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents/${documentPath}`;
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (response.status === 404) return false;
  if (!response.ok) throw new Error(`Firestore sequence-assignment request failed: ${response.status} ${await response.text()}`);
  await writeFile(destination, `${JSON.stringify(await response.json(), null, 2)}\n`);
  return true;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) return;
  const credentialsPath = args.credentialsPath || process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (!credentialsPath) throw new Error('pass --credentials <service-account.json> or set GOOGLE_APPLICATION_CREDENTIALS');
  const credentials = JSON.parse(await readFile(resolve(credentialsPath), 'utf8'));
  if (!credentials.client_email || !credentials.private_key || !credentials.project_id) {
    throw new Error('service-account JSON must include project_id, client_email, and private_key');
  }
  const token = await getAccessToken(credentials);
  const bucket = args.bucket || process.env.FIREBASE_STORAGE_BUCKET || `${credentials.project_id}.appspot.com`;
  const prefix = `${args.dev ? 'dev' : 'prod'}-${args.studyName}`;
  const out = resolve(args.out);
  await download(bucket, `${prefix}/participants/${args.pid}_participantData`, `${out}/participantData.json`, token);
  console.log(`fetched participant ${args.pid}`);
  const sequenceFound = await fetchSequenceAssignment(credentials.project_id, prefix, args.pid, token, `${out}/sequenceAssignment.json`);
  console.log(`sequence assignment: ${sequenceFound ? 'fetched' : 'not found'}`);
  for (const kind of ['screenRecording', 'audio']) {
    const listing = await listObjects(bucket, `${prefix}/${kind}/${args.pid}_`, token);
    const matches = listing.filter((item) => !item.name.endsWith('.wav_transcription.txt'));
    console.log(`${kind}: ${matches.length} file(s)`);
    for (const item of matches) {
      const identifier = item.name.slice(`${prefix}/${kind}/${args.pid}_`.length);
      const destination = `${out}/${kind}/${identifier}.webm`;
      await download(bucket, item.name, destination, token);
      console.log(`  ${destination}`);
    }
  }
  console.log(`\nDone. Session data in ${out}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});