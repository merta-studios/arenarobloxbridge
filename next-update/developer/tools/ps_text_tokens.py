"""Minimaler PowerShell-Tokenizer: trennt Code, Strings, Here-Strings, Kommentare."""
from __future__ import annotations

QUOTES = ("'", '"')


def segments(src: str):
    """Liefert Liste von (kind, start, end). kind in code/comment/sq/dq/here/hereq."""
    out = []
    i, n = 0, len(src)
    code_start = 0
    while i < n:
        c = src[i]
        # Here-String-Eröffner @' oder @" (Terminator ist immer "Zeilenanfang + Quote + @")
        if c == '@' and i + 1 < n and src[i + 1] in QUOTES:
            prev = src[i - 1] if i > 0 else '\n'
            if not prev.isalnum() and prev not in "@'\"$-":
                if code_start < i:
                    out.append(('code', code_start, i))
                quote = src[i + 1]
                term = "\n" + quote + "@"
                j = i + 2
                k = src.find(term, j)
                if k < 0:
                    k = n - len(term)
                j = k + len(term)
                kind = 'here' if quote == "'" else 'hereq'
                out.append((kind, i, min(j, n)))
                i = min(j, n)
                code_start = i
                continue
        # Blockkommentar <# ... #>
        if c == '<' and i + 1 < n and src[i + 1] == '#':
            if code_start < i:
                out.append(('code', code_start, i))
            j = src.find('#>', i + 2)
            j = n if j < 0 else j + 2
            out.append(('comment', i, j))
            i = j
            code_start = i
            continue
        # Zeilenkommentar
        if c == '#':
            if code_start < i:
                out.append(('code', code_start, i))
            j = src.find('\n', i)
            if j < 0:
                j = n
            out.append(('comment', i, j))
            i = j
            code_start = i
            continue
        # Einfaches Anführungszeichen ('' als Escape)
        if c == "'":
            if code_start < i:
                out.append(('code', code_start, i))
            j = i + 1
            while j < n:
                if src[j] == "'":
                    if j + 1 < n and src[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            out.append(('sq', i, j))
            i = j
            code_start = i
            continue
        # Doppeltes Anführungszeichen (Backtick als Escape)
        if c == '"':
            if code_start < i:
                out.append(('code', code_start, i))
            j = i + 1
            while j < n:
                if src[j] == '`':
                    j += 2
                    continue
                if src[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(('dq', i, j))
            i = j
            code_start = i
            continue
        i += 1
    if code_start < n:
        out.append(('code', code_start, n))
    return out
