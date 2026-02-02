"""Tests for decorator implementations."""

from decorators import (
    filter_by_current_user,
    log_processes,
    max_listing,
    sort_processes,
    suppress_errors,
)


def test_suppress_errors():
    """Test that suppress_errors catches specified exceptions."""

    @suppress_errors(ValueError, TypeError)
    def risky_function(should_fail=True):
        if should_fail:
            raise ValueError("Expected error")
        return [{"name": "test"}]

    # Should suppress ValueError and return empty list
    result = risky_function(should_fail=True)
    assert result == []

    # Should work normally
    result = risky_function(should_fail=False)
    assert len(result) == 1


def test_suppress_errors_propagates_others():
    """Test that suppress_errors doesn't catch other exceptions."""

    @suppress_errors(ValueError)
    def risky_function():
        raise TypeError("Different error")

    try:
        risky_function()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_log_processes(tmp_path):
    """Test that log_processes writes process info to file."""
    log_file = tmp_path / "test_processes.log"

    @log_processes(str(log_file))
    def get_test_processes():
        return [
            {
                "pid": 1234,
                "name": "test.exe",
                "cpu_percent": 15.5,
                "memory_percent": 8.2,
                "username": "testuser",
                "cmdline": ["test.exe", "--arg"],
                "exe": "/path/to/test.exe",
                "phys_mem": 1024 * 1024 * 100,  # 100 MB in bytes
            },
            {
                "pid": 5678,
                "name": "app.exe",
                "cpu_percent": 12.3,
                "memory_percent": 5.7,
                "username": "admin",
                "cmdline": ["app.exe"],
                "exe": "/path/to/app.exe",
                "phys_mem": 1024 * 1024 * 50,  # 50 MB in bytes
            },
        ]

    processes = get_test_processes()

    assert log_file.exists()
    content = log_file.read_text()
    assert "2 processes" in content
    assert "test.exe" in content
    assert "1234" in content
    assert "15.5" in content or "15.50" in content
    assert len(processes) == 2


def test_filter_by_current_user():
    """Test that filter_by_current_user filters processes correctly."""
    import getpass

    current_user = getpass.getuser()

    @filter_by_current_user
    def get_test_processes():
        return [
            {"name": "my_process.exe", "username": current_user, "cpu_percent": 10},
            {"name": "other_process.exe", "username": "other_user", "cpu_percent": 15},
            {"name": "system_process.exe", "username": None, "cpu_percent": 5},
            {"name": "my_other.exe", "username": current_user, "cpu_percent": 20},
        ]

    filtered = get_test_processes()

    # Should only have processes for current user
    assert len(filtered) == 2
    assert all(p["username"] == current_user for p in filtered)


def test_sort_processes_by_cpu():
    """Test sort_processes decorator sorting by CPU percent."""

    @sort_processes(field="cpu_percent", reverse=True)
    def get_test_processes():
        return [
            {"name": "low.exe", "cpu_percent": 5.0},
            {"name": "high.exe", "cpu_percent": 20.0},
            {"name": "medium.exe", "cpu_percent": 10.0},
        ]

    sorted_procs = get_test_processes()

    # Should be sorted by CPU in descending order
    assert len(sorted_procs) == 3
    assert sorted_procs[0]["cpu_percent"] == 20.0
    assert sorted_procs[1]["cpu_percent"] == 10.0
    assert sorted_procs[2]["cpu_percent"] == 5.0


def test_sort_processes_by_name():
    """Test sort_processes decorator sorting by name."""

    @sort_processes(field="name", reverse=False)
    def get_test_processes():
        return [
            {"name": "zebra.exe", "cpu_percent": 5.0},
            {"name": "apple.exe", "cpu_percent": 20.0},
            {"name": "middle.exe", "cpu_percent": 10.0},
        ]

    sorted_procs = get_test_processes()

    # Should be sorted by name in ascending order
    assert len(sorted_procs) == 3
    assert sorted_procs[0]["name"] == "apple.exe"
    assert sorted_procs[1]["name"] == "middle.exe"
    assert sorted_procs[2]["name"] == "zebra.exe"


def test_max_listing_limits_results():
    """Test max_listing decorator limits number of results."""

    @max_listing(max_count=2)
    def get_test_processes():
        return [
            {"name": "proc1.exe", "cpu_percent": 5.0},
            {"name": "proc2.exe", "cpu_percent": 10.0},
            {"name": "proc3.exe", "cpu_percent": 15.0},
            {"name": "proc4.exe", "cpu_percent": 20.0},
        ]

    limited_procs = get_test_processes()

    # Should only return first 2 processes
    assert len(limited_procs) == 2
    assert limited_procs[0]["name"] == "proc1.exe"
    assert limited_procs[1]["name"] == "proc2.exe"


def test_max_listing_under_limit():
    """Test max_listing decorator when results are under limit."""

    @max_listing(max_count=10)
    def get_test_processes():
        return [
            {"name": "proc1.exe", "cpu_percent": 5.0},
            {"name": "proc2.exe", "cpu_percent": 10.0},
        ]

    limited_procs = get_test_processes()

    # Should return all processes since under limit
    assert len(limited_procs) == 2