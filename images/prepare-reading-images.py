"""Make temporary, legible reading slices from observed browser asset order.

Input: JSON array on stdin, each with key, directory and ordered files.
No network access; no comic images are written into the research deliverables.
"""
import json
import sys
import os
import tempfile
from pathlib import Path
from PIL import Image

for record in json.load(sys.stdin):
    images = [Image.open(Path(record['directory']) / name).convert('RGB')
              for name in record['files']]
    strip = Image.new('RGB', (max(i.width for i in images),
                             sum(i.height for i in images)), 'white')
    y = 0
    for im in images:
        strip.paste(im, (0, y))
        y += im.height
    key = record['key']
    if not key or Path(key).name != key or key in {'.', '..'}:
        raise ValueError('key must be one directory name')
    destination = Path(os.environ.get('READING_OUTPUT_DIR', str(Path(tempfile.gettempdir()) / 'reading-images'))) / key
    destination.mkdir(parents=True, exist_ok=True)
    slices = []
    for index, y in enumerate(range(0, strip.height, 2200), 1):
        target = destination / f'{index}.jpg'
        strip.crop((0, y, strip.width, min(y + 2300, strip.height))).save(target)
        slices.append(str(target))
    print(json.dumps({'key': record['key'], 'source_images': len(images),
                      'size': strip.size, 'slices': len(slices),
                      'directory': str(destination)}, ensure_ascii=False))
