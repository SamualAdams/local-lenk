# Django + PostgreSQL Migration Plan for Lenk

## Executive Summary

This document outlines a comprehensive plan to restructure the Lenk file viewer application into a proper Django application using PostgreSQL. The current application uses a Django-like directory structure but implements custom database handling with SQLite. This migration will leverage Django's ORM, settings management, and application architecture while maintaining the desktop Tkinter GUI.

---

## Current Architecture Analysis

### Directory Structure
```
lenk/
├── manage.py                    # Entry point (Django-like)
├── lenk/
│   ├── __init__.py
│   ├── __main__.py              # Package entrypoint
│   └── apps/
│       └── viewer/
│           ├── __init__.py
│           ├── app.py           # Main Tkinter GUI (1571 lines)
│           ├── database.py      # SQLite mixin (186 lines)
│           ├── navigation.py    # Navigation state mixin (120 lines)
│           └── comments.py      # Comment/audio mixin (221 lines)
└── docs/
    └── README.md
```

### Current Technology Stack
- **GUI**: Tkinter (desktop application)
- **Database**: SQLite (~/.file_viewer_stars.db)
- **Data Access**: Custom SQL with mixins
- **Architecture**: Mixin-based composition
- **Python**: 3.10+

### Current Database Schema (SQLite)

**Tables:**
1. `starred` - Favorite/starred file paths
2. `comments` - Cell-level comments with fuzzy matching
3. `settings` - Key-value configuration storage
4. `session_state` - Last browsing session persistence

### Key Features
- File browsing with favorites (starred items)
- Markdown cell-based viewing (Instagram-style navigation)
- Comments per markdown cell with content hashing
- Fuzzy comment matching when content changes
- Text-to-speech (macOS `say` command)
- OpenAI ChatGPT integration for @chat commands
- Session persistence (directory, file, cell position)
- Navigation state persistence (tree expansion)
- Export annotated markdown files
- Comment narration queue

---

## Target Django Architecture

### Proposed Directory Structure

```
lenk/                                    # Project root
├── manage.py                            # Django management script
├── pyproject.toml                       # Modern Python packaging
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
├── README.md                            # Main documentation
│
├── lenk/                                # Django project package
│   ├── __init__.py
│   ├── settings/                        # Split settings
│   │   ├── __init__.py
│   │   ├── base.py                      # Common settings
│   │   ├── development.py               # Dev overrides
│   │   └── production.py                # Prod overrides
│   ├── urls.py                          # URL routing (minimal for desktop)
│   ├── wsgi.py                          # WSGI entry (optional)
│   └── asgi.py                          # ASGI entry (optional)
│
├── apps/                                # Django apps directory
│   ├── __init__.py
│   │
│   ├── core/                            # Core utilities
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                    # Base abstract models
│   │   ├── managers.py                  # Custom model managers
│   │   └── utils.py                     # Shared utilities
│   │
│   ├── files/                           # File management app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                    # StarredFile model
│   │   ├── managers.py                  # File query managers
│   │   ├── services.py                  # Business logic
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── comments/                        # Comments app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                    # Comment, CellHash models
│   │   ├── managers.py                  # Comment query managers
│   │   ├── services.py                  # Comment matching logic
│   │   ├── ai.py                        # OpenAI integration
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── settings/                        # Settings app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                    # UserSetting model
│   │   ├── managers.py
│   │   ├── services.py                  # Settings management
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── sessions/                        # Session state app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                    # ViewerSession, NavigationState
│   │   ├── managers.py
│   │   ├── services.py                  # Session persistence
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   └── viewer/                          # Desktop GUI app
│       ├── __init__.py
│       ├── apps.py
│       ├── main.py                      # Entry point (calls gui.py)
│       ├── gui/                         # GUI components
│       │   ├── __init__.py
│       │   ├── main_window.py           # Main FileViewer class
│       │   ├── widgets.py               # Custom widgets
│       │   ├── markdown_renderer.py     # Markdown display logic
│       │   └── dialogs.py               # Settings, dialogs
│       ├── audio/                       # Audio/TTS functionality
│       │   ├── __init__.py
│       │   ├── tts.py                   # Text-to-speech
│       │   ├── narration.py             # Comment narration
│       │   └── dictation.py             # Comment reading
│       └── utils/                       # Viewer utilities
│           ├── __init__.py
│           ├── clipboard.py             # Clipboard operations
│           └── markdown_parser.py       # Cell parsing
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── test_files/
│   ├── test_comments/
│   ├── test_settings/
│   └── test_viewer/
│
└── docs/                                # Documentation
    ├── README.md                        # Quick start
    ├── DJANGO_MIGRATION_PLAN.md         # This document
    ├── ARCHITECTURE.md                  # Architecture overview
    └── DEPLOYMENT.md                    # Deployment guide
```

