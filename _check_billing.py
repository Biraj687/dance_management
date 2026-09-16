from pathlib import Path

t = Path('d:/projects/dance management/billing/views.py').read_text('utf-8')
lines = t.split('\n')
for i, l in enumerate(lines):
    if any(k in l for k in ['def export', 'def _', 'issued_date', 'def _csv', 'def _invoice', 'paid_on']):
        print(f"{i+1:3}: {l}")