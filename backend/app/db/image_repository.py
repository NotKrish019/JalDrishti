"""SQLite-based durable metadata repository for JalDrishti inspection imagery.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Minimal, robust, zero-daemon persistence adhering to project constraints.
Persists application-level identifiers, Cloudinary public/asset IDs,
dimensions, status, timestamps, and inspection associations.
"""

import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.schemas.image import ImageMetadata

logger = logging.getLogger(__name__)


class MetadataPersistenceError(Exception):
    """Raised when image metadata cannot be durably written or retrieved."""
    pass


class ImageRepository:
    """Thread-safe SQLite repository managing image metadata persistence."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Establish a SQLite connection with row factory enabled."""
        if self.db_path != ":memory:":
            path = Path(self.db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create necessary tables and indices if not already present."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS image_metadata (
                        image_id TEXT PRIMARY KEY,
                        inspection_id TEXT,
                        public_id TEXT NOT NULL,
                        asset_id TEXT,
                        resource_type TEXT NOT NULL DEFAULT 'image',
                        format TEXT NOT NULL,
                        width INTEGER NOT NULL,
                        height INTEGER NOT NULL,
                        bytes INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'uploaded',
                        structure_type TEXT,
                        original_filename TEXT,
                        preview_url TEXT NOT NULL,
                        secure_url TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_image_inspection 
                    ON image_metadata(inspection_id);
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_image_public_id 
                    ON image_metadata(public_id);
                    """
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to initialize SQLite database at %s: %s", self.db_path, e)
            raise MetadataPersistenceError(f"Database initialization failed: {e}") from e

    def save(self, metadata: ImageMetadata) -> ImageMetadata:
        """Durably persist or update an image metadata record.

        Args:
            metadata: ImageMetadata instance to store.

        Returns:
            ImageMetadata: The persisted record.

        Raises:
            MetadataPersistenceError: If the record could not be written.
        """
        sql = """
        INSERT INTO image_metadata (
            image_id, inspection_id, public_id, asset_id, resource_type,
            format, width, height, bytes, created_at, status,
            structure_type, original_filename, preview_url, secure_url
        ) VALUES (
            :image_id, :inspection_id, :public_id, :asset_id, :resource_type,
            :format, :width, :height, :bytes, :created_at, :status,
            :structure_type, :original_filename, :preview_url, :secure_url
        )
        ON CONFLICT(image_id) DO UPDATE SET
            inspection_id = excluded.inspection_id,
            public_id = excluded.public_id,
            asset_id = excluded.asset_id,
            resource_type = excluded.resource_type,
            format = excluded.format,
            width = excluded.width,
            height = excluded.height,
            bytes = excluded.bytes,
            created_at = excluded.created_at,
            status = excluded.status,
            structure_type = excluded.structure_type,
            original_filename = excluded.original_filename,
            preview_url = excluded.preview_url,
            secure_url = excluded.secure_url;
        """
        try:
            with self._get_connection() as conn:
                conn.execute(sql, metadata.model_dump())
                conn.commit()
            return metadata
        except sqlite3.Error as e:
            logger.error("Failed to persist image metadata for image_id %s: %s", metadata.image_id, e)
            raise MetadataPersistenceError(f"Metadata persistence failed: {e}") from e

    def get_by_id(self, image_id: str) -> Optional[ImageMetadata]:
        """Retrieve image metadata by its application-level image_id."""
        sql = "SELECT * FROM image_metadata WHERE image_id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (image_id,))
                row = cursor.fetchone()
                if row:
                    return ImageMetadata.model_validate(dict(row))
                return None
        except sqlite3.Error as e:
            logger.error("Failed to query image metadata for image_id %s: %s", image_id, e)
            raise MetadataPersistenceError(f"Metadata query failed: {e}") from e

    def get_by_public_id(self, public_id: str) -> Optional[ImageMetadata]:
        """Retrieve image metadata by its Cloudinary public_id."""
        sql = "SELECT * FROM image_metadata WHERE public_id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (public_id,))
                row = cursor.fetchone()
                if row:
                    return ImageMetadata.model_validate(dict(row))
                return None
        except sqlite3.Error as e:
            logger.error("Failed to query image metadata for public_id %s: %s", public_id, e)
            raise MetadataPersistenceError(f"Metadata query failed: {e}") from e

    def list_by_inspection_id(self, inspection_id: str) -> List[ImageMetadata]:
        """Retrieve all images associated with a given inspection session."""
        sql = "SELECT * FROM image_metadata WHERE inspection_id = ? ORDER BY created_at ASC;"
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (inspection_id,))
                rows = cursor.fetchall()
                return [ImageMetadata.model_validate(dict(r)) for r in rows]
        except sqlite3.Error as e:
            logger.error("Failed to list images for inspection_id %s: %s", inspection_id, e)
            raise MetadataPersistenceError(f"Metadata listing failed: {e}") from e

    def delete(self, image_id: str) -> bool:
        """Delete an image record from the database.

        Returns:
            bool: True if row existed and was deleted, False otherwise.
        """
        sql = "DELETE FROM image_metadata WHERE image_id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, (image_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Failed to delete image record %s: %s", image_id, e)
            raise MetadataPersistenceError(f"Metadata deletion failed: {e}") from e

    def clear(self) -> None:
        """Clear all records (primarily for testing isolation)."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM image_metadata;")
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to clear image_metadata table: %s", e)
            raise MetadataPersistenceError(f"Table clear failed: {e}") from e


image_repository = ImageRepository()
