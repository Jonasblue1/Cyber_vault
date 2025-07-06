"""
Steganographic Data Backup & Recovery
Covert, resilient data backup for hostile environments.
"""
from PIL import Image
import numpy as np
import io
import json

# LSB encode data into image
def encode_data_to_image(data, image_path='backup.png'):
    # Convert data to binary string
    data_bytes = json.dumps(data).encode('utf-8')
    data_bits = ''.join([bin(byte)[2:].zfill(8) for byte in data_bytes])
    size = int(np.ceil(np.sqrt(len(data_bits) / 3)))
    img = np.zeros((size, size, 3), dtype=np.uint8) + 255
    flat = img.flatten()
    for i, bit in enumerate(data_bits):
        flat[i] = (flat[i] & ~1) | int(bit)
    img = flat.reshape((size, size, 3))
    Image.fromarray(img).save(image_path)
    return image_path

# LSB decode data from image
def decode_data_from_image(image_path):
    img = np.array(Image.open(image_path))
    flat = img.flatten()
    bits = [str(flat[i] & 1) for i in range(len(flat))]
    # Group bits into bytes
    bytes_list = [int(''.join(bits[i:i+8]), 2) for i in range(0, len(bits), 8)]
    # Find null terminator or try to decode
    try:
        data_bytes = bytes(bytes_list)
        return json.loads(data_bytes.decode('utf-8', errors='ignore'))
    except Exception:
        return None

# CLI backup
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python steg.py backup|restore <file> [data]')
        exit(1)
    cmd, file = sys.argv[1], sys.argv[2]
    if cmd == 'backup':
        data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {'test': 'data'}
        encode_data_to_image(data, file)
        print(f'Backup written to {file}')
    elif cmd == 'restore':
        data = decode_data_from_image(file)
        print('Restored data:', data)
