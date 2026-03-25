"""Generate a minimal valid PDF for testing."""
import struct

pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
4 0 obj<</Length 137>>stream
BT /F1 12 Tf 72 720 Td (Acme Corp Annual Report 2023) Tj 0 -20 Td (Revenue: 45.2 billion) Tj 0 -20 Td (Net Income: 8.7 billion) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000306 00000 n 
0000000240 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
495
%%EOF"""

import os, sys
out = os.path.join(os.path.dirname(__file__), "..", "backend", "tests", "fixtures", "sample.pdf")
out = os.path.abspath(out)
with open(out, "wb") as f:
    f.write(pdf_content)
print(f"Written to {out}")
