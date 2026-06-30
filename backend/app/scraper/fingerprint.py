"""
app/scraper/fingerprint.py
────────────────────────
Fingerprint randomization using browserforge.
Generates unique browser fingerprints ensuring we don't use the same fingerprint twice consecutively.
"""

from typing import Dict, Any, Optional
from browserforge.fingerprints import FingerprintGenerator

class FingerprintManager:
    """Manages generation of unique browser fingerprints."""
    def __init__(self):
        self._generator = FingerprintGenerator()
        self._last_fingerprint: Optional[Any] = None

    def get_fingerprint(self) -> Any:
        """Generate a new unique fingerprint."""
        # Simple loop to ensure we don't generate the same user agent as last time
        for _ in range(5):
            fp = self._generator.generate(
                browser="chrome", 
                os=("windows", "macos", "linux"),
                strict=False
            )
            
            if not self._last_fingerprint or fp.navigator.userAgent != self._last_fingerprint.navigator.userAgent:
                self._last_fingerprint = fp
                return fp
        
        return self._last_fingerprint or self._generator.generate(browser="chrome")

fingerprint_manager = FingerprintManager()
