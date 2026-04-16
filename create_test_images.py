#!/usr/bin/env python3
"""
Download sample test images for Immich MCP testing.
"""

from pathlib import Path

import requests


def create_test_images(use_real_photos=True):
    """Create test photos directory with sample images.

    Args:
        use_real_photos: If True, copy real photos from user's collection.
                        If False, download placeholder images.
    """

    # Create test photos directory
    test_dir = Path("test_photos")
    test_dir.mkdir(exist_ok=True)

    if use_real_photos:
        # Copy real photos from user's 1998 collection
        real_photos_dir = Path("E:/Multimedia Files/Photos/1998")

        if real_photos_dir.exists():
            copied = 0

            for photo_file in real_photos_dir.glob("*"):
                if photo_file.is_file() and photo_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
                    dest_file = test_dir / photo_file.name
                    if not dest_file.exists():
                        try:
                            import shutil

                            shutil.copy2(photo_file, dest_file)
                            copied += 1
                        except Exception:
                            pass
                    else:
                        copied += 1

            return copied
        else:
            use_real_photos = False

    if not use_real_photos:
        # Sample images from Lorem Picsum (free placeholder images)
        test_images = [
            ("vacation_beach.jpg", "https://picsum.photos/800/600?random=1"),
            ("mountain_hike.jpg", "https://picsum.photos/800/600?random=2"),
            ("city_street.jpg", "https://picsum.photos/800/600?random=3"),
            ("family_dinner.jpg", "https://picsum.photos/800/600?random=4"),
            ("dog_playing.jpg", "https://picsum.photos/800/600?random=5"),
            ("sunset_ocean.jpg", "https://picsum.photos/800/600?random=6"),
            ("birthday_party.jpg", "https://picsum.photos/800/600?random=7"),
            ("wedding_ceremony.jpg", "https://picsum.photos/800/600?random=8"),
            ("ski_trip.jpg", "https://picsum.photos/800/600?random=9"),
            ("cooking_class.jpg", "https://picsum.photos/800/600?random=10"),
        ]

        downloaded = 0

        for filename, url in test_images:
            filepath = test_dir / filename
            if not filepath.exists():
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                        downloaded += 1
                    else:
                        pass
                except Exception:
                    pass
            else:
                downloaded += 1

        return downloaded


if __name__ == "__main__":
    create_test_images()
