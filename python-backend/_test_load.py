"""Find where chatbot.py stops executing."""
import sys
sys.path.insert(0, '.')

lines = open('routes/chatbot.py', encoding='utf-8-sig').readlines()
total = len(lines)
print(f"Total lines: {total}")

# Try executing chunks
ns = {}
chunks = [100, 200, 250, 260, 270, 280, 300, 400, 500, total]
for end in chunks:
    content = ''.join(lines[:end])
    try:
        code = compile(content, 'chatbot.py', 'exec')
        exec(code, ns)
        has_di = 'detect_intent' in ns
        has_cp = '_COMPLEX_PATTERNS' in ns
        print(f"Lines 1-{end}: OK  detect_intent={has_di}  _COMPLEX_PATTERNS={has_cp}")
        if has_di:
            result = ns['detect_intent']('How do I convince a healthcare CIO to switch from MPLS to SD-WAN?')
            print(f"  -> detect_intent result: {result}")
            break
    except SyntaxError as e:
        print(f"Lines 1-{end}: SyntaxError at line {e.lineno}: {e.msg}")
    except Exception as e:
        print(f"Lines 1-{end}: {type(e).__name__}: {e}")
