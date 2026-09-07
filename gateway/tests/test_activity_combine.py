# Copyright 2017-present, The Visdom Authors
"""Folding several instances' answers about one workspace into one."""

from app.admin.activity import _combine


def fold(*entries):
    merged = {}
    for entry in entries:
        _combine(merged, "ws-1", dict(entry, workspace_id="ws-1"))
    return merged["ws-1"]


def test_live_counts_add_up_across_instances():
    result = fold({"viewers": 2, "writers": 1}, {"viewers": 3, "writers": 0})

    assert result["viewers"] == 5
    assert result["writers"] == 1


def test_running_totals_add_up_too():
    """A workspace moves between instances when one restarts, so the work each
    did is a share of the same total, not a rival answer to it."""
    result = fold(
        {"writes": 10, "broadcasts": 4, "broadcast_bytes": 100},
        {"writes": 3, "broadcasts": 1, "broadcast_bytes": 25},
    )

    assert result["writes"] == 13
    assert result["broadcasts"] == 5
    assert result["broadcast_bytes"] == 125


def test_an_instance_that_only_sees_the_files_does_not_zero_the_real_answer():
    """Every instance shares the volume, so all of them report every workspace
    while only one has the sockets."""
    result = fold({"viewers": 4, "writes": 9}, {"viewers": 0, "writes": 0})

    assert result["viewers"] == 4
    assert result["writes"] == 9


def test_the_latest_write_and_the_largest_size_win():
    result = fold(
        {"last_active_at": 100.0, "bytes": 2048},
        {"last_active_at": 500.0, "bytes": 1024},
    )

    assert result["last_active_at"] == 500.0
    assert result["bytes"] == 2048


def test_a_counter_no_instance_reports_stays_absent():
    """A visdom that predates these counters should read as unknown, not as a
    workspace that has done no work."""
    result = fold({"viewers": 1}, {"viewers": 1})

    assert "writes" not in result
    assert "broadcasts" not in result


def test_a_slug_is_taken_from_whichever_instance_knows_it():
    result = fold({"slug": None, "viewers": 0}, {"slug": "real-one", "viewers": 1})

    assert result["slug"] == "real-one"
