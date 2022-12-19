from typing import Optional, Union
from pathlib import Path
import tempfile
import uuid


def get_path(folder: Optional[Union[str, Path]] = None, path: Optional[Union[str, Path]] = None) -> Path:
    if not path and not folder:
        folder = Path(tempfile.gettempdir())
    folder = Path(folder or '')
    folder.mkdir(parents=True, exist_ok=True)
    path = Path(path or str(uuid.uuid4()))
    return folder / path


def save(lines, folder=None, path=None) -> Path:
    p = get_path(folder, path)
    with open(p, 'w') as f:
        for line in lines:
            f.write(f'{line}\n')
    return p