---

## Django Models Design

### App: `files` (Starred Files)

```python
# apps/files/models.py
from django.db import models
from apps.core.models import TimeStampedModel

class StarredFile(TimeStampedModel):
    """Represents a user-favorited file or directory."""

    path = models.TextField(unique=True, db_index=True)
    starred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'starred_files'
        ordering = ['-starred_at']
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['-starred_at']),
        ]

    def __str__(self):
        return self.path

    @property
    def exists(self):
        """Check if the file still exists on disk."""
        import os
        return os.path.exists(self.path)

    @property
    def is_directory(self):
        import os
        return os.path.isdir(self.path)
```

### App: `comments` (Comments & Cell Hashing)

```python
# apps/comments/models.py
from django.db import models
from apps.core.models import TimeStampedModel

class Comment(TimeStampedModel):
    """Cell-level comment with fuzzy matching support."""

    MATCH_CONFIDENCE_CHOICES = [
        ('exact', 'Exact Match'),
        ('fuzzy', 'Fuzzy Match'),
    ]

    file_path = models.TextField(db_index=True)
    heading_text = models.TextField()
    content_hash = models.CharField(max_length=32)  # MD5 hash
    cell_index = models.IntegerField()
    comment_text = models.TextField()
    match_confidence = models.CharField(
        max_length=10,
        choices=MATCH_CONFIDENCE_CHOICES,
        default='exact'
    )
    last_matched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['file_path', 'heading_text', 'content_hash']),
            models.Index(fields=['file_path', 'heading_text']),
            models.Index(fields=['file_path']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Comment on {self.file_path} - {self.heading_text[:50]}"

    @property
    def is_fuzzy_match(self):
        return self.match_confidence == 'fuzzy'

    @property
    def is_likely_outdated(self):
        """Check if comment might be outdated based on match confidence."""
        return self.match_confidence == 'fuzzy'
```

### App: `settings` (User Settings)

```python
# apps/settings/models.py
from django.db import models
from apps.core.models import TimeStampedModel

class UserSetting(TimeStampedModel):
    """Key-value store for user preferences."""

    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.TextField()

    class Meta:
        db_table = 'user_settings'
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value[:50]}"

    @classmethod
    def get_value(cls, key, default=None):
        """Get setting value with default fallback."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value):
        """Set or update a setting value."""
        obj, _ = cls.objects.update_or_create(
            key=key,
            defaults={'value': str(value)}
        )
        return obj
```

### App: `sessions` (Session State)

