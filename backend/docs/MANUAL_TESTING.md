# Manual Testing Guide for MetPol AI

This document provides step-by-step instructions for manual testing scenarios that cannot be fully automated, particularly focusing on security and production readiness verification.

## 🔒 Database Admin Security Testing

### Prerequisites

- Docker Compose environment running
- Access to terminal/command line
- Web browser

### Test 1: SQLite Web Admin Access Control

**Objective**: Verify that `/db/*` routes are properly secured and only accessible to authorized users.

#### Steps:

1. **Start the application**:

   ```bash
   cd /path/to/METPOL_AI
   docker-compose up -d
   ```

2. **Attempt unauthorized access**:

   - Open browser to `http://localhost:8080/db/`
   - **Expected Result**: Should be prompted for HTTP Basic Auth credentials or receive 401/403 error
   - **❌ FAILURE**: If you can access the database interface without authentication

3. **Verify correct credentials work**:

   ```bash
   # Check the .htpasswd file exists
   docker exec metpol_ai-nginx-1 cat /etc/nginx/.htpasswd
   ```

   - Use the credentials from `.htpasswd` to access `/db/`
   - **Expected Result**: Should gain access to SQLite Web interface
   - **❌ FAILURE**: If valid credentials don't work

4. **Test invalid credentials**:

   - Try accessing `/db/` with wrong username/password
   - **Expected Result**: Access denied
   - **❌ FAILURE**: If invalid credentials grant access

5. **Verify API routes still work**:
   ```bash
   curl http://localhost:8080/api/health
   ```
   - **Expected Result**: `{"status": "healthy"}` response
   - **❌ FAILURE**: If API routes are blocked

#### Security Verification Checklist:

- [ ] `/db/` requires authentication
- [ ] Invalid credentials are rejected
- [ ] Valid credentials allow access
- [ ] API routes (`/api/*`) remain accessible
- [ ] No sensitive information leaked in error messages

### Test 2: Production Environment Security

**Objective**: Verify security measures work correctly in production-like environment.

#### Steps:

1. **Set production environment variables**:

   ```bash
   export ENV=production
   export ADMIN_EMAILS="real-admin@company.com"
   export GOOGLE_CLIENT_ID="your-prod-client-id"
   ```

2. **Test admin access controls**:

   - Use a non-admin Google account to login
   - Attempt to access admin endpoints
   - **Expected Result**: 403 Forbidden for admin endpoints
   - **❌ FAILURE**: If non-admin can access admin functions

3. **Verify CORS settings**:

   ```bash
   curl -H "Origin: https://malicious-site.com" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: X-Requested-With" \
        -X OPTIONS \
        http://localhost:8080/api/ask
   ```

   - **Expected Result**: CORS headers should restrict unauthorized origins
   - **❌ FAILURE**: If any origin is allowed in production

4. **Test rate limiting** (if implemented):
   - Make rapid successive requests to `/api/ask`
   - **Expected Result**: Should hit rate limits and return 429
   - **Note**: This might not be implemented yet

## 🚦 Load Testing Manual Verification

### Test 3: System Performance Under Load

**Objective**: Verify system handles concurrent users and doesn't crash under stress.

#### Setup:

```bash
# Install load testing tools
pip install locust requests

# Start application
docker-compose up -d
```

#### Steps:

1. **Concurrent User Simulation**:

   ```bash
   # Run our load tests
   python -m pytest backend/server/tests/load/test_load.py -v -m slow
   ```

2. **Monitor System Resources**:

   ```bash
   # Monitor Docker containers
   docker stats

   # Check logs for errors
   docker-compose logs -f
   ```

3. **Manual Locust Test** (if Locust is available):

   ```bash
   # Create a simple locustfile
   cat > locustfile.py << 'EOF'
   from locust import HttpUser, task, between

   class WebsiteUser(HttpUser):
       wait_time = between(1, 3)

       @task(3)
       def health_check(self):
           self.client.get("/api/health")

       @task(1)
       def ask_question_unauthorized(self):
           response = self.client.post("/api/ask",
               json={"question": "test"})
           assert response.status_code == 401
   EOF

   # Run load test
   locust --host=http://localhost:8080 --users=10 --spawn-rate=2 -t 60s
   ```

4. **Verify System Recovery**:
   - After load test, check all services are still responsive
   - Test normal user workflows still work
   - **Expected Result**: System should handle load gracefully and recover
   - **❌ FAILURE**: If system becomes unresponsive or crashes

### Performance Expectations:

- [ ] Health checks respond within 100ms
- [ ] System handles 10+ concurrent users
- [ ] No memory leaks during sustained load
- [ ] Error rates remain acceptable (< 1% for valid requests)
- [ ] System recovers properly after load test

## 🔐 Authentication Flow Manual Testing

