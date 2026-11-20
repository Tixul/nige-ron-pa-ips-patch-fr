"""IPS patch: create and apply (standard "PATCH" ... "EOF" format).

    python tools/ips.py make  ORIGINAL.ngc TRANSLATED.ngc patch.ips
    python tools/ips.py apply ORIGINAL.ngc patch.ips      OUTPUT.ngc

The patch only holds modified bytes (no range of original bytes is copied into it).
The translated ROM may be LARGER than the original (Nige-Ron-Pa: 1 MiB -> 2 MiB): the extra part
is written ENTIRELY as records past the end of the original file: patchers grow the file but do
not agree on the filler (Flips/Lunar IPS use 00, NgpCraft Emulator uses FF), so no byte of the
extension is left to chance. Long runs of one byte are stored as RLE records.
"""
import sys
sys.dont_write_bytecode = True   # no __pycache__

MAX = 0xFFFF
RLE_MIN = 16                     # a run of at least this many identical bytes becomes an RLE record


def _run(dst, i, end):
    j = i
    while j < end and dst[j] == dst[i] and j - i < MAX:
        j += 1
    return j - i


def make(src, dst):
    if len(dst) < len(src):
        raise SystemExit('the translated ROM is smaller than the original: not supported')
    m = len(src)

    def same(k):                       # the extension (k >= m) is always written
        return k < m and src[k] == dst[k]

    out = bytearray(b'PATCH')
    i, n = 0, len(dst)
    while i < n:
        if same(i):
            i += 1
            continue
        if i == 0x454F46:                      # offset "EOF": ambiguous in IPS
            i -= 1                             # start one byte earlier (that byte is rewritten as is)
        if i > 0xFFFFFF:
            raise SystemExit('ROM too large for IPS')
        r = _run(dst, i, n)
        if r >= RLE_MIN:
            out += i.to_bytes(3, 'big') + b'\x00\x00' + r.to_bytes(2, 'big') + dst[i:i + 1]
            i += r
            continue
        j = i
        while j < n and j - i < MAX and not same(j):
            if _run(dst, j, n) >= RLE_MIN:
                break
            j += 1
        if j == i:
            j = i + 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + dst[i:j]
        i = j
    out += b'EOF'
    return bytes(out)


def apply(src, patch):
    if patch[:5] != b'PATCH':
        raise SystemExit('not an IPS patch')
    rom, p = bytearray(src), 5
    while patch[p:p + 3] != b'EOF':
        off = int.from_bytes(patch[p:p + 3], 'big')
        size = int.from_bytes(patch[p + 3:p + 5], 'big')
        p += 5
        if size:
            data = patch[p:p + size]
            p += size
        else:                                  # RLE record
            count = int.from_bytes(patch[p:p + 2], 'big')
            data = patch[p + 2:p + 3] * count
            p += 3
        if off + len(data) > len(rom):
            rom += b'\x00' * (off + len(data) - len(rom))
        rom[off:off + len(data)] = data
    return bytes(rom)


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ('make', 'apply'):
        raise SystemExit(__doc__)
    if sys.argv[1] == 'make':
        data = make(open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read())
    else:
        data = apply(open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read())
    open(sys.argv[4], 'wb').write(data)
    print(sys.argv[4], len(data), 'bytes')


if __name__ == '__main__':
    main()
