"""
app/sentiment/wordcloud_generator.py
─────────────────────────────────────
Generates word clouds for positive, negative, and neutral sentiments.
Saves PNG files into 'backend/static/wordclouds/'.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional
import matplotlib
# Use non-interactive backend for server-friendly plotting (prevents Tkinter errors)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from app.utils.logger import logger

# ── Ensure output directory exists ───────────────────────────────────────────
STATIC_DIR = Path("static/wordclouds")
os.makedirs(STATIC_DIR, exist_ok=True)


class WordCloudGenerator:
    """
    Generates word cloud visualization PNGs for different sentiments.
    """

    def __init__(self, output_dir: Path = STATIC_DIR) -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug("WordCloudGenerator output directory: {path}", path=self.output_dir.absolute())

    def _generate_cloud(
        self,
        word_freqs: Dict[str, int],
        filename: str,
        color_map: str,
        title: str
    ) -> Optional[str]:
        """
        Helper method to generate a single word cloud from frequencies.
        """
        if not word_freqs:
            logger.debug("No words available for word cloud '{title}'; skipping generation", title=title)
            return None

        filepath = self.output_dir / filename

        try:
            # Create WordCloud
            wc = WordCloud(
                width=800,
                height=400,
                background_color="black",
                colormap=color_map,
                max_words=100,
                contour_width=2,
                contour_color="steelblue",
            )

            wc.generate_from_frequencies(word_freqs)

            # Draw using matplotlib
            plt.figure(figsize=(10, 5), facecolor="k")
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            plt.tight_layout(pad=0)

            # Save PNG
            plt.savefig(filepath, format="png", facecolor="k", bbox_inches="tight")
            plt.close()
            
            logger.info("Saved word cloud image to {path}", path=filepath.absolute())
            return str(filepath)

        except Exception as exc:
            logger.error("Error generating word cloud for '{title}': {exc}", title=title, exc=exc)
            return None

    def generate_all_clouds(
        self,
        positive_freqs: Dict[str, int],
        negative_freqs: Dict[str, int],
        neutral_freqs: Dict[str, int],
        product_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate positive, negative, and neutral word cloud PNGs.
        Optionally uses product_id to namespace the filenames.

        Returns:
            dict mapping sentiment label → relative file path of the image.
        """
        suffix = f"_{product_id}" if product_id else ""
        
        pos_file = f"positive{suffix}.png"
        neg_file = f"negative{suffix}.png"
        neu_file = f"neutral{suffix}.png"

        results = {}

        # Colors: Greenish for positive, Reddish for negative, Bluish/Greyish for neutral
        pos_path = self._generate_cloud(positive_freqs, pos_file, "Greens", "Positive Sentiment")
        if pos_path:
            results["positive"] = pos_path

        neg_path = self._generate_cloud(negative_freqs, neg_file, "Reds", "Negative Sentiment")
        if neg_path:
            results["negative"] = neg_path

        neu_path = self._generate_cloud(neutral_freqs, neu_file, "Blues", "Neutral Sentiment")
        if neu_path:
            results["neutral"] = neu_path

        return results