```python
# apps/sessions/models.py
from django.db import models
from apps.core.models import TimeStampedModel

class ViewerSession(TimeStampedModel):
    """Persists the viewer's browsing session."""

    # Singleton pattern - only one session record
    id = models.IntegerField(primary_key=True, default=1)
    current_directory = models.TextField(blank=True, null=True)
    current_file = models.TextField(blank=True, null=True)
    current_cell = models.IntegerField(default=0)

    class Meta:
        db_table = 'viewer_sessions'

    def __str__(self):
        return f"Session: {self.current_file or 'No file'}"

    @classmethod
    def get_current(cls):
        """Get or create the singleton session instance."""
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def update_state(self, directory=None, file=None, cell=None):
        """Update session state fields."""
        if directory is not None:
            self.current_directory = directory
        if file is not None:
            self.current_file = file
        if cell is not None:
            self.current_cell = cell
        self.save()


class NavigationState(TimeStampedModel):
    """Stores tree expansion/selection state."""

    STATE_TYPE_CHOICES = [
        ('tree', 'File Tree'),
        ('favorites', 'Favorites Tree'),
    ]

    state_type = models.CharField(
        max_length=20,
        choices=STATE_TYPE_CHOICES,
        unique=True
    )
    open_paths = models.JSONField(default=list)
    selected_path = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'navigation_states'

    def __str__(self):
        return f"{self.state_type} navigation state"

    @classmethod
    def get_tree_state(cls):
        """Get file tree navigation state."""
        obj, _ = cls.objects.get_or_create(state_type='tree')
        return obj

    @classmethod
    def get_favorites_state(cls):
        """Get favorites tree navigation state."""
        obj, _ = cls.objects.get_or_create(state_type='favorites')
        return obj
```

### Core Models (Base Classes)

