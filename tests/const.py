"""Sample WakaTime API responses for tests."""

USER_INFO = {
    "data": {
        "id": "user-123",
        "email": "dev@example.com",
        "username": "dev",
        "display_name": "Dev Example",
        "timezone": "America/Sao_Paulo",
    }
}

STATS = {
    "data": {
        "total_seconds": 36000.0,
        "daily_average": 9000.0,
        "human_readable_total": "10 hrs",
        "human_readable_daily_average": "2 hrs 30 mins",
        "is_up_to_date": True,
        "range": "last_7_days",
        "start": "2026-05-22T00:00:00Z",
        "end": "2026-05-29T00:00:00Z",
        "best_day": {
            "date": "2026-05-27",
            "text": "5 hrs",
            "total_seconds": 18000.0,
        },
        "languages": [
            {"name": "Python", "total_seconds": 20000.0, "percent": 55.5, "text": "5 hrs"},
            {"name": "Rust", "total_seconds": 10000.0, "percent": 27.7, "text": "2 hrs"},
        ],
        "editors": [{"name": "VS Code", "percent": 100.0, "text": "10 hrs"}],
        "operating_systems": [{"name": "Mac", "percent": 100.0, "text": "10 hrs"}],
        "projects": [
            {"name": "ha-wakatime", "total_seconds": 21600.0, "percent": 60.0, "text": "6 hrs"},
            {"name": "side-project", "total_seconds": 14400.0, "percent": 40.0, "text": "4 hrs"},
        ],
        "categories": [{"name": "Coding", "percent": 90.0, "text": "9 hrs"}],
        "machines": [{"name": "macbook", "percent": 100.0, "text": "10 hrs"}],
        "dependencies": [{"name": "aiohttp", "percent": 30.0, "text": "3 hrs"}],
    }
}

SUMMARY_TODAY = {
    "data": [
        {"grand_total": {"total_seconds": 3600.0, "text": "1 hr"}}
    ]
}

ALL_TIME = {
    "data": {
        "total_seconds": 360000.0,
        "daily_average": 7200.0,
        "text": "100 hrs",
        "is_up_to_date": True,
        "range": {"start": "2024-01-01", "end": "2026-05-29", "timezone": "America/Sao_Paulo"},
    }
}

GOALS = {
    "data": [
        {
            "id": "goal-1",
            "title": "Code 2 hrs per day",
            "type": "coding",
            "status": "success",
            "is_enabled": True,
            "average_status": "success",
            "seconds": 7200,
            "delta": "day",
            "range": "last 7 days",
        }
    ]
}

MACHINES = {
    "data": [
        {"name": "macbook", "ip": "10.0.0.1", "last_seen_at": "2026-05-29T12:00:00Z", "timezone": "America/Sao_Paulo"}
    ]
}

PROJECTS = {
    "data": [
        {"name": "ha-wakatime", "repository": "github.com/x/ha-wakatime", "language": "Python"},
        {"name": "side-project", "repository": None, "language": "Rust"},
    ]
}
