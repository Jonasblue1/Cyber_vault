@echo off
REM Generate self-signed TLS certificate for CyberVault (Windows)
IF NOT EXIST cert.pem (
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
    ECHO Self-signed TLS certificate generated.
) ELSE (
    ECHO TLS certificate already exists.
)
