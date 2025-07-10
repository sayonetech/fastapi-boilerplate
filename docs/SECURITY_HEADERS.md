# Security Headers Implementation

This document describes the comprehensive security headers middleware implementation for the Madcrow Backend API.

## 🔒 Overview

The security headers middleware automatically adds essential security headers to **all HTTP responses** sent by your API server to protect against common web vulnerabilities including XSS, clickjacking, MIME sniffing, and more.

### ⚡ What This Does

- **Automatic Protection**: Adds security headers to every API response without manual intervention
- **Response Headers**: These are headers added to responses your server sends back to clients (not request headers)
- **Zero Code Changes**: Works transparently with existing endpoints
- **Configurable**: Each security header can be enabled/disabled and customized via environment variables
- **Production Ready**: Includes both development-friendly and production-strict configurations

### 🎯 Key Benefits

1. **XSS Protection**: Content Security Policy prevents cross-site scripting attacks
2. **Clickjacking Prevention**: X-Frame-Options stops malicious iframe embedding
3. **HTTPS Enforcement**: HSTS forces secure connections
4. **Information Disclosure**: Hides server details and controls referrer information
5. **Browser Security**: Leverages modern browser security features

## 🛡️ Security Headers Added to HTTP Responses

The following headers are automatically added to **every HTTP response** from your API:

### 📋 Complete Headers List

When a client makes a request to your API, these headers will be included in the response:

```http
HTTP/1.1 200 OK
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()
Server: Madcrow-API
X-Security-Headers: enabled
Content-Type: application/json
```

### 🔍 Detailed Header Explanations

### 1. HTTP Strict Transport Security (HSTS)
- **Purpose**: Enforces HTTPS connections and prevents protocol downgrade attacks
- **Header**: `Strict-Transport-Security`
- **Configuration**:
  - `SECURITY_HSTS_ENABLED`: Enable/disable HSTS
  - `SECURITY_HSTS_MAX_AGE`: Cache duration in seconds (default: 1 year)
  - `SECURITY_HSTS_INCLUDE_SUBDOMAINS`: Include subdomains in policy
  - `SECURITY_HSTS_PRELOAD`: Enable HSTS preload list inclusion

### 2. Content Security Policy (CSP)
- **Purpose**: Prevents XSS attacks by controlling resource loading
- **Header**: `Content-Security-Policy`
- **Configuration**:
  - `SECURITY_CSP_ENABLED`: Enable/disable CSP
  - `SECURITY_CSP_DEFAULT_SRC`: Default source policy
  - `SECURITY_CSP_SCRIPT_SRC`: Script source policy
  - `SECURITY_CSP_STYLE_SRC`: Style source policy
  - `SECURITY_CSP_IMG_SRC`: Image source policy
  - `SECURITY_CSP_FONT_SRC`: Font source policy
  - `SECURITY_CSP_CONNECT_SRC`: Connection source policy
  - `SECURITY_CSP_FRAME_ANCESTORS`: Frame ancestors policy

### 3. X-Frame-Options
- **Purpose**: Prevents clickjacking attacks
- **Header**: `X-Frame-Options`
- **Configuration**: `SECURITY_X_FRAME_OPTIONS` (default: DENY)

### 4. X-Content-Type-Options
- **Purpose**: Prevents MIME sniffing attacks
- **Header**: `X-Content-Type-Options: nosniff`
- **Configuration**: `SECURITY_X_CONTENT_TYPE_OPTIONS`

### 5. X-XSS-Protection
- **Purpose**: Legacy XSS protection (for older browsers)
- **Header**: `X-XSS-Protection: 1; mode=block`
- **Configuration**: `SECURITY_X_XSS_PROTECTION`

### 6. Referrer-Policy
- **Purpose**: Controls referrer information sent with requests
- **Header**: `Referrer-Policy`
- **Configuration**: `SECURITY_REFERRER_POLICY` (default: strict-origin-when-cross-origin)

### 7. Permissions-Policy
- **Purpose**: Controls browser features and APIs
- **Header**: `Permissions-Policy`
- **Configuration**:
  - `SECURITY_PERMISSIONS_POLICY_ENABLED`: Enable/disable
  - `SECURITY_PERMISSIONS_POLICY`: Policy directives

### 8. Server Header Control
- **Purpose**: Hides or customizes server information
- **Configuration**:
  - `SECURITY_HIDE_SERVER_HEADER`: Hide server header
  - `SECURITY_SERVER_HEADER_VALUE`: Custom server header value

## 👥 Client/Frontend Impact

### What Frontend Developers Need to Know

These security headers will affect how browsers handle your frontend applications:

#### Content Security Policy (CSP) Impact
- **Inline Scripts**: `'unsafe-inline'` allows inline JavaScript (development mode)
- **External Resources**: Only allowed from `'self'` and specified domains
- **Images**: Can load from `'self'`, `data:` URLs, and HTTPS sources
- **Fonts**: Only from `'self'` by default

