import os
from dataclasses import dataclass
import hashlib

from config import load_config, get_chunk

@dataclass
class Chunk:
    id: str
    relative_path: str
    start_line: int
    end_line: int
    text: str
    chunk_type: str
    name: str | None
    file_hash: str

def make_chunk_id(relative_path, start_line, text):
    val = "\0".join([relative_path, str(start_line), text])
    encoded=val.encode('utf-8')
    hash_value = hashlib.sha256(encoded).hexdigest()
    return hash_value[0:12]

def _build_chunk(lines, start_line, relative_path, file_hash):
    text = "".join(lines)
    return Chunk(
        id = make_chunk_id(relative_path, start_line, text),
        relative_path = relative_path,
        start_line = start_line,
        end_line = start_line + len(lines) - 1,
        text = text,
        chunk_type = "block",
        name = None,
        file_hash = file_hash,
    )

def chunk_by_size(text, relative_path, file_hash, max_chars, overlap_chars):
    if not text.strip():
        return []

    lines = text.splitlines(keepends=True)
    chunks = []
    current = []
    current_len = 0
    start = 1

    for idx, line in enumerate(lines, start=1):

        # Step 8: a single line longer than max_chars
        if len(line) > max_chars:
            if current:
                chunks.append(_build_chunk(current, start, relative_path, file_hash))

            step = max_chars - overlap_chars
            pos = 0
            while pos < len(line):
                piece = line[pos:pos + max_chars]
                chunks.append(_build_chunk([piece], idx, relative_path, file_hash))
                if pos + max_chars >= len(line):
                    break
                pos += step

            current = []
            current_len = 0
            start = idx + 1
            continue

        # Normal line that would overflow the current chunk
        if current and current_len + len(line) > max_chars:
            chunks.append(_build_chunk(current, start, relative_path, file_hash))

            overlap = []
            overlap_len = 0
            for prev in reversed(current):
                if overlap_len + len(prev) > overlap_chars:
                    break
                overlap.insert(0, prev)
                overlap_len += len(prev)

            if len(overlap) == len(current):
                overlap_len -= len(overlap.pop(0))

            while overlap and overlap_len + len(line) > max_chars:
                overlap_len -= len(overlap.pop(0))

            current = overlap
            current_len = overlap_len
            start = idx - len(overlap)

        current.append(line)
        current_len += len(line)

    if current:
        chunks.append(_build_chunk(current, start, relative_path, file_hash))

    return chunks

def check_chunks(text, chunks, max_chars):
    n_lines = len(text.splitlines(keepends=True))

    # 1. size limit
    for c in chunks:
        assert len(c.text) <= max_chars, f"chunk at line {c.start_line} is too long: {len(c.text)}"

    # 2. coverage: every line number appears in some chunk
    covered = set()
    for c in chunks:
        covered.update(range(c.start_line, c.end_line + 1))
    assert covered == set(range(1, n_lines + 1)), "some lines are not covered"

    # 3. order: start lines never go backward
    starts = [c.start_line for c in chunks]
    assert starts == sorted(starts), "chunks are out of order"

    # 4. unique ids
    ids = [c.id for c in chunks]
    assert len(set(ids)) == len(ids), "duplicate chunk ids"

if __name__ == "__main__":
    from pathlib import Path

    big = "".join(chr(97 + i % 26) for i in range(100))
    sample = "line one\nline two\nline three\nline four\nline five"

    cases = [
        ("sample ov=19", sample, 20, 19),
        ("sample ov=10", sample, 20, 10),
        ("sample ov=8", sample, 20, 8),
        ("sample ov=0", sample, 20, 0),
        ("giant line", big, 40, 10),
        ("normal, giant, normal", "short\n" + big + "\nafter", 40, 10),
        ("exactly max_chars", "y" * 40, 40, 10),
    ]

    for name, text, mx, ov in cases:
        first = chunk_by_size(text, "t.py", "h", mx, ov)
        second = chunk_by_size(text, "t.py", "h", mx, ov)
        check_chunks(text, first, mx)
        assert [c.id for c in first] == [c.id for c in second], "ids not deterministic"
        print("OK  ", name, "->", [(c.start_line, c.end_line) for c in first])

    assert chunk_by_size("", "t.py", "h", 20, 8) == []
    assert chunk_by_size("  \n ", "t.py", "h", 20, 8) == []
    print("OK   empty text")

    real = Path(__file__).with_name("scanner.py")
    if real.exists():
        src = real.read_text(encoding="utf-8")
        result = chunk_by_size(src, "scanner.py", "h", 1500, 100)
        check_chunks(src, result, 1500)
        for c in result:
            print("  ", c.start_line, c.end_line, len(c.text))
        print("OK   real file")
