import os

# File signatures for TXT and XLSX
# TXT is tricky since it doesn't have a strong header, we look for readable ascii sequences
# XLSX files are actually ZIP files with signature: 50 4B 03 04 (PK..)

FILE_SIGNATURES = {
    b'\x50\x4B\x03\x04': '.xlsx',  # ZIP signature for XLSX files
}

OUTPUT_DIR = 'RecoveredFiles'
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def is_printable_ascii(byte_seq):
    return all(32 <= b <= 126 or b in (9, 10, 13) for b in byte_seq)

def recover_files_from_disk(drive_letter='Z'):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    drive_path = r'\\.\{}:'.format(drive_letter)  # Raw disk path on Windows

    with open(drive_path, 'rb') as disk:
        buffer = b''
        file_count = {ext:0 for ext in FILE_SIGNATURES.values()}
        txt_file_count = 0

        while True:
            chunk = disk.read(CHUNK_SIZE)
            if not chunk:
                break

            buffer += chunk

            # Look for XLSX/ZIP files by signature
            for sig, ext in FILE_SIGNATURES.items():
                start = buffer.find(sig)
                while start != -1:
                    # Try to extract a chunk (let's assume max 10 MB per file to avoid huge files)
                    end = buffer.find(b'\x50\x4B\x05\x06', start)  # ZIP End of central directory signature
                    if end == -1:
                        end = start + 10 * 1024 * 1024  # 10MB max
                    else:
                        end += 22  # size of end of central directory record

                    file_data = buffer[start:end]
                    if file_data.startswith(sig):
                        file_count[ext] += 1
                        filename = os.path.join(OUTPUT_DIR, f'recovered_{file_count[ext]}{ext}')
                        with open(filename, 'wb') as f_out:
                            f_out.write(file_data)
                        print(f'Recovered {filename}')
                    # Remove extracted part from buffer
                    buffer = buffer[end:]
                    start = buffer.find(sig)

            # Extract readable ascii chunks for txt recovery
            # Simple approach: extract sequences of printable ascii chars >= 100 bytes
            ascii_start = None
            for i, b in enumerate(buffer):
                if 32 <= b <= 126 or b in (9,10,13):
                    if ascii_start is None:
                        ascii_start = i
                else:
                    if ascii_start is not None and i - ascii_start >= 100:
                        txt_file_count += 1
                        filename = os.path.join(OUTPUT_DIR, f'recovered_{txt_file_count}.txt')
                        with open(filename, 'wb') as f_out:
                            f_out.write(buffer[ascii_start:i])
                        print(f'Recovered {filename}')
                    ascii_start = None

            # Keep last few bytes in buffer in case file spans chunks
            if len(buffer) > CHUNK_SIZE:
                buffer = buffer[-CHUNK_SIZE:]

if __name__ == "__main__":
    print("Starting recovery from drive Z:")
    recover_files_from_disk('Z')
    print("Done!")