### Test 4: OAuth Integration

**Objective**: Verify Google OAuth flow works end-to-end in browser.

#### Prerequisites:

- Valid Google OAuth credentials
- Frontend application running

#### Steps:

1. **Test Login Flow**:

   - Navigate to frontend application
   - Click "Login with Google"
   - Complete OAuth flow
   - **Expected Result**: Successful login, user data populated
   - **❌ FAILURE**: OAuth errors, login fails

2. **Test Token Validation**:

   - After login, make API requests from browser
   - Check Network tab for Authorization headers
   - **Expected Result**: Bearer token included in requests
   - **❌ FAILURE**: No auth headers or invalid tokens

3. **Test Token Expiry**:

   - Wait for token to expire (or manipulate token)
   - Make API request
   - **Expected Result**: 401 response, user prompted to re-login
   - **❌ FAILURE**: Expired tokens still accepted

4. **Test Logout**:
   - Click logout button
   - Attempt to make authenticated requests
   - **Expected Result**: Requests fail, user redirected to login
   - **❌ FAILURE**: Can still make authenticated requests after logout

## 🌐 Network Security Testing

### Test 5: HTTPS and SSL/TLS

**Objective**: Verify secure communication in production.

#### Steps (Production Only):

1. **SSL Certificate Validation**:

   ```bash
   # Check SSL certificate
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

   - **Expected Result**: Valid certificate, secure connection
   - **❌ FAILURE**: Invalid certificate, insecure connection

2. **HTTP to HTTPS Redirect**:

   ```bash
   curl -I http://your-domain.com
   ```

   - **Expected Result**: 301/302 redirect to HTTPS
   - **❌ FAILURE**: HTTP connection allowed

3. **Security Headers**:
   ```bash
   curl -I https://your-domain.com
   ```
   - Check for security headers:
     - `Strict-Transport-Security`
     - `X-Content-Type-Options`
     - `X-Frame-Options`
     - `X-XSS-Protection`
   - **Expected Result**: Security headers present
   - **❌ FAILURE**: Missing security headers

## 📊 Monitoring and Logging Verification

### Test 6: Error Logging and Monitoring

**Objective**: Verify errors are properly logged and monitored.

#### Steps:

1. **Generate Test Errors**:

   ```bash
   # Invalid authentication
   curl -X POST http://localhost:8080/api/ask \
        -H "Content-Type: application/json" \
        -d '{"question": "test"}'

   # Invalid JSON
   curl -X POST http://localhost:8080/api/ask \
        -H "Content-Type: application/json" \
        -d 'invalid json'
   ```

2. **Check Log Output**:

   ```bash
   docker-compose logs backend | grep ERROR
   ```

   - **Expected Result**: Errors logged with timestamps, user context
   - **❌ FAILURE**: No error logs or insufficient detail

3. **Verify No Sensitive Data in Logs**:
   - Check logs don't contain passwords, tokens, or personal info
   - **Expected Result**: Sanitized log messages
   - **❌ FAILURE**: Sensitive data in logs

## ✅ Manual Testing Checklist

Before production deployment, verify:

### Security:

- [ ] Database admin interface requires authentication
- [ ] Non-admin users cannot access admin endpoints
- [ ] OAuth flow works correctly
- [ ] CORS properly configured for production
- [ ] HTTPS enforced in production
- [ ] Security headers present
- [ ] Error messages don't leak sensitive information

### Performance:

- [ ] System handles expected concurrent load
- [ ] Response times within acceptable limits
- [ ] No memory leaks under sustained load
- [ ] Graceful degradation under extreme load

### Functionality:

- [ ] All API endpoints respond correctly
- [ ] Database operations work under load
- [ ] File uploads/downloads work (if applicable)
- [ ] Error handling works as expected

### Monitoring:

- [ ] Error logging works properly
- [ ] Performance metrics collected
- [ ] Alerts configured for critical issues
- [ ] Log rotation configured

## 🚨 Troubleshooting Common Issues

### Database Admin Not Protected:

1. Check nginx configuration
2. Verify .htpasswd file exists and is mounted
3. Test nginx config: `nginx -t`
4. Restart nginx service

### OAuth Flow Failing:

1. Verify Google OAuth credentials
2. Check redirect URIs match configuration
3. Inspect browser network tab for errors
4. Verify CORS settings

### Performance Issues:

1. Check database query performance
2. Monitor memory usage
3. Verify connection pooling
4. Check for N+1 query problems

### Rate Limiting Not Working:

1. Verify rate limiting middleware configured
2. Check Redis/memory store for rate limiting
3. Test with multiple IP addresses
4. Verify rate limiting headers in response

---

**Last Updated**: [Date]
**Tested By**: [Name]
**Environment**: [Development/Staging/Production]
