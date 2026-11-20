"""ROMs and the facts measured on them (shared by every tool).

The French version is built on top of the English fan translation v0.9 (Loic / JinRawX, 2018),
because that patch already moved the whole script out of the Japanese code. The tools rebuild it
in memory: Japanese ROM + the original English IPS -> English ROM -> French ROM.

Measured facts (19/11/2026):
- The English script sits at file 0x100000..0x127D10, messages ended by FF. Free space until
  0x1F8000 (0x1F8000.. = save area).
- Events point at messages with `A0 lo hi 3x 00` (CPU 0x30xxxx = file 0x10xxxx), battle texts with
  `44 lo hi 30 00`, the credits with `f2 lo hi 32`. A pointer is kept when it was rewritten by the
  English patch, points at a message start, replaces a Japanese pointer to 0x20..0x2Fxxxx, and is
  not the one-byte-shifted reading of a real pointer.
- Messages that nothing points at belong to lists read BY NUMBER (items, moods, biographies,
  credits): the order and the number of messages must never change.
"""
import hashlib
import zlib
from pathlib import Path

# Expected Japanese ROM (No-Intro "Nigeronpa (Japan)")
JP_SIZE = 1048576
JP_CRC = 0x3CC3E269
JP_SHA1 = 'b5d355ea808dd01cf746daef7704e54d7766bd3b'
# English ROM obtained with the English patch v0.9 (nigeronpa_en_0.9.ips)
EN_CRC = 0x6672D6E6

TEXT_START = 0x100000
TEXT_END = 0x127D10       # first byte after the last FF of the English script
FREE_END = 0x1F8000       # 0x1F8000.. = save area (flash), never touched
CPU_BASE = 0x200000


def ips_apply(src: bytes, patch: bytes) -> bytes:
    """Standard IPS (PATCH ... EOF [3-byte truncation]); the file grows when a record goes past its end."""
    if not patch.startswith(b'PATCH'):
        raise SystemExit('not an IPS file')
    out = bytearray(src)
    i = 5
    while patch[i:i + 3] != b'EOF':
        off = int.from_bytes(patch[i:i + 3], 'big')
        n = int.from_bytes(patch[i + 3:i + 5], 'big')
        i += 5
        if n == 0:
            run = int.from_bytes(patch[i:i + 2], 'big')
            data = bytes([patch[i + 2]]) * run
            i += 3
        else:
            data = patch[i:i + n]
            i += n
        if len(out) < off + len(data):
            out += b'\x00' * (off + len(data) - len(out))
        out[off:off + len(data)] = data
    tail = patch[i + 3:i + 6]
    if len(tail) == 3:
        del out[int.from_bytes(tail, 'big'):]
    return bytes(out)


def load_jp(path):
    jp = Path(path).read_bytes()
    if len(jp) != JP_SIZE or zlib.crc32(jp) != JP_CRC or hashlib.sha1(jp).hexdigest() != JP_SHA1:
        raise SystemExit('%s is not the expected Japanese ROM (size %d, CRC32 %08X): see README'
                         % (path, len(jp), zlib.crc32(jp)))
    return jp


def load(jp_path, en_ips_path):
    """(Japanese ROM, English ROM) - the English one rebuilt from the official English IPS."""
    jp = load_jp(jp_path)
    en = ips_apply(jp, Path(en_ips_path).read_bytes())
    if zlib.crc32(en) != EN_CRC:
        raise SystemExit('%s is not the English patch v0.9 (result CRC32 %08X, expected %08X)'
                         % (en_ips_path, zlib.crc32(en), EN_CRC))
    return jp, en


def messages(en: bytes):
    """[(start, end_without_FF)] in order."""
    out, s = [], TEXT_START
    for i in range(TEXT_START, TEXT_END):
        if en[i] == 0xFF:
            out.append((s, i))
            s = i + 1
    assert s == TEXT_END, hex(s)
    return out


def pointers(jp: bytes, en: bytes):
    """[(file position of the 3-byte pointer, target)]"""
    out = []
    for i in range(0, 0x100000 - 3):
        hi = en[i + 2]
        if hi not in (0x30, 0x31, 0x32) or en[i:i + 3] == jp[i:i + 3]:
            continue
        tgt = (hi - 0x20) << 16 | en[i + 1] << 8 | en[i]
        if not (TEXT_START <= tgt < TEXT_END):
            continue
        if tgt != TEXT_START and en[tgt - 1] != 0xFF:
            continue
        if not (0x20 <= jp[i + 2] <= 0x2F):
            continue
        out.append((i, tgt))
    pos = {i for i, _ in out}
    return [(i, t) for i, t in out if i + 1 not in pos]