```python
# apps/core/models.py
from django.db import models

class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

---

## Django Settings Configuration

### Base Settings (`lenk/settings/base.py`)

```python
import os
from pathlib import Path
from decouple import config  # python-decouple for env vars

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    # Django core (minimal for desktop app)
    'django.contrib.contenttypes',
    'django.contrib.auth',  # Optional, for future multi-user support

    # Local apps
    'apps.core',
    'apps.files',
    'apps.comments',
    'apps.settings',
    'apps.sessions',
    'apps.viewer',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='lenk_db'),
        'USER': config('DB_USER', default='lenk_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Custom settings for Lenk
LENK_DEFAULT_HOME_DIR = config('LENK_HOME_DIR', default=str(Path.home()))
LENK_DEFAULT_VOICE_SPEED = config('LENK_VOICE_SPEED', default=200, cast=int)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
```

### Development Settings

```python
# lenk/settings/development.py
from .base import *

DEBUG = True
DATABASES['default']['NAME'] = 'lenk_dev'
```

### Production Settings

```python
# lenk/settings/production.py
from .base import *

DEBUG = False
DATABASES['default']['CONN_MAX_AGE'] = None  # Persistent connections
```

---

## Service Layer Architecture

### File Service (`apps/files/services.py`)

```python
from typing import List
from .models import StarredFile

class FileService:
    """Business logic for starred files."""

    @staticmethod
    def is_starred(path: str) -> bool:
        """Check if a path is starred."""
        return StarredFile.objects.filter(path=path).exists()

    @staticmethod
    def add_star(path: str) -> StarredFile:
        """Star a file or directory."""
        obj, created = StarredFile.objects.get_or_create(path=path)
        return obj

    @staticmethod
    def remove_star(path: str) -> bool:
        """Unstar a file or directory."""
        count, _ = StarredFile.objects.filter(path=path).delete()
        return count > 0

    @staticmethod
    def get_starred_items() -> List[str]:
        """Get all starred paths ordered by recency."""
        return list(
            StarredFile.objects.values_list('path', flat=True)
        )

    @staticmethod
    def cleanup_missing_files() -> int:
        """Remove starred entries for files that no longer exist."""
        import os
        starred = StarredFile.objects.all()
        deleted = 0
        for item in starred:
            if not os.path.exists(item.path):
                item.delete()
                deleted += 1
        return deleted
```

### Comment Service (`apps/comments/services.py`)

```python
import hashlib
from typing import List, Tuple
from .models import Comment

class CommentService:
    """Business logic for comments with fuzzy matching."""

    @staticmethod
    def get_cell_hash(content: str) -> str:
        """Generate MD5 hash of cell content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    @staticmethod
    def extract_heading(cell_content: str) -> str:
        """Extract heading from cell content."""
        lines = cell_content.strip().split('\n')
        for line in lines:
            if line.startswith('#'):
                return line.strip()
        return "[No Heading]"

    @staticmethod
    def get_comments(
        file_path: str,
        cell_content: str,
        cell_index: int
    ) -> List[Tuple[str, str, str]]:
        """Get comments for a cell with fuzzy matching.

        Returns list of tuples: (comment_text, created_at, confidence)
        """
        heading = CommentService.extract_heading(cell_content)
        content_hash = CommentService.get_cell_hash(cell_content)

        # Try exact match first
        exact_matches = Comment.objects.filter(
            file_path=file_path,
            heading_text=heading,
            content_hash=content_hash
        ).order_by('created_at')

        if exact_matches.exists():
            # Update match metadata
            exact_matches.update(
                match_confidence='exact',
                last_matched_at=models.F('last_matched_at')
            )
            return [
                (c.comment_text, c.created_at.isoformat(), c.match_confidence)
                for c in exact_matches
            ]

        # Fallback to fuzzy match (heading only)
        fuzzy_matches = Comment.objects.filter(
            file_path=file_path,
            heading_text=heading
        ).order_by('created_at')

        if fuzzy_matches.exists():
            # Update match metadata
            fuzzy_matches.update(match_confidence='fuzzy')
            return [
                (c.comment_text, c.created_at.isoformat(), 'fuzzy')
                for c in fuzzy_matches
            ]

        return []

    @staticmethod
    def add_comment(
        file_path: str,
        cell_content: str,
        cell_index: int,
        comment_text: str
    ) -> Comment:
        """Add a new comment to a cell."""
        heading = CommentService.extract_heading(cell_content)
        content_hash = CommentService.get_cell_hash(cell_content)

        comment = Comment.objects.create(
            file_path=file_path,
            heading_text=heading,
            content_hash=content_hash,
            cell_index=cell_index,
            comment_text=comment_text,
            match_confidence='exact'
        )
        return comment
```

---

## Migration Strategy

### Phase 1: Setup & Dependencies (Week 1)

**Tasks:**
1. Create `pyproject.toml` with modern packaging
2. Add dependencies:
   - Django 4.2+ (LTS)
   - psycopg2-binary (PostgreSQL adapter)
   - python-decouple (environment variables)
   - pytest-django (testing)
3. Set up PostgreSQL database locally
4. Create `.env.example` template
5. Initialize Django project structure

**Dependencies:**
```toml
[project]
name = "lenk"
version = "0.2.0"
dependencies = [
    "django>=4.2,<5.0",
    "psycopg2-binary>=2.9",
    "python-decouple>=3.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-django>=4.5",
    "black>=23.0",
    "ruff>=0.1",
]
```

### Phase 2: Django Apps & Models (Week 2)

**Tasks:**
1. Create app structure (core, files, comments, settings, sessions)
2. Define all Django models
3. Create initial migrations
4. Set up Django settings (base, dev, prod)
5. Configure PostgreSQL connection

**Migration Commands:**
```bash
# Create apps
django-admin startapp core apps/core
django-admin startapp files apps/files
django-admin startapp comments apps/comments
django-admin startapp settings apps/settings
django-admin startapp sessions apps/sessions

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Phase 3: Service Layer (Week 3)

**Tasks:**
1. Implement service classes for each app
2. Write comprehensive unit tests
3. Create data migration script (SQLite → PostgreSQL)
4. Test data migration with real user data

**Data Migration Script:**
```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import os
from django.core.management.base import BaseCommand
from apps.files.models import StarredFile
from apps.comments.models import Comment
from apps.settings.models import UserSetting
from apps.sessions.models import ViewerSession, NavigationState

class Command(BaseCommand):
    help = 'Migrate data from SQLite to PostgreSQL'

    def handle(self, *args, **options):
        db_path = os.path.expanduser("~/.file_viewer_stars.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Migrate starred files
        cursor.execute('SELECT path, starred_at FROM starred')
        for path, starred_at in cursor.fetchall():
            StarredFile.objects.get_or_create(
                path=path,
                defaults={'starred_at': starred_at}
            )

        # Migrate comments
        cursor.execute('''
            SELECT file_path, heading_text, content_hash, cell_index,
                   comment_text, created_at, match_confidence
            FROM comments
        ''')
        for row in cursor.fetchall():
            Comment.objects.get_or_create(
                file_path=row[0],
                heading_text=row[1],
                content_hash=row[2],
                cell_index=row[3],
                comment_text=row[4],
                defaults={
                    'created_at': row[5],
                    'match_confidence': row[6]
                }
            )

        # Migrate settings
        cursor.execute('SELECT key, value FROM settings')
        for key, value in cursor.fetchall():
            UserSetting.set_value(key, value)

        # Migrate session state
        cursor.execute('''
            SELECT current_directory, current_file, current_cell
            FROM session_state WHERE id = 1
        ''')
        row = cursor.fetchone()
        if row:
            session = ViewerSession.get_current()
            session.update_state(
                directory=row[0],
                file=row[1],
                cell=row[2]
            )

        conn.close()
        self.stdout.write(self.style.SUCCESS('Migration complete!'))
```

### Phase 4: Refactor GUI Layer (Week 4)

**Tasks:**
1. Refactor `app.py` into modular GUI components
2. Replace mixin database calls with Django ORM service calls
3. Update GUI to use Django models instead of direct SQL
4. Maintain all existing Tkinter functionality

**Before (Current):**
```python
# lenk/apps/viewer/app.py
class FileViewer(DatabaseMixin, NavigationStateMixin, CommentAudioMixin):
    def __init__(self, root):
        self.init_database()  # Custom SQLite
        self.load_settings()  # Custom SQL
```

**After (Django):**
```python
# apps/viewer/gui/main_window.py
import django
django.setup()  # Initialize Django

from apps.files.services import FileService
from apps.settings.models import UserSetting

class FileViewer:
    def __init__(self, root):
        self.file_service = FileService()
        self.load_settings()

    def load_settings(self):
        self.home_directory = UserSetting.get_value(
            'home_directory',
            default=str(Path.home())
        )
        self.voice_speed = int(UserSetting.get_value('voice_speed', '200'))
```

### Phase 5: Testing & Documentation (Week 5)

**Tasks:**
1. Write integration tests for all services
2. Test GUI with PostgreSQL backend
3. Performance testing & optimization
4. Update documentation
5. Create deployment guide

**Test Example:**
```python
# tests/test_comments/test_services.py
import pytest
from apps.comments.services import CommentService
from apps.comments.models import Comment

@pytest.mark.django_db
class TestCommentService:
    def test_add_and_get_comment_exact_match(self):
        # Add comment
        comment = CommentService.add_comment(
            file_path='/test/file.md',
            cell_content='# Test Heading\nContent here',
            cell_index=0,
            comment_text='This is a test comment'
        )

        # Retrieve with exact match
        comments = CommentService.get_comments(
            file_path='/test/file.md',
            cell_content='# Test Heading\nContent here',
            cell_index=0
        )

        assert len(comments) == 1
        assert comments[0][0] == 'This is a test comment'
        assert comments[0][2] == 'exact'

    def test_fuzzy_match_when_content_changes(self):
        # Add comment with original content
        CommentService.add_comment(
            file_path='/test/file.md',
            cell_content='# Test Heading\nOriginal content',
            cell_index=0,
            comment_text='Original comment'
        )

        # Try to get with changed content (same heading)
        comments = CommentService.get_comments(
            file_path='/test/file.md',
            cell_content='# Test Heading\nModified content',
            cell_index=0
        )

        assert len(comments) == 1
        assert comments[0][2] == 'fuzzy'
```

### Phase 6: Deployment & Migration (Week 6)

**Tasks:**
1. Create backup of SQLite database
2. Run migration script on production data
3. Deploy PostgreSQL database
4. Update `manage.py` to use Django's management commands
5. Create rollback plan

---

## PostgreSQL Setup

### Local Development

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database and user
psql postgres
CREATE DATABASE lenk_dev;
CREATE USER lenk_user WITH PASSWORD 'your_password';
ALTER ROLE lenk_user SET client_encoding TO 'utf8';
ALTER ROLE lenk_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lenk_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE lenk_dev TO lenk_user;
\q
```

### Environment Configuration

```bash
# .env file
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_NAME=lenk_dev
DB_USER=lenk_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=your-openai-key-here
```

---

## Benefits of Django + PostgreSQL

### 1. **Robust ORM**
- Type-safe database operations
- Query optimization
- Built-in migrations
- Relationship management

### 2. **Better Data Integrity**
- ACID transactions
- Foreign key constraints
- Data validation at model level
- Atomic operations

### 3. **Scalability**
- PostgreSQL handles larger datasets better than SQLite
- Support for concurrent access (future multi-user?)
- Better indexing capabilities
- Full-text search (for future features)

### 4. **Developer Experience**
- Django admin (optional, for debugging)
- Management commands
- Testing framework
- Rich ecosystem

### 5. **Future-Proofing**
- Easy to add web interface later
- API endpoints (Django REST Framework)
- User authentication system
- Cloud deployment ready

---

## Potential Challenges & Solutions

### Challenge 1: Desktop App + Django
**Problem:** Django is web-focused; desktop apps are unusual.

**Solution:**
- Django can run without web server
- Call `django.setup()` at app startup
- Use ORM and models independently
- No need for URLs, views, or templates

### Challenge 2: Performance Overhead
**Problem:** Django ORM might be slower than raw SQL.

**Solution:**
- Use `select_related()` and `prefetch_related()` for optimization
- Enable query caching
- Use database indexes strategically
- Profile and optimize hot paths

### Challenge 3: Distribution & Dependencies
**Problem:** More dependencies to bundle.

**Solution:**
- Use PyInstaller or cx_Freeze for packaging
- Include PostgreSQL client libraries
- Consider embedded PostgreSQL (PostgreSQL Portable)
- Or use Docker for consistent environment

### Challenge 4: Database Setup for End Users
**Problem:** Users need PostgreSQL installed.

**Solution:**
- Provide Docker Compose setup
- Create installer script
- Or: Use embedded PostgreSQL
- Alternative: Keep SQLite option for single-user mode

---

## Hybrid Approach: Multi-Backend Support

### Strategy: Support Both SQLite and PostgreSQL

Allow users to choose their database backend via configuration:

```python
# lenk/settings/base.py
DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # ... postgres config
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

**Benefits:**
- Easy onboarding (SQLite by default)
- Power users can opt into PostgreSQL
- Same ORM code works for both
- Gradual migration path

---

## Next Steps & Decision Points

### Questions to Answer:

1. **Single-user or multi-user?**
   - Single-user: SQLite might be sufficient
   - Multi-user/cloud: PostgreSQL required

2. **Distribution model?**
   - Standalone app: Embedded database preferred
   - Developer tool: PostgreSQL acceptable

3. **Performance requirements?**
   - Current SQLite performance acceptable?
   - Expected dataset size?

4. **Future features?**
   - Web interface planned?
   - API access needed?
   - Cloud sync desired?

### Recommended Approach:

**Option A: Full PostgreSQL Migration**
- Best for: Future web features, multi-user support
- Effort: ~6 weeks
- Risk: Medium (deployment complexity)

**Option B: Django ORM + Hybrid Backend**
- Best for: Flexibility, gradual migration
- Effort: ~4 weeks
- Risk: Low (fallback to SQLite)

**Option C: Django ORM + SQLite Only**
- Best for: Quick wins, single-user app
- Effort: ~3 weeks
- Risk: Very low (minimal change)

---

## Conclusion

Migrating Lenk to Django with PostgreSQL will provide:
- Modern, maintainable architecture
- Better data integrity and performance
- Future-proofing for web/API features
- Improved developer experience

The recommended path is **Option B (Hybrid Backend)** which provides the best balance of benefits while minimizing deployment complexity.

Next action: Review this plan and decide on the preferred approach, then begin Phase 1 implementation.
