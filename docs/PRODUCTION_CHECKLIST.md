# Production Deployment Checklist

This comprehensive checklist ensures your Madcrow Backend is production-ready with proper security, performance, and monitoring configurations.

## 🔒 Security Configuration

### Critical Security Headers

#### ⚠️ Content Security Policy (CSP) - HIGH PRIORITY

```bash
# ❌ DEVELOPMENT (Current Default - NOT for production)
SECURITY_CSP_SCRIPT_SRC='self' 'unsafe-inline'

# ✅ PRODUCTION (Recommended)
SECURITY_CSP_SCRIPT_SRC='self'
SECURITY_CSP_STYLE_SRC='self'
```

**Why**: `'unsafe-inline'` allows inline JavaScript/CSS which can be exploited for XSS attacks.

**Action Required**:

- [ ] Remove `'unsafe-inline'` from `SECURITY_CSP_SCRIPT_SRC`
- [ ] Remove `'unsafe-inline'` from `SECURITY_CSP_STYLE_SRC`
- [ ] Test your frontend to ensure no inline scripts/styles break
- [ ] Use nonces or hashes for any required inline content

#### HSTS Configuration

```bash
# ✅ PRODUCTION Settings
SECURITY_HSTS_ENABLED=true
SECURITY_HSTS_MAX_AGE=31536000  # 1 year
SECURITY_HSTS_INCLUDE_SUBDOMAINS=true
SECURITY_HSTS_PRELOAD=true  # Enable for maximum security
```

**Checklist**:

- [ ] HSTS enabled with minimum 1 year max-age
- [ ] Include subdomains if applicable
- [ ] Consider HSTS preload for public sites

#### Frame Protection

```bash
# ✅ PRODUCTION Settings
SECURITY_X_FRAME_OPTIONS=DENY
SECURITY_CSP_FRAME_ANCESTORS='none'
```

**Checklist**:

- [ ] Verify your API doesn't need to be embedded in iframes
- [ ] Use `SAMEORIGIN` only if same-origin embedding is required

### Environment Variables Audit

#### Required Production Settings

```bash
# Environment (Documentation will be automatically disabled)
DEPLOY_ENV=PRODUCTION
DEBUG=false

# Security
SECRET_KEY=<strong-random-key-minimum-32-chars>
SECURITY_HEADERS_ENABLED=true
SECURITY_HSTS_PRELOAD=true

# Database
DB_PASSWORD=<strong-database-password>
DB_HOST=<production-database-host>

# CORS (Restrict to your domains)
WEB_API_CORS_ALLOW_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Checklist**:

- [ ] `DEBUG=false` in production
- [ ] Strong `SECRET_KEY` (use `openssl rand -base64 42`)
- [ ] Restrict CORS origins to your actual domains
- [ ] Strong database credentials
- [ ] All sensitive values in environment variables (not hardcoded)

## 🗄️ Database Security

### Connection Security

```bash
# ✅ PRODUCTION Database Settings
SQLALCHEMY_DATABASE_URI_SCHEME=postgresql+psycopg
DB_EXTRAS=sslmode=require&connect_timeout=10
SQLALCHEMY_POOL_PRE_PING=true
SQLALCHEMY_POOL_RECYCLE=3600
```

**Checklist**:

- [ ] SSL/TLS enabled for database connections
- [ ] Connection pooling configured appropriately
- [ ] Database user has minimal required permissions
- [ ] Regular database backups configured
- [ ] Database monitoring enabled

### Migration Safety

**Checklist**:

- [ ] All migrations tested in staging environment
- [ ] Database backup before running migrations
- [ ] Rollback plan prepared
- [ ] Migration scripts reviewed for performance impact

## 🌐 Network & Infrastructure

### HTTPS & SSL

**Checklist**:

- [ ] Valid SSL certificate installed
- [ ] HTTP redirects to HTTPS
- [ ] SSL Labs test score A or A+
- [ ] Certificate auto-renewal configured

### Load Balancer & Reverse Proxy

**Checklist**:

- [ ] Proper health check endpoints configured (`/api/v1/health`)
- [ ] Request timeout settings appropriate
- [ ] Rate limiting configured
- [ ] Real IP forwarding configured (`proxy_headers=True` in uvicorn)

## 📊 Monitoring & Logging

### Application Monitoring

```bash
# ✅ PRODUCTION Logging
LOG_LEVEL=INFO  # Not DEBUG in production
LOG_FILE_MAX_SIZE=100  # MB
LOG_FILE_BACKUP_COUNT=10
```

**Checklist**:

- [ ] Application performance monitoring (APM) configured
- [ ] Error tracking service integrated
- [ ] Health check monitoring
- [ ] Database performance monitoring
- [ ] Log aggregation system configured

### Security Monitoring

**Checklist**:

- [ ] Failed authentication attempts monitoring
- [ ] Unusual traffic pattern detection
- [ ] Security headers validation monitoring
- [ ] SSL certificate expiration monitoring

## 🚀 Performance Optimization

### Application Performance

```bash
# ✅ PRODUCTION Performance Settings
API_COMPRESSION_ENABLED=true
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_MAX_OVERFLOW=10
```

**Checklist**:

- [ ] Response compression enabled
- [ ] Database connection pooling optimized
- [ ] Async operations used for I/O
- [ ] Caching strategy implemented (Redis)
- [ ] Static assets served via CDN

### Resource Limits

**Checklist**:

- [ ] Memory limits configured
- [ ] CPU limits appropriate
- [ ] Request timeout limits set
- [ ] File upload size limits configured

## 🔐 Authentication & Authorization

### Security Implementation

**Checklist**:

- [ ] Strong password policies enforced
- [ ] JWT tokens with appropriate expiration
- [ ] Refresh token rotation implemented
- [ ] Rate limiting on authentication endpoints
- [ ] Account lockout after failed attempts
- [ ] Two-factor authentication available

## 🧪 Testing & Validation

### Pre-Deployment Testing

**Checklist**:

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Security headers test passing (`uv run python test_security_headers.py`)
- [ ] Load testing completed
- [ ] Security scanning completed

### Security Validation Tools

```bash
# Test security headers
curl -I https://yourdomain.com/api/v1/health

