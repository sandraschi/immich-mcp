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
    test_dir = Path('test_photos')
    test_dir.mkdir(exist_ok=True)

    if use_real_photos:
        # Copy real photos from user's 1998 collection
        real_photos_dir = Path('E:/Multimedia Files/Photos/1998')

        if real_photos_dir.exists():
            print('Copying real photos from 1998 collection...')
            copied = 0

            for photo_file in real_photos_dir.glob('*'):
                if photo_file.is_file() and photo_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    dest_file = test_dir / photo_file.name
                    if not dest_file.exists():
                        try:
                            import shutil
                            shutil.copy2(photo_file, dest_file)
                            print(f'[COPY] {photo_file.name}')
                            copied += 1
                        except Exception as e:
                            print(f'[ERROR] Failed to copy {photo_file.name}: {e}')
                    else:
                        print(f'[SKIP] {photo_file.name} already exists')
                        copied += 1

            print(f'\nSuccessfully prepared {copied} real photos in {test_dir}/')
            return copied
        else:
            print('[WARN] Real photos directory not found, falling back to placeholders')
            use_real_photos = False

    if not use_real_photos:
        # Sample images from Lorem Picsum (free placeholder images)
        test_images = [
            ('vacation_beach.jpg', 'https://picsum.photos/800/600?random=1'),
            ('mountain_hike.jpg', 'https://picsum.photos/800/600?random=2'),
            ('city_street.jpg', 'https://picsum.photos/800/600?random=3'),
            ('family_dinner.jpg', 'https://picsum.photos/800/600?random=4'),
            ('dog_playing.jpg', 'https://picsum.photos/800/600?random=5'),
            ('sunset_ocean.jpg', 'https://picsum.photos/800/600?random=6'),
            ('birthday_party.jpg', 'https://picsum.photos/800/600?random=7'),
            ('wedding_ceremony.jpg', 'https://picsum.photos/800/600?random=8'),
            ('ski_trip.jpg', 'https://picsum.photos/800/600?random=9'),
            ('cooking_class.jpg', 'https://picsum.photos/800/600?random=10')
        ]

        print('Downloading placeholder test images...')
        downloaded = 0

        for filename, url in test_images:
            filepath = test_dir / filename
            if not filepath.exists():
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        print(f'[OK] Downloaded {filename}')
                        downloaded += 1
                    else:
                        print(f'[FAIL] Failed to download {filename} (status: {response.status_code})')
                except Exception as e:
                    print(f'[ERROR] Error downloading {filename}: {e}')
            else:
                print(f'[SKIP] {filename} already exists')
                downloaded += 1

        print(f'\nSuccessfully prepared {downloaded} placeholder images in {test_dir}/')
        return downloaded

if __name__ == "__main__":
    create_test_images()
