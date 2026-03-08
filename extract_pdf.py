import sys
import subprocess

try:
    import pypdf
except ImportError:
    subprocess.run([sys.executable, -m, pip, install, pypdf, --break-system-packages], check=True)
    import pypdf

reader = pypdf.PdfReader(TEKNOFEST26_Savasan_IHA_TYF_TR_zMqMG.pdf)
text = "
for