# Online security tests
# - https://securityheaders.com/
# - https://observatory.mozilla.org/
# - https://www.ssllabs.com/ssltest/
```

**Checklist**:

- [ ] Security headers scan (A+ rating)
- [ ] SSL/TLS configuration test (A+ rating)
- [ ] Vulnerability scanning completed
- [ ] Penetration testing completed (if required)

## 📋 Deployment Process

### Pre-Deployment

**Checklist**:

- [ ] Code review completed
- [ ] All tests passing in CI/CD
- [ ] Database migration plan reviewed
- [ ] Rollback plan prepared
- [ ] Monitoring alerts configured

### Deployment

**Checklist**:

- [ ] Blue-green or rolling deployment strategy
- [ ] Health checks passing after deployment
- [ ] Database migrations applied successfully
- [ ] Cache warming completed (if applicable)
- [ ] Smoke tests passing

### Post-Deployment

**Checklist**:

- [ ] Application responding correctly
- [ ] All endpoints returning expected responses
- [ ] Error rates within normal range
- [ ] Performance metrics normal
- [ ] Security headers present and correct

## 🚨 Emergency Procedures

### Incident Response

**Checklist**:

- [ ] Incident response plan documented
- [ ] Emergency contacts list updated
- [ ] Rollback procedures tested
- [ ] Communication plan for outages
- [ ] Security incident response plan

## 📝 Documentation

### Required Documentation

**Checklist**:

- [ ] API documentation updated
- [ ] Deployment procedures documented
- [ ] Environment setup guide current
- [ ] Security configuration documented
- [ ] Monitoring runbooks created

## 🔄 Maintenance

### Regular Tasks

**Checklist**:

- [ ] Dependency updates scheduled
- [ ] Security patches applied promptly
- [ ] Log rotation configured
- [ ] Database maintenance scheduled
- [ ] SSL certificate renewal automated

---

## 🎯 Quick Production Readiness Score

**Security**: **_/10
**Performance**: _**/10
**Monitoring**: **_/10
**Documentation**: _**/10
**Testing**: \_\_\_/10

**Overall Score**: \_\_\_/50

### Minimum Requirements for Production

- [ ] Security Score ≥ 8/10
- [ ] All "HIGH PRIORITY" items completed
- [ ] SSL/HTTPS properly configured
- [ ] Monitoring and alerting active
- [ ] Backup and recovery procedures tested

---

_Last Updated: $(date)_
_Review this checklist before every production deployment_
