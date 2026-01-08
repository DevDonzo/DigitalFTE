"""FileSystem Watcher - Monitor drop folder"""
import os
import logging
from pathlib import Path
from datetime import datetime
import shutil

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: pip install watchdog")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, watch_folder: str):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'
        self.watch_folder = Path(watch_folder)
        
    def on_created(self, event):
        if event.is_directory:
            return
        
        try:
            source = Path(event.src_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = self.inbox / f"FILE_{source.stem}_{timestamp}{source.suffix}"
            
            # Copy file
            shutil.copy2(source, dest)
            
            # Create metadata
            meta = f"""---
type: file_drop
original_name: {source.name}
size_bytes: {source.stat().st_size}
extension: {source.suffix}
received: {datetime.now().isoformat()}
---

New file dropped: {source.name}
"""
            meta_file = dest.with_suffix('.md')
            meta_file.write_text(meta)
            
            logger.info(f"Processed: {source.name} → {dest.name}")
        except Exception as e:
            logger.error(f"Drop folder error: {e}")

if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    watch_folder = os.getenv('WATCH_FOLDER', str(Path.home() / 'Downloads'))
    
    if not Path(watch_folder).exists():
        print(f"ERROR: Watch folder {watch_folder} doesn't exist")
        exit(1)
    
    handler = DropFolderHandler(vault_path, watch_folder)
    observer = Observer()
    observer.schedule(handler, watch_folder, recursive=False)
    observer.start()
    
    logger.info(f"Watching: {watch_folder}")
    try:
        while True:
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
