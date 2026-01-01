"""Smoke tests for db_helper and schema initialization.

These tests verify that:
1. Database schema initializes correctly from schema.sql
2. Helper functions can read/write to expected tables
3. Core contract between helpers and schema is valid
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path so we can import helpers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.db_helper import (
    get_connection,
    init_database,
    create_workspace,
    get_workspace,
    list_workspaces,
    add_rule,
    get_rules,
    add_integration,
    get_integrations,
    get_preference,
    set_preference,
    get_template,
    list_templates,
)


class TestDatabaseInitialization:
    """Test database schema initialization."""

    def test_init_database_creates_core_tables(self):
        """Verify that init_database creates expected tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            schema_path = Path(__file__).parent.parent / "schema.sql"

            # Initialize database
            init_database(db_path=db_path, schema_path=schema_path)

            # Verify database file exists
            assert db_path.exists(), "Database file was not created"

            # Check for expected tables
            with get_connection(db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                )
                tables = {row[0] for row in cursor.fetchall()}

            # Verify core tables exist
            expected_tables = {
                "workspaces",
                "cursor_rules",
                "integrations",
                "templates",
                "preferences",
                "mcp_servers",
            }
            assert expected_tables.issubset(
                tables
            ), f"Missing tables: {expected_tables - tables}"

    def test_init_database_with_dexter_sql(self):
        """Verify that dexter.sql schema initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            dexter_schema = Path(__file__).parent.parent / "dexter.sql"

            # Initialize with dexter.sql
            init_database(db_path=db_path, schema_path=dexter_schema)

            # Check for control-plane tables
            with get_connection(db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                )
                tables = {row[0] for row in cursor.fetchall()}

            expected_tables = {
                "action_log",
                "rules",
                "context",
                "domains",
                "checkpoints",
            }
            assert expected_tables.issubset(
                tables
            ), f"Missing tables: {expected_tables - tables}"


class TestWorkspaceHelpers:
    """Test workspace CRUD operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            schema_path = Path(__file__).parent.parent / "schema.sql"
            init_database(db_path=db_path, schema_path=schema_path)

            # Temporarily override DB_PATH for testing
            original_db_path = os.environ.get("DB_PATH")
            os.environ["DB_PATH"] = str(db_path)

            yield db_path

            # Restore original DB_PATH
            if original_db_path:
                os.environ["DB_PATH"] = original_db_path
            else:
                os.environ.pop("DB_PATH", None)

    def test_create_and_get_workspace(self, temp_db):
        """Test creating and retrieving a workspace."""
        workspace_id = create_workspace(
            name="Test Workspace",
            description="A test workspace",
            project_type="test",
        )

        assert workspace_id is not None, "Workspace ID should not be None"

        workspace = get_workspace(workspace_id)
        assert workspace is not None, "Workspace should be retrievable"
        assert workspace["name"] == "Test Workspace"
        assert workspace["description"] == "A test workspace"
        assert workspace["project_type"] == "test"

    def test_list_workspaces(self, temp_db):
        """Test listing all workspaces."""
        create_workspace(name="Workspace 1")
        create_workspace(name="Workspace 2")

        workspaces = list_workspaces()
        assert len(workspaces) >= 2, "Should have at least 2 workspaces"
        names = {ws["name"] for ws in workspaces}
        assert "Workspace 1" in names
        assert "Workspace 2" in names


class TestRuleHelpers:
    """Test cursor rule management."""

    @pytest.fixture
    def temp_db_with_workspace(self):
        """Create a database with a workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            schema_path = Path(__file__).parent.parent / "schema.sql"
            init_database(db_path=db_path, schema_path=schema_path)

            original_db_path = os.environ.get("DB_PATH")
            os.environ["DB_PATH"] = str(db_path)

            workspace_id = create_workspace(name="Test")

            yield db_path, workspace_id

            if original_db_path:
                os.environ["DB_PATH"] = original_db_path
            else:
                os.environ.pop("DB_PATH", None)

    def test_add_and_get_rules(self, temp_db_with_workspace):
        """Test adding and retrieving rules."""
        _, workspace_id = temp_db_with_workspace

        rule_id = add_rule(
            workspace_id=workspace_id,
            rule_name="test_rule",
            content="Test rule content",
            description="A test rule",
        )

        assert rule_id is not None

        rules = get_rules(workspace_id)
        assert len(rules) >= 1
        rule_names = {rule["rule_name"] for rule in rules}
        assert "test_rule" in rule_names


class TestIntegrationHelpers:
    """Test integration management."""

    @pytest.fixture
    def temp_db_with_workspace(self):
        """Create a database with a workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            schema_path = Path(__file__).parent.parent / "schema.sql"
            init_database(db_path=db_path, schema_path=schema_path)

            original_db_path = os.environ.get("DB_PATH")
            os.environ["DB_PATH"] = str(db_path)

            workspace_id = create_workspace(name="Test")

            yield db_path, workspace_id

            if original_db_path:
                os.environ["DB_PATH"] = original_db_path
            else:
                os.environ.pop("DB_PATH", None)

    def test_add_and_get_integrations(self, temp_db_with_workspace):
        """Test adding and retrieving integrations."""
        _, workspace_id = temp_db_with_workspace

        integration_id = add_integration(
            workspace_id=workspace_id,
            integration_type="test",
            name="Test Integration",
            config_json='{"key": "value"}',
            api_key_env_var="TEST_API_KEY",
        )

        assert integration_id is not None

        integrations = get_integrations(workspace_id)
        assert len(integrations) >= 1
        names = {integ["name"] for integ in integrations}
        assert "Test Integration" in names


class TestPreferenceHelpers:
    """Test preference management."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            schema_path = Path(__file__).parent.parent / "schema.sql"
            init_database(db_path=db_path, schema_path=schema_path)

            original_db_path = os.environ.get("DB_PATH")
            os.environ["DB_PATH"] = str(db_path)

            yield db_path

            if original_db_path:
                os.environ["DB_PATH"] = original_db_path
            else:
                os.environ.pop("DB_PATH", None)

    def test_set_and_get_preference(self, temp_db):
        """Test setting and retrieving preferences."""
        set_preference("test_key", "test_value", "A test preference")

        value = get_preference("test_key")
        assert value == "test_value"

    def test_update_preference(self, temp_db):
        """Test updating an existing preference."""
        set_preference("update_key", "value1")
        set_preference("update_key", "value2")

        value = get_preference("update_key")
        assert value == "value2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
