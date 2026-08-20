"""Annotation applier for claude_reference/bankC1.txt.

Directive file format (one directive per stanza, blank-line separated):

  C <ADDR> <text>      set the comment on the instruction line at C1/ADDR
                       (replaces an existing trailing comment only if the
                       line has none; use C! to overwrite)
  C! <ADDR> <text>     overwrite the comment on the line at C1/ADDR
  H <ADDR>             insert the following indented lines (until the next
  <tab>text            blank line) as a header block immediately before the
  <tab>text            line for C1/ADDR, preceded/followed by blank lines

The applier never alters the address / byte / mnemonic fields; it appends
comments after the mnemonic column in the file's own style.  Every ADDR must
match exactly one 'C1/ADDR:' line or the run aborts.
"""
import re
import sys

REF = 'claude_reference/bankC1.txt'


def load(path=REF):
    return open(path, encoding='latin-1').read().splitlines()


def save(lines, path=REF):
    open(path, 'w', encoding='latin-1', newline='\n').write('\n'.join(lines) + '\n')


def index(lines):
    idx = {}
    pat = re.compile(r'^C1/([0-9A-F]{4}):')
    for i, l in enumerate(lines):
        m = pat.match(l)
        if m:
            idx.setdefault(m.group(1), []).append(i)
    return idx


def set_comment(lines, idx, addr, text, force=False):
    import re as _re
    hits = idx.get(addr, [])
    if len(hits) != 1:
        raise SystemExit(f'{addr}: {len(hits)} matches')
    i = hits[0]
    line = lines[i]
    parts = line.split('\t')
    # fields: 'C1/xxxx:', bytes, mnemonic, [comment...]
    if len(parts) < 3:
        raise SystemExit(f'{addr}: unexpected format: {line!r}')
    text = text.strip()
    if text.startswith('(') and text.endswith(')'):
        text = text[1:-1]
    field = parts[2]
    if field.lstrip().startswith('('):
        # data line whose third field is itself a comment: C! replaces it
        if not force:
            raise SystemExit(f'{addr}: already commented: {line!r}')
        lines[i] = f'{parts[0]}\t{parts[1]}\t({text})'
        return
    mnem = _re.match(r'^([^(]*)', field).group(1).rstrip()
    existing = field[len(_re.match(r'^([^(]*)', field).group(1)):].strip()
    if len(parts) > 3:
        tail = ' '.join(p.strip() for p in parts[3:] if p.strip())
        existing = (existing + ' ' + tail).strip() if existing else tail
    # a bare caller note "(from ...)" is kept and merged with the new text
    from_note = ''
    m = _re.match(r'^(\(from [^)]*\))\s*(.*)$', existing)
    if m:
        from_note, rest = m.group(1), m.group(2)
    else:
        rest = existing
    if rest and not force:
        raise SystemExit(f'{addr}: already commented: {line!r}')
    pieces = [p for p in (f'({text})', from_note) if p]
    body = '\t'.join(parts[:2] + [mnem]).rstrip()
    lines[i] = f'{body}\t\t' + ' '.join(pieces)


def insert_header(lines, idx, addr, header_lines):
    hits = idx.get(addr, [])
    if len(hits) != 1:
        raise SystemExit(f'H {addr}: {len(hits)} matches')
    i = hits[0]
    block = []
    # ensure a blank line before the header unless one is already there
    if i > 0 and lines[i - 1].strip():
        block.append('')
    block.extend(header_lines)
    lines[i:i] = block


def apply(directive_path, path=REF):
    lines = load(path)
    idx = index(lines)
    src = open(directive_path, encoding='utf-8').read().splitlines()
    pending_headers = []   # (addr, [lines]) applied last, bottom-up
    comments = []
    i = 0
    while i < len(src):
        l = src[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith('C! '):
            _, addr, text = l.split(' ', 2)
            comments.append((addr.upper(), text, True))
        elif l.startswith('C '):
            _, addr, text = l.split(' ', 2)
            comments.append((addr.upper(), text, False))
        elif l.startswith('H '):
            addr = l.split()[1].upper()
            i += 1
            hl = []
            while i < len(src) and src[i].startswith('\t'):
                hl.append(src[i][1:])
                i += 1
            pending_headers.append((addr, hl))
            continue
        else:
            raise SystemExit(f'bad directive: {l!r}')
        i += 1

    for addr, text, force in comments:
        set_comment(lines, idx, addr, text, force)

    # insert headers bottom-up so earlier insertions don't shift later ones
    order = sorted(pending_headers,
                   key=lambda h: idx[h[0]][0], reverse=True)
    for addr, hl in order:
        insert_header(lines, idx, addr, hl)

    save(lines, path)
    print(f'applied {len(comments)} comments, {len(pending_headers)} headers')


def verify_instructions_unchanged(before, after):
    pat = re.compile(r'^(C1/[0-9A-F]{4}:\t[^\t]*\t[^\t(]*)')
    def core(ls):
        out = []
        for l in ls:
            m = pat.match(l)
            if m:
                out.append(m.group(1).rstrip())
        return out
    a, b = core(before), core(after)
    assert a == b, 'instruction fields changed!'
    print(f'verified: {len(a)} instruction lines unchanged')


if __name__ == '__main__':
    if sys.argv[1] == 'apply':
        apply(sys.argv[2])
    elif sys.argv[1] == 'check':
        verify_instructions_unchanged(load(sys.argv[2]), load(REF))
