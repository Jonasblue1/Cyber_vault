"""
Script to generate self-signed TLS 1.3 certificates for local HTTPS
"""
import subprocess

def generate_cert(cert_file='cert.pem', key_file='key.pem'):
    subprocess.run([
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', key_file,
        '-out', cert_file, '-days', '365', '-nodes', '-subj', '/CN=localhost'
    ])

if __name__ == '__main__':
    generate_cert()
    print('Self-signed TLS certificate generated.')
