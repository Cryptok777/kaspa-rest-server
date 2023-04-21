charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def from_hex(hex_str):
    arr = []
    for n in range(0, len(hex_str), 2):
        arr.append(int(hex_str[n:n+2], 16))
    return arr

def to_words(data):
    value = 0
    bits = 0
    max_v = (1 << 5) - 1
    result = []
    for i in range(len(data)):
        value = (value << 8) | data[i]
        bits += 8
        while bits >= 5:
            bits -= 5
            result.append((value >> bits) & max_v)
    if bits > 0:
        result.append((value << (5 - bits)) & max_v)
    return result

def polymod(values):
    c = 1
    for d in values:
        c0 = c >> 35
        c = ((c & 0x07FFFFFFFF) << 5) ^ d
        if c0 & 0x01:
            c ^= 0x98F2BC8E61
        if c0 & 0x02:
            c ^= 0x79B76D99E2
        if c0 & 0x04:
            c ^= 0xF33E5FB3C4
        if c0 & 0x08:
            c ^= 0xAE2EABE2A8
        if c0 & 0x10:
            c ^= 0x1E4F43E470
    return c ^ 1

def encode_address(prefix, payload, version):
    data = [version] + payload

    address = to_words(data)
    checksum_num = polymod(
        [
            *(ord(c) & 0x1F for c in prefix),
            0,
            *address,
            0, 0, 0, 0, 0, 0, 0, 0
        ]
    )
    checksum = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(8):
        checksum[7 - i] = (checksum_num >> (5 * i)) & 0x1F
    return prefix + ":" + "".join(charset[c] for c in address + checksum)

def parse_payload(payload):
    if payload is None:
        return ["", ""]

    buffer = from_hex(payload)
    version = buffer[16]
    length = buffer[18]
    script = buffer[19:19 + length]
    if script[0] == 0xAA:
        version = 8
        script = script[1:]
    if script[0] < 0x76:
        address_size = script[0]
        address = script[1:address_size + 1]
        return [encode_address("kaspa", address, version), "".join(chr(c) for c in buffer[19 + length:])]
    return [payload, ""]