#### Frame Embedding
- **X-Frame-Options: DENY**: Your API responses cannot be embedded in iframes
- **CSP frame-ancestors 'none'**: Reinforces iframe blocking

#### HTTPS Enforcement
- **HSTS**: Browsers will automatically redirect HTTP to HTTPS after first visit
- **Secure Cookies**: Cookies should be marked as `Secure` in production

### 🚨 Common Frontend Issues & Solutions

1. **CSP Violations**: Check browser console for blocked resources
   ```javascript
   // ❌ This might be blocked by CSP
   eval('some code');

   // ✅ Use proper script loading instead
   const script = document.createElement('script');
   script.src = '/path/to/script.js';
   ```

2. **Mixed Content**: Ensure all resources use HTTPS in production
3. **Third-party Integrations**: May need CSP policy updates

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Security Headers Configuration
SECURITY_HEADERS_ENABLED=true
SECURITY_HSTS_ENABLED=true
SECURITY_HSTS_MAX_AGE=31536000
SECURITY_HSTS_INCLUDE_SUBDOMAINS=true
SECURITY_HSTS_PRELOAD=false
SECURITY_CSP_ENABLED=true
SECURITY_CSP_DEFAULT_SRC='self'
SECURITY_CSP_SCRIPT_SRC='self' 'unsafe-inline'
SECURITY_CSP_STYLE_SRC='self' 'unsafe-inline'
SECURITY_CSP_IMG_SRC='self' data: https:
SECURITY_CSP_FONT_SRC='self'
SECURITY_CSP_CONNECT_SRC='self'
SECURITY_CSP_FRAME_ANCESTORS='none'
SECURITY_X_FRAME_OPTIONS=DENY
SECURITY_X_CONTENT_TYPE_OPTIONS=true
SECURITY_X_XSS_PROTECTION=true
SECURITY_REFERRER_POLICY=strict-origin-when-cross-origin
SECURITY_PERMISSIONS_POLICY_ENABLED=true
SECURITY_PERMISSIONS_POLICY=geolocation=(), microphone=(), camera=(), payment=(), usb=()
SECURITY_HIDE_SERVER_HEADER=true
SECURITY_SERVER_HEADER_VALUE=Madcrow-API
```

### Development vs Production

The middleware automatically adjusts based on the `DEPLOY_ENV` setting:

- **Development**: More permissive CSP policies for easier development
- **Production**: Stricter security policies for maximum protection

## 🧪 Testing & Verification

### 1. Quick Test with cURL

Test any endpoint to see security headers in action:

```bash
# Start the application
uv run python main.py

# Test with cURL (shows response headers)
curl -I http://localhost:5001/api/v1/health

# Expected output includes:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'...
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: geolocation=(), microphone=()...
```

### 2. Run the Automated Test Script

```bash
# In another terminal, run the comprehensive test
uv run python test_security_headers.py
```

### 3. Use Built-in Security Endpoints

Test security headers using the built-in endpoints:

```bash
# Get security configuration info
curl http://localhost:5001/api/v1/security/info

# Test headers endpoint (check response headers)
curl -I http://localhost:5001/api/v1/security/headers

# Get security recommendations
curl http://localhost:5001/api/v1/security/recommendations
```

### 4. Browser Developer Tools

1. Open your browser's Developer Tools (F12)
2. Go to Network tab
3. Make a request to any API endpoint
4. Click on the response to see headers
5. Verify security headers are present

### 5. Online Tools

Test your deployed application with these tools:
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)

## 📁 File Structure

```
src/
├── configs/enviornment/security_config.py  # Configuration schema
├── middleware/security_middleware.py       # Middleware implementation
├── extensions/ext_security.py             # Extension integration
└── routes/v1/security.py                  # Security testing endpoints
```

## 🔧 Customization

### Custom CSP Policies

For specific applications, you may need to customize CSP policies:

```python
# Development CSP (more permissive)
SECURITY_CSP_SCRIPT_SRC='self' 'unsafe-inline' 'unsafe-eval'

# Production CSP (strict)
SECURITY_CSP_SCRIPT_SRC='self'
```

### Environment-Specific Configuration

Use different configurations for different environments:

```bash
# Development
SECURITY_CSP_SCRIPT_SRC='self' 'unsafe-inline'

# Production
SECURITY_CSP_SCRIPT_SRC='self'
SECURITY_HSTS_PRELOAD=true
```

## 🚨 Security Recommendations

1. **HTTPS Only**: Always use HTTPS in production
2. **Regular Updates**: Keep dependencies updated
3. **CSP Monitoring**: Monitor CSP violations in production
4. **Testing**: Regularly test security headers
5. **Documentation**: Keep security policies documented

## 🐛 Troubleshooting

### Common Issues

1. **CSP Violations**: Check browser console for CSP errors
2. **HSTS Issues**: Clear browser HSTS cache if needed
3. **Frame Blocking**: Adjust X-Frame-Options for embedding needs

### Debug Mode

Enable debug logging to see security configuration:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📚 References

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN Security Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security)
- [Content Security Policy Guide](https://content-security-policy.com/)
