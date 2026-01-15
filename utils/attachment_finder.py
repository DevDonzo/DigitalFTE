"""Attachment Finder - Search and validate files for email attachments"""
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


def search_attachments(query: str, search_paths: list[Path] = None) -> list[dict]:
    """Search for files matching query in specified paths"""
    if search_paths is None:
        search_paths = [
            Path.home() / 'Downloads',
            Path.home() / 'Desktop'
        ]

    results = []
    query_lower = query.lower()

    for search_path in search_paths:
        if not search_path.exists():
            logger.debug(f"Search path doesn't exist: {search_path}")
            continue

        try:
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    if query_lower in filename.lower():
                        filepath = Path(root) / filename
                        try:
                            results.append({
                                'path': str(filepath),
                                'name': filename,
                                'size_mb': filepath.stat().st_size / (1024 * 1024),
                                'modified': filepath.stat().st_mtime
                            })
                        except OSError:
                            # Skip files we can't stat
                            continue
        except Exception as e:
            logger.warning(f"Error searching {search_path}: {e}")
            continue

    # Sort by modification time, newest first
    return sorted(results, key=lambda x: x['modified'], reverse=True)


def validate_attachment(filepath: str | Path) -> dict:
    """Validate file exists and check size constraints"""
    filepath = Path(filepath)
    warnings = []

    if not filepath.exists():
        return {
            'valid': False,
            'warnings': ['File not found'],
            'size_mb': 0,
            'path': str(filepath)
        }

    try:
        size_mb = filepath.stat().st_size / (1024 * 1024)
    except OSError as e:
        return {
            'valid': False,
            'warnings': [f'Cannot access file: {e}'],
            'size_mb': 0,
            'path': str(filepath)
        }

    # Gmail limit is 25MB per email
    if size_mb > 25:
        return {
            'valid': False,
            'warnings': [f'File exceeds Gmail 25MB limit ({size_mb:.1f}MB)'],
            'size_mb': size_mb,
            'path': str(filepath)
        }
    elif size_mb > 10:
        warnings.append(f'Large file ({size_mb:.1f}MB) - consider compressing')

    return {
        'valid': True,
        'warnings': warnings,
        'size_mb': size_mb,
        'path': str(filepath)
    }


def validate_all_attachments(filepaths: list[str | Path]) -> tuple[list[str], list[dict]]:
    """Validate a list of attachment paths

    Returns:
        (valid_paths, validation_details)
    """
    valid_paths = []
    validation_details = []

    for filepath in filepaths:
        validation = validate_attachment(filepath)
        validation_details.append(validation)

        if validation['valid']:
            valid_paths.append(filepath)

    return valid_paths, validation_details


def get_supported_formats() -> list[str]:
    """Get list of supported attachment file formats"""
    return ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.rtf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.csv']


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
