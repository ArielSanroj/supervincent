# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within SuperVincent InvoiceBot, please report it responsibly:

### How to Report

1. **DO NOT** create a public GitHub issue
2. Email security details to: security@supervincent.com
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- We will acknowledge receipt within 48 hours
- We will provide regular updates on our progress
- We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Measures

### Data Protection
- All invoice data is encrypted at rest
- API credentials are stored securely using environment variables
- No sensitive data is logged

### Input Validation
- File upload size limits (10MB max)
- MIME type validation for uploaded files
- Path traversal protection
- SQL injection prevention

### API Security
- Rate limiting implemented
- API key rotation support
- HTTPS enforcement
- Request/response validation

### Dependencies
- Regular security updates
- Automated vulnerability scanning
- Pinned dependency versions

## Security Best Practices

### For Users
1. Keep your API credentials secure
2. Use strong, unique passwords
3. Regularly update the application
4. Monitor access logs
5. Use HTTPS in production

### For Developers
1. Follow secure coding practices
2. Validate all inputs
3. Use parameterized queries
4. Implement proper error handling
5. Keep dependencies updated

## Known Security Considerations

### OCR Processing
- Tesseract OCR processes images locally
- No image data is sent to external services
- Temporary files are cleaned up after processing

### API Integration
- Alegra API credentials are required
- All API calls use HTTPS
- Rate limiting is respected

### File Processing
- PDFs and images are processed locally
- No files are sent to external services
- Temporary files are automatically cleaned up

## Security Updates

We regularly update dependencies and security measures. To stay informed:

1. Watch this repository for security releases
2. Subscribe to our security mailing list
3. Follow our security blog

## Contact

For security-related questions or concerns:
- Email: security@supervincent.com
- PGP Key: [Available on request]

## Acknowledgments

We thank the security researchers who help us keep SuperVincent InvoiceBot secure.
