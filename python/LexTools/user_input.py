from pathlib import Path
import time
import logging
import shutil

log = logging.getLogger(__name__)

def require_empty_dir(
    path: Path, 
    parents: bool = False,
    overwrite: bool = False,
) -> None:
    # Make directory if it doesn't exist or is empty
    if not path.is_dir():
        path.mkdir(parents=parents)
        return
    elif not any(path.iterdir()):
        return

    if not overwrite:
        # Check if user wants to delete contents of directory
        overwrite = request_permission(f'Delete contents of {path}?')

    files = list(path.iterdir())
    if overwrite:
        log.info('Deleting all %d files from %s', len(files), path)
        time.sleep(2) # Give the user a moment to realize if this was a mistake
        shutil.rmtree(path)
    else:
        raise FileExistsError(
            f'{len(files)} files found (e.g. {files[0].name}): {path}'
        )

import concurrent.futures
import threading
def request_permission(prompt: str) -> bool:
    # Not working
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    #     fn = lambda : input(f'{prompt} [y,n] ') 
    #     future = executor.submit(fn)
    #     try:
    #         result = future.result(timeout=2) == 'y'
    #     except TimeoutError:
    #         print('Ran out of time')
    
    result = 'n'
    def fn():
        nonlocal result
        result = input(f'{prompt} [y,n] ')
    input_thread = threading.Thread(target=fn)
    print('Submitting thread')
    input_thread.start()
    input_thread.join(timeout=2)
    result = result == 'y'

    return result



if __name__ == '__main__':
    import pytest
    empty_dir = Path('path_to/empty_dir')

    assert not empty_dir.parent.is_dir()

    # Error if parent directory does not exist
    with pytest.raises(FileNotFoundError):
        require_empty_dir(empty_dir)

    # Create directory if it does not exist
    empty_dir.parent.mkdir()
    assert not empty_dir.is_dir()
    require_empty_dir(empty_dir)
    assert empty_dir.is_dir()
    
    # Do nothing if directory exists but is empty
    require_empty_dir(empty_dir)
    assert empty_dir.is_dir()

    # Error if directory exists and is not empty
    (empty_dir/'file.txt').write_text('TEST\n')
    with pytest.raises(FileExistsError):
        require_empty_dir(empty_dir)

    shutil.rmtree(empty_dir.parent)
    print('Tests Passed')
