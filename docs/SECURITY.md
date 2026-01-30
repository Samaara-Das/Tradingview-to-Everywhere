# Security Documentation
# TTE Tiered Screener Architecture

This document outlines security considerations, best practices, and threat mitigations for the system.

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [API Security](#api-security)
5. [Infrastructure Security](#infrastructure-security)
6. [Threat Model](#threat-model)
7. [Security Checklist](#security-checklist)
8. [Incident Response](#incident-response)

---

## Security Overview

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY BOUNDARIES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PUBLIC INTERNET                           │   │
│  │  ┌───────────────┐         ┌───────────────┐                │   │
│  │  │  TradingView  │──HTTPS──│  Stock Buddy  │                │   │
│  │  │   Webhooks    │         │   (Vercel)    │                │   │
│  │  └───────────────┘         └───────┬───────┘                │   │
│  └────────────────────────────────────┼────────────────────────┘   │
│                                       │                             │
│  ┌────────────────────────────────────┼────────────────────────┐   │
│  │                    PRIVATE NETWORK │                         │   │
│  │                     ┌──────────────▼──────────────┐         │   │
│  │                     │     MongoDB Atlas           │         │   │
│  │                     │  (IP Whitelist + Auth)      │         │   │
│  │                     └─────────────────────────────┘         │   │
│  │                                                              │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │           LOCAL MACHINE (Python Orchestrator)          │  │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │   │
│  │  │  │  Selenium   │  │   Chrome    │  │   .env      │    │  │   │
│  │  │  │  (Local)    │  │  Profile    │  │  (Secrets)  │    │  │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Trust Boundaries

| Boundary | Trust Level | Security Measures |
|----------|-------------|-------------------|
| TradingView → Stock Buddy | Low | Webhook secret validation |
| Stock Buddy → MongoDB | High | Connection string auth, IP whitelist |
| Python → Stock Buddy API | Medium | HTTPS, optional API key |
| Python → TradingView | High | Chrome profile with session |
| Dashboard → API | Public | Rate limiting, input validation |

---

## Authentication & Authorization

### Webhook Authentication

TradingView webhooks can include a secret for validation:

```typescript
// Stock Buddy API - Webhook validation
export default async function handler(req, res) {
  // Skip auth in development
  if (process.env.NODE_ENV === 'development') {
    return processWebhook(req, res);
  }

  const { secret } = req.body;
  const expectedSecret = process.env.WEBHOOK_SECRET;

  // Timing-safe comparison to prevent timing attacks
  if (!expectedSecret || !timingSafeEqual(secret, expectedSecret)) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      code: 'UNAUTHORIZED'
    });
  }

  return processWebhook(req, res);
}

function timingSafeEqual(a: string, b: string): boolean {
  if (!a || !b || a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
```

### MongoDB Authentication

- **Connection String Auth**: Username/password in connection string
- **Database User Permissions**: Read/write to specific database only
- **IP Whitelist**: Restrict access to known IPs

```javascript
// Create database user with minimal permissions
db.createUser({
  user: "tte_app",
  pwd: "strong-random-password",
  roles: [
    { role: "readWrite", db: "tte" }
  ]
})
```

### Dashboard Authentication (Future)

Currently public read access. For future authentication:

```typescript
// Example: NextAuth.js integration
import { getSession } from 'next-auth/react';

export default async function handler(req, res) {
  const session = await getSession({ req });

  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Proceed with authorized request
}
```

---

## Data Protection

### Sensitive Data Classification

| Data Type | Classification | Protection |
|-----------|----------------|------------|
| Webhook Secret | Secret | Environment variable, never logged |
| MongoDB URI | Secret | Environment variable, never logged |
| TradingView Session | Secret | Chrome profile, never exported |
| Trading Signals | Internal | Public read, write via webhook only |
| Hot List | Internal | Public read, write via webhook only |
| Screenshots | Public | Stored in TradingView CDN |

### Environment Variable Security

**DO**:
- Use `.env` files for local development
- Use Vercel Environment Variables for production
- Use different secrets for dev/staging/prod
- Rotate secrets periodically

**DON'T**:
- Commit `.env` files to git
- Log environment variables
- Share secrets in plain text
- Use the same secret across environments

### .gitignore Configuration

```gitignore
# Environment files
.env
.env.local
.env.*.local

# Credentials
*.pem
*.key
credentials.json
firebase-credentials.json

# Chrome profile data
chrome-profile/

# Logs (may contain sensitive data)
*.log
logs/
```

### Data Encryption

- **In Transit**: All API calls over HTTPS (TLS 1.2+)
- **At Rest**: MongoDB Atlas encrypts data at rest (AES-256)
- **Secrets**: Stored in platform-native secret managers

---

## API Security

### Input Validation

All API endpoints validate input:

```typescript
// Example: NWE endpoint validation
import { z } from 'zod';

const nweSchema = z.object({
  tier: z.literal('nwe'),
  symbol: z.string().min(3).max(20).regex(/^[A-Z0-9]+$/),
  direction: z.enum(['bullish', 'bearish']),
  timeframes: z.array(z.enum(['H4', 'D1'])).optional(),
  timestamp: z.number().int().positive().optional(),
  secret: z.string().optional()
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const validated = nweSchema.parse(req.body);
    // Process validated data
  } catch (error) {
    return res.status(400).json({
      success: false,
      error: 'Invalid payload',
      code: 'INVALID_PAYLOAD',
      details: error.errors
    });
  }
}
```

### Rate Limiting

Implemented at multiple levels:

| Level | Limit | Implementation |
|-------|-------|----------------|
| Vercel Edge | 1000 req/min | Platform default |
| API Endpoints | 100 req/min | Custom middleware |
| Database | Connection pool | MongoDB driver |

```typescript
// Simple rate limiting middleware
const rateLimits = new Map<string, { count: number; resetAt: number }>();

function rateLimit(req, res, next) {
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const now = Date.now();
  const windowMs = 60000; // 1 minute
  const maxRequests = 100;

  const record = rateLimits.get(ip) || { count: 0, resetAt: now + windowMs };

  if (now > record.resetAt) {
    record.count = 0;
    record.resetAt = now + windowMs;
  }

  record.count++;
  rateLimits.set(ip, record);

  if (record.count > maxRequests) {
    return res.status(429).json({
      success: false,
      error: 'Rate limit exceeded',
      code: 'RATE_LIMITED',
      details: { resetAt: record.resetAt }
    });
  }

  next();
}
```

### CORS Configuration

```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: 'https://stock-buddy-app.vercel.app' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PATCH, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type' },
        ],
      },
    ];
  },
};
```

### SQL/NoSQL Injection Prevention

```typescript
// GOOD: Parameterized queries
const signal = await db.collection('signals').findOne({ _id: new ObjectId(id) });

// BAD: String interpolation (vulnerable)
const signal = await db.collection('signals').findOne({ _id: `${id}` });
```

---

## Infrastructure Security

### Vercel Security

- Automatic HTTPS with Let's Encrypt
- DDoS protection at edge
- Isolated serverless functions
- Automatic security updates

### MongoDB Atlas Security

- Encryption at rest (AES-256)
- Encryption in transit (TLS)
- IP Access List (whitelist)
- Database audit logging
- Automated backups

**IP Whitelist Configuration**:
```
# For Vercel, allow all IPs (serverless = dynamic IPs)
0.0.0.0/0

# Or use Vercel's static IPs (requires paid plan)
# See: https://vercel.com/docs/concepts/functions/serverless-functions/streaming#static-ips
```

### Local Machine Security (Python Orchestrator)

- Run with minimal privileges
- Keep OS and dependencies updated
- Use firewall to block unnecessary ports
- Encrypt disk if storing sensitive data
- Don't expose Chrome profile

---

## Threat Model

### Identified Threats

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Webhook spoofing | Medium | Medium | Webhook secret validation |
| API abuse | High | Low | Rate limiting |
| Data exfiltration | Low | High | Access controls, audit logging |
| Session hijacking | Low | High | Secure Chrome profile storage |
| DDoS attack | Medium | Medium | Vercel edge protection |
| MongoDB breach | Low | High | Encryption, IP whitelist, strong auth |

### Attack Vectors

1. **Unauthorized Webhook Calls**
   - Attacker sends fake NWE/OBDIV webhooks
   - Mitigation: Webhook secret validation

2. **Enumeration Attacks**
   - Attacker scrapes all signals via API
   - Mitigation: Rate limiting, pagination limits

3. **Injection Attacks**
   - Attacker sends malicious payloads
   - Mitigation: Input validation, parameterized queries

4. **Credential Theft**
   - Attacker steals .env or Chrome profile
   - Mitigation: Secure storage, access controls

---

## Security Checklist

### Initial Setup

- [ ] Strong, unique webhook secret generated
- [ ] MongoDB user with minimal permissions created
- [ ] IP whitelist configured in MongoDB Atlas
- [ ] Environment variables set (not in code)
- [ ] `.gitignore` includes all sensitive files
- [ ] HTTPS enforced on all endpoints

### Ongoing Maintenance

- [ ] Dependencies updated monthly
- [ ] Secrets rotated quarterly
- [ ] Access logs reviewed weekly
- [ ] Security patches applied promptly
- [ ] Backup restoration tested quarterly

### Code Review Security Checks

- [ ] No hardcoded secrets
- [ ] All user input validated
- [ ] No SQL/NoSQL injection vulnerabilities
- [ ] Proper error handling (no stack traces in prod)
- [ ] Sensitive data not logged
- [ ] HTTPS used for all external calls

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| Critical | Data breach, system compromise | Immediate | Credential leak, unauthorized access |
| High | Service outage, security vulnerability | < 1 hour | API down, injection vulnerability |
| Medium | Degraded service, suspicious activity | < 4 hours | High error rate, unusual traffic |
| Low | Minor issues, potential risks | < 24 hours | Outdated dependency, minor bug |

### Incident Response Steps

1. **Identify**
   - Detect the incident
   - Assess severity
   - Document initial findings

2. **Contain**
   - Isolate affected systems
   - Disable compromised credentials
   - Block malicious IPs

3. **Eradicate**
   - Remove threat
   - Patch vulnerability
   - Update credentials

4. **Recover**
   - Restore service
   - Verify fix
   - Monitor for recurrence

5. **Learn**
   - Post-incident review
   - Update documentation
   - Improve defenses

### Security Contacts

| Role | Contact | Escalation Path |
|------|---------|-----------------|
| Security Lead | [Your Name] | Direct |
| Database Admin | [DBA Name] | Via Security Lead |
| Infrastructure | [DevOps Name] | Via Security Lead |

---

## Appendix: Generating Secrets

### Generate Webhook Secret

```bash
# OpenSSL (recommended)
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Generate Strong Password

```bash
# OpenSSL
openssl rand -base64 24

# Python
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Verify Secret Strength

Secrets should be:
- At least 32 characters
- Randomly generated (not human-created)
- Different for each environment
- Stored securely (never in code)

---

*Last updated: 2026-01-29*
