# WakaTime Full Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Home Assistant WakaTime custom integration to expose the maximum amount of WakaTime data, make scan interval / stats range / sensors / goals / projects user-configurable via an Options flow, remove dead blueprint code, fix the broken auth, and add a full pytest test suite.

**Architecture:** Standard modern HA custom integration. A single `DataUpdateCoordinator` fetches all WakaTime endpoints in parallel and normalizes the responses into one dict. Sensors are declarative `SensorEntityDescription` objects carrying `value_fn`/`attr_fn` lambdas, plus dynamic per-goal and per-project sensors. Config is split into a `ConfigFlow` (API key) and an `OptionsFlow` (interval, range, sensor/goal/project selection); changing options reloads the entry. The integration uses `entry.runtime_data` to hold the coordinator.

**Tech Stack:** Python 3.12, `homeassistant==2025.2.4`, `aiohttp`, `voluptuous`, HA selectors, `pytest` + `pytest-homeassistant-custom-component==0.13.214`, `ruff`.

---

## Background: what's wrong today

- **Auth bug** (`api.py:20`): sends `Authorization: Basic {api_key}` with the raw key. WakaTime requires the key **base64-encoded** (`Basic base64(api_key)`). Auth is effectively broken.
- **Dead blueprint code**: `coordinator.py`, `entity.py`, `switch.py`, `binary_sensor.py`, `data.py` all reference `IntegrationBlueprint*` symbols and import `ATTRIBUTION` / API classes that don't exist. Only `Platform.SENSOR` is loaded, so they're unused but broken. They will be deleted or rewritten.
- **Broken sensors**: `current_streak` and `best_streak` read fields that the `all_time_since_today` endpoint does not return (always 0/`[]`). `most_active_time` reads `stats.data.best_day.time`, which doesn't exist (`best_day` has `date`/`text`/`total_seconds`). These are removed/replaced.
- **Not configurable**: `SCAN_INTERVAL` is hardcoded to 30 minutes; stats range is fixed; no way to choose sensors.
- **Limited data**: only summaries/stats/all-time are used. WakaTime also exposes machines, dependencies, categories, goals, projects, best-day, and human-readable aggregates.

## Verified WakaTime API facts (from https://wakatime.com/developers)

- **Auth**: HTTP Basic with **base64-encoded** API key: `Authorization: Basic <base64(api_key)>`.
- `GET /users/current` → `data`: `id`, `email`, `username`, `display_name`, `timezone`, ...
- `GET /users/current/stats/{range}` where range ∈ `last_7_days`, `last_30_days`, `last_6_months`, `last_year`, `all_time`. `data`: `total_seconds`, `daily_average`, `human_readable_total`, `human_readable_daily_average`, `is_up_to_date`, `range`, `start`, `end`, `best_day` (`{date, text, total_seconds}`), and arrays `languages`, `editors`, `operating_systems`, `projects`, `categories`, `machines`, `dependencies` — each item `{name, total_seconds, percent, digital, text, hours, minutes}`.
- `GET /users/current/summaries?start=&end=` → `data` is a **list** of days, each with `grand_total` (`{total_seconds, text, ...}`), `projects`, `languages`, ...
- `GET /users/current/all_time_since_today` → `data`: `total_seconds`, `daily_average`, `text`, `decimal`, `digital`, `is_up_to_date`, `range` (`{start, end, timezone}`). **No streak fields.**
- `GET /users/current/goals` → `data` is a list; each goal: `id`, `title`, `type`, `status`, `is_enabled`, `average_status`, `seconds`, `delta`, `range`, `chart_data`.
- `GET /users/current/machine_names` → `data` list: `name`, `ip`, `last_seen_at`, `timezone`.
- `GET /users/current/projects` → `data` list: `name`, `repository`, `language`.

---

## File Structure

**`custom_components/wakatime/` (after refactor):**

| File | Responsibility |
|------|----------------|
| `const.py` | All constants: domain, base URL, config/option keys, defaults, ranges, icons. |
| `api.py` | `WakatimeApiClient` (base64 auth, all endpoints) + `WakatimeApiError` / `WakatimeApiAuthError`. |
| `coordinator.py` | **Rewritten** `WakatimeDataUpdateCoordinator`: parallel fetch + normalize, interval/range from options. |
| `entity.py` | **Rewritten** `WakatimeEntity` base class with device info. |
| `__init__.py` | Setup/unload entry, `runtime_data`, options-reload listener, `WakatimeConfigEntry` type. |
| `config_flow.py` | `WakatimeConfigFlow` (API key) + `WakatimeOptionsFlow` (interval, range, sensors, goals, projects). |
| `sensor.py` | Declarative static sensors + dynamic goal/project sensors. |
| `diagnostics.py` | **New** redacted config-entry diagnostics. |
| `manifest.json` | Version bump, loggers, integration_type. |
| `translations/en.json`, `translations/pt-BR.json` | Config + options + entity strings. |
| ~~`switch.py`~~, ~~`binary_sensor.py`~~, ~~`data.py`~~ | **Deleted** (dead blueprint). |

**`tests/` (new):**

| File | Responsibility |
|------|----------------|
| `tests/__init__.py` | Makes `tests` a package (puts repo root on `sys.path`). |
| `tests/conftest.py` | `enable_custom_integrations` autouse + `mock_api` fixture. |
| `tests/const.py` | Sample WakaTime JSON fixtures. |
| `tests/test_api.py` | Base64 header, success parse, auth error. |
| `tests/test_config_flow.py` | User flow success / invalid auth / options flow. |
| `tests/test_init.py` | Setup + unload entry. |
| `tests/test_sensor.py` | Sensor states/attributes from mocked data. |

**Repo root:** `pytest.ini`, updated `requirements.txt`, new `.github/workflows/test.yml`, updated `README.md`.

---

### Task 1: Test scaffolding & dependencies

**Files:**
- Modify: `requirements.txt`
- Create: `pytest.ini`
- Create: `tests/__init__.py`
- Create: `tests/const.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add the test dependency**

Modify `requirements.txt` — append one line (keep existing pins):

```text
colorlog==6.9.0
homeassistant==2025.2.4
pip>=21.3.1
ruff==0.11.8
voluptuous==0.14.0
aiohttp==3.11.16
pytest==8.3.5
pytest-cov==4.1.0
pytest-homeassistant-custom-component==0.13.214
```

> `0.13.214` is the release whose pinned `homeassistant` is exactly `2025.2.4` (verified against the package's `ha_version`). It pulls in `pytest-asyncio`, `pytest-aiohttp`, and the HA test plugins.

- [ ] **Step 2: Install dependencies**

Run: `./scripts/setup`
Expected: installs without error; `pip show pytest-homeassistant-custom-component` reports `0.13.214`.

- [ ] **Step 3: Create `pytest.ini`**

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
norecursedirs = .git config
```

- [ ] **Step 4: Make `tests` a package**

Create `tests/__init__.py`:

```python
"""Tests for the Wakatime integration."""
```

- [ ] **Step 5: Create sample API fixtures**

Create `tests/const.py`:

```python
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
```

- [ ] **Step 6: Create `tests/conftest.py`**

Create `tests/conftest.py`:

```python
"""Shared fixtures for Wakatime tests."""

from unittest.mock import AsyncMock, patch

import pytest

from . import const

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading the wakatime custom integration in every test."""
    yield


@pytest.fixture
def mock_api():
    """Patch WakatimeApiClient everywhere it is imported with canned data."""
    with patch(
        "custom_components.wakatime.WakatimeApiClient", autospec=True
    ) as client_cls, patch(
        "custom_components.wakatime.config_flow.WakatimeApiClient", new=client_cls
    ):
        client = client_cls.return_value
        client.get_user_info = AsyncMock(return_value=const.USER_INFO)
        client.get_stats = AsyncMock(return_value=const.STATS)
        client.get_summary_today = AsyncMock(return_value=const.SUMMARY_TODAY)
        client.get_all_time_since_today = AsyncMock(return_value=const.ALL_TIME)
        client.get_goals = AsyncMock(return_value=const.GOALS)
        client.get_machine_names = AsyncMock(return_value=const.MACHINES)
        client.get_projects = AsyncMock(return_value=const.PROJECTS)
        yield client
```

- [ ] **Step 7: Commit**

```bash
git checkout -b feat/wakatime-full-integration
git add requirements.txt pytest.ini tests/__init__.py tests/const.py tests/conftest.py
git commit -m "test: add pytest scaffolding and WakaTime fixtures"
```

---

### Task 2: Rewrite `const.py`

**Files:**
- Modify: `custom_components/wakatime/const.py` (full rewrite)

- [ ] **Step 1: Replace the file contents**

Overwrite `custom_components/wakatime/const.py`:

```python
"""Constants for the Wakatime integration."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "wakatime"
NAME = "Wakatime"
ATTRIBUTION = "Data provided by WakaTime"
BASE_URL = "https://wakatime.com/api/v1"

# Config / options keys
CONF_SCAN_INTERVAL = "scan_interval"
CONF_STATS_RANGE = "stats_range"
CONF_ENABLED_SENSORS = "enabled_sensors"
CONF_MONITORED_GOALS = "monitored_goals"
CONF_MONITORED_PROJECTS = "monitored_projects"

# Defaults / bounds
DEFAULT_SCAN_INTERVAL = 30  # minutes
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 1440
DEFAULT_STATS_RANGE = "last_7_days"

STATS_RANGES = [
    "last_7_days",
    "last_30_days",
    "last_6_months",
    "last_year",
    "all_time",
]

# Icons
ICON_CODING = "mdi:code-braces"
ICON_LANGUAGE = "mdi:code-tags"
ICON_PROJECT = "mdi:folder"
ICON_EDITOR = "mdi:laptop"
ICON_OPERATING_SYSTEM = "mdi:monitor"
ICON_CATEGORY = "mdi:shape"
ICON_MACHINE = "mdi:desktop-tower"
ICON_DEPENDENCY = "mdi:package-variant"
ICON_TIME = "mdi:clock-outline"
ICON_AVERAGE = "mdi:chart-line"
ICON_TOTAL = "mdi:sigma"
ICON_PRODUCTIVITY = "mdi:trending-up"
ICON_BEST_DAY = "mdi:trophy"
ICON_GOAL = "mdi:bullseye-arrow"
ICON_COUNT = "mdi:counter"
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "from custom_components.wakatime import const; print(const.DOMAIN, const.BASE_URL)"`
Expected: `wakatime https://wakatime.com/api/v1`

- [ ] **Step 3: Commit**

```bash
git add custom_components/wakatime/const.py
git commit -m "refactor: expand and clean up constants"
```

---

### Task 3: Rewrite the API client (base64 fix + all endpoints)

**Files:**
- Modify: `custom_components/wakatime/api.py` (full rewrite)
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api.py`:

```python
"""Tests for the WakaTime API client."""

import base64

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.wakatime.api import (
    WakatimeApiAuthError,
    WakatimeApiClient,
    WakatimeApiError,
)
from custom_components.wakatime.const import BASE_URL


async def test_auth_header_is_base64(hass):
    """The Authorization header must contain the base64-encoded key."""
    session = async_get_clientsession(hass)
    client = WakatimeApiClient("waka_key", session)
    expected = base64.b64encode(b"waka_key").decode()
    assert client._headers["Authorization"] == f"Basic {expected}"


async def test_get_stats_success(hass, aioclient_mock):
    """A 200 response returns the parsed JSON body."""
    aioclient_mock.get(
        f"{BASE_URL}/users/current/stats/last_7_days",
        json={"data": {"total_seconds": 100}},
    )
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    data = await client.get_stats("last_7_days")
    assert data["data"]["total_seconds"] == 100


async def test_auth_error_raised_on_401(hass, aioclient_mock):
    """A 401 raises WakatimeApiAuthError."""
    aioclient_mock.get(f"{BASE_URL}/users/current", status=401)
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    with pytest.raises(WakatimeApiAuthError):
        await client.get_user_info()


async def test_generic_error_raised_on_500(hass, aioclient_mock):
    """A 500 raises WakatimeApiError (not auth)."""
    aioclient_mock.get(f"{BASE_URL}/users/current", status=500)
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    with pytest.raises(WakatimeApiError):
        await client.get_user_info()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_api.py -v`
Expected: FAIL — `ImportError`/`AttributeError` (no `WakatimeApiAuthError`, no base64 header, no `get_stats(range)`).

- [ ] **Step 3: Rewrite `api.py`**

Overwrite `custom_components/wakatime/api.py`:

```python
"""API client for Wakatime."""

from __future__ import annotations

import base64
import logging

import aiohttp
from homeassistant.util import dt as dt_util

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class WakatimeApiError(Exception):
    """Generic Wakatime API error."""


class WakatimeApiAuthError(WakatimeApiError):
    """Authentication error talking to the Wakatime API."""


class WakatimeApiClient:
    """API client for Wakatime."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._api_key = api_key
        self._session = session
        encoded = base64.b64encode(api_key.encode()).decode()
        self._headers = {"Authorization": f"Basic {encoded}"}

    async def _fetch_data(self, endpoint: str) -> dict:
        """Fetch and parse data from the API, raising typed errors."""
        url = f"{BASE_URL}/{endpoint}"
        try:
            async with self._session.get(url, headers=self._headers) as response:
                if response.status in (401, 403):
                    raise WakatimeApiAuthError(
                        f"Authentication failed ({response.status})"
                    )
                if response.status != 200:
                    raise WakatimeApiError(
                        f"Error fetching {endpoint}: HTTP {response.status}"
                    )
                return await response.json()
        except aiohttp.ClientError as err:
            raise WakatimeApiError(f"Connection error: {err}") from err

    async def get_user_info(self) -> dict:
        """Get the current user."""
        return await self._fetch_data("users/current")

    async def get_stats(self, stats_range: str = "last_7_days") -> dict:
        """Get aggregated stats for the given range."""
        return await self._fetch_data(f"users/current/stats/{stats_range}")

    async def get_summary_today(self) -> dict:
        """Get today's summary."""
        today = dt_util.now().strftime("%Y-%m-%d")
        return await self._fetch_data(
            f"users/current/summaries?start={today}&end={today}"
        )

    async def get_all_time_since_today(self) -> dict:
        """Get all-time totals."""
        return await self._fetch_data("users/current/all_time_since_today")

    async def get_goals(self) -> dict:
        """Get the user's goals."""
        return await self._fetch_data("users/current/goals")

    async def get_machine_names(self) -> dict:
        """Get the user's machines."""
        return await self._fetch_data("users/current/machine_names")

    async def get_projects(self) -> dict:
        """Get the user's projects."""
        return await self._fetch_data("users/current/projects")
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/test_api.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add custom_components/wakatime/api.py tests/test_api.py
git commit -m "fix: base64-encode WakaTime auth and expand API client"
```

---

### Task 4: Rewrite the coordinator

**Files:**
- Modify: `custom_components/wakatime/coordinator.py` (full rewrite — replaces blueprint version)

- [ ] **Step 1: Overwrite `coordinator.py`**

Overwrite `custom_components/wakatime/coordinator.py`:

```python
"""DataUpdateCoordinator for the Wakatime integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WakatimeApiAuthError, WakatimeApiClient, WakatimeApiError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_STATS_RANGE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_RANGE,
    DOMAIN,
    LOGGER,
)


class WakatimeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage fetching Wakatime data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WakatimeApiClient,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.entry = entry
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    @property
    def stats_range(self) -> str:
        """Return the configured stats range."""
        return self.entry.options.get(CONF_STATS_RANGE, DEFAULT_STATS_RANGE)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all endpoints in parallel and normalize the result."""
        try:
            async with async_timeout.timeout(30):
                (
                    user_info,
                    stats,
                    summary_today,
                    all_time,
                    goals,
                    machines,
                    projects,
                ) = await asyncio.gather(
                    self.client.get_user_info(),
                    self.client.get_stats(self.stats_range),
                    self.client.get_summary_today(),
                    self.client.get_all_time_since_today(),
                    self.client.get_goals(),
                    self.client.get_machine_names(),
                    self.client.get_projects(),
                )
        except WakatimeApiAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except WakatimeApiError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "user": user_info.get("data", {}),
            "stats": stats.get("data", {}),
            "summaries": summary_today.get("data", []),
            "all_time": all_time.get("data", {}),
            "goals": goals.get("data", []),
            "machines": machines.get("data", []),
            "projects": projects.get("data", []),
        }
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "from custom_components.wakatime.coordinator import WakatimeDataUpdateCoordinator; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add custom_components/wakatime/coordinator.py
git commit -m "refactor: parallel-fetch coordinator driven by options"
```

---

### Task 5: Rewrite the base entity and delete dead blueprint files

**Files:**
- Modify: `custom_components/wakatime/entity.py` (full rewrite)
- Delete: `custom_components/wakatime/switch.py`
- Delete: `custom_components/wakatime/binary_sensor.py`
- Delete: `custom_components/wakatime/data.py`

- [ ] **Step 1: Overwrite `entity.py`**

Overwrite `custom_components/wakatime/entity.py`:

```python
"""Base entity for the Wakatime integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME
from .coordinator import WakatimeDataUpdateCoordinator


class WakatimeEntity(CoordinatorEntity[WakatimeDataUpdateCoordinator]):
    """Base class for all Wakatime entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: WakatimeDataUpdateCoordinator) -> None:
        """Initialize the entity and its device."""
        super().__init__(coordinator)
        user = coordinator.data.get("user", {}) if coordinator.data else {}
        user_id = user.get("id") or coordinator.entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(user_id))},
            name=user.get("display_name") or user.get("username") or NAME,
            manufacturer="WakaTime",
            model="API",
            configuration_url="https://wakatime.com/dashboard",
        )
```

- [ ] **Step 2: Delete the dead blueprint files**

Run:

```bash
git rm custom_components/wakatime/switch.py custom_components/wakatime/binary_sensor.py custom_components/wakatime/data.py
```

Expected: three files removed.

- [ ] **Step 3: Verify no remaining references to deleted symbols**

Run: `grep -rn "IntegrationBlueprint\|binary_sensor\|switch" custom_components/wakatime/ || echo "clean"`
Expected: `clean` (no matches).

- [ ] **Step 4: Commit**

```bash
git add custom_components/wakatime/entity.py
git commit -m "refactor: rewrite base entity and remove dead blueprint files"
```

---

### Task 6: Rewrite `__init__.py` (runtime_data + options reload)

**Files:**
- Modify: `custom_components/wakatime/__init__.py` (full rewrite)
- Test: `tests/test_init.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_init.py`:

```python
"""Tests for setup and unload of the Wakatime integration."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.const import DOMAIN


async def _add_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "waka_key"},
        unique_id="user-123",
        title="dev@example.com",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_and_unload(hass, mock_api):
    """Entry loads, exposes the coordinator, then unloads cleanly."""
    entry = await _add_entry(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None
    assert entry.runtime_data.data["user"]["id"] == "user-123"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_init.py -v`
Expected: FAIL — current `__init__.py` doesn't set `runtime_data` and the coordinator import path differs.

- [ ] **Step 3: Overwrite `__init__.py`**

Overwrite `custom_components/wakatime/__init__.py`:

```python
"""The Wakatime integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WakatimeApiClient
from .coordinator import WakatimeDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]

type WakatimeConfigEntry = ConfigEntry[WakatimeDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> bool:
    """Set up Wakatime from a config entry."""
    client = WakatimeApiClient(entry.data[CONF_API_KEY], async_get_clientsession(hass))
    coordinator = WakatimeDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/test_init.py -v`
Expected: PASS (1 passed).

> Note: `test_init.py` exercises `sensor.py`, so this test only goes green once Task 8 is also done if run last. If running task-by-task, expect it to pass after Task 8. To unblock now, the platform forward to `sensor` must succeed — Task 8 provides `sensor.py`. If you are executing strictly in order, run `python -m pytest tests/test_init.py -v` again at the end of Task 8.

- [ ] **Step 5: Commit**

```bash
git add custom_components/wakatime/__init__.py tests/test_init.py
git commit -m "refactor: modern entry setup with runtime_data and options reload"
```

---

### Task 7: Config flow + Options flow

**Files:**
- Modify: `custom_components/wakatime/config_flow.py` (full rewrite)
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config_flow.py`:

```python
"""Tests for the Wakatime config and options flows."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResultType

from custom_components.wakatime.api import WakatimeApiAuthError
from custom_components.wakatime.const import DOMAIN


async def test_user_flow_success(hass):
    """A valid key creates an entry titled with the user's email."""
    with patch(
        "custom_components.wakatime.config_flow.WakatimeApiClient.get_user_info",
        return_value={"data": {"id": "user-123", "email": "dev@example.com"}},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "waka_key"}
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "dev@example.com"
    assert result2["data"][CONF_API_KEY] == "waka_key"


async def test_user_flow_invalid_auth(hass):
    """An auth error surfaces the invalid_auth message."""
    with patch(
        "custom_components.wakatime.config_flow.WakatimeApiClient.get_user_info",
        side_effect=WakatimeApiAuthError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "bad"}
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"


async def test_options_flow(hass, mock_api):
    """The options flow stores the chosen scan interval and range."""
    from homeassistant.const import CONF_API_KEY as _KEY
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.wakatime.const import (
        CONF_SCAN_INTERVAL,
        CONF_STATS_RANGE,
    )

    entry = MockConfigEntry(
        domain=DOMAIN, data={_KEY: "waka_key"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_SCAN_INTERVAL: 15, CONF_STATS_RANGE: "last_30_days"},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 15
    assert entry.options[CONF_STATS_RANGE] == "last_30_days"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: FAIL — no options flow, no `cannot_connect`/typed-error handling, current flow doesn't base64 or use the new exceptions.

- [ ] **Step 3: Overwrite `config_flow.py`**

Overwrite `custom_components/wakatime/config_flow.py`:

```python
"""Config and options flow for the Wakatime integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import WakatimeApiAuthError, WakatimeApiClient, WakatimeApiError
from .const import (
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_GOALS,
    CONF_MONITORED_PROJECTS,
    CONF_SCAN_INTERVAL,
    CONF_STATS_RANGE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_RANGE,
    DOMAIN,
    LOGGER,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    STATS_RANGES,
)


class WakatimeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial Wakatime config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the API-key step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = WakatimeApiClient(user_input[CONF_API_KEY], session)
            try:
                info = await client.get_user_info()
            except WakatimeApiAuthError:
                errors["base"] = "invalid_auth"
            except WakatimeApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception during Wakatime setup")
                errors["base"] = "unknown"
            else:
                data = info.get("data", {})
                if not data.get("id"):
                    errors["base"] = "invalid_auth"
                else:
                    await self.async_set_unique_id(str(data["id"]))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=data.get("email")
                        or data.get("username")
                        or "WakaTime",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return WakatimeOptionsFlow()


class WakatimeOptionsFlow(OptionsFlow):
    """Handle Wakatime options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Local import avoids a circular import at module load time.
        from .sensor import SENSOR_TYPES

        coordinator = self.config_entry.runtime_data
        data = coordinator.data if coordinator else {}
        options = self.config_entry.options

        sensor_keys = [d.key for d in SENSOR_TYPES]
        goal_titles = [
            g.get("title") or str(g.get("id")) for g in data.get("goals", [])
        ]
        project_names = [
            p["name"] for p in data.get("projects", []) if p.get("name")
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
                vol.Optional(
                    CONF_STATS_RANGE,
                    default=options.get(CONF_STATS_RANGE, DEFAULT_STATS_RANGE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=STATS_RANGES,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="stats_range",
                    )
                ),
                vol.Optional(
                    CONF_ENABLED_SENSORS,
                    default=options.get(CONF_ENABLED_SENSORS, sensor_keys),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=sensor_keys,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_MONITORED_GOALS,
                    default=options.get(CONF_MONITORED_GOALS, goal_titles),
                ): SelectSelector(
                    SelectSelectorConfig(options=goal_titles, multiple=True)
                ),
                vol.Optional(
                    CONF_MONITORED_PROJECTS,
                    default=options.get(CONF_MONITORED_PROJECTS, []),
                ): SelectSelector(
                    SelectSelectorConfig(options=project_names, multiple=True)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: PASS (3 passed). (The options-flow test depends on `sensor.py` from Task 8; if running strictly in order, re-run after Task 8.)

- [ ] **Step 5: Commit**

```bash
git add custom_components/wakatime/config_flow.py tests/test_config_flow.py
git commit -m "feat: typed config flow + options flow (interval, range, sensors, goals, projects)"
```

---

### Task 8: Rewrite `sensor.py` (declarative + dynamic sensors)

**Files:**
- Modify: `custom_components/wakatime/sensor.py` (full rewrite)
- Test: `tests/test_sensor.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_sensor.py`:

```python
"""Tests for the Wakatime sensors."""

from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_API_KEY: "waka_key"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_daily_total_sensor(hass, mock_api):
    """Daily total reflects today's summary grand_total."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_daily_total")
    assert state is not None
    assert state.state == "3600"


async def test_top_language_sensor(hass, mock_api):
    """Top language is the first language and lists the rest as attributes."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_top_language")
    assert state.state == "Python"
    assert state.attributes["breakdown"][0]["name"] == "Python"


async def test_range_total_and_all_time(hass, mock_api):
    """Range total and all-time total map to stats/all_time totals."""
    await _setup(hass)
    assert hass.states.get("sensor.dev_example_range_total").state == "36000"
    assert hass.states.get("sensor.dev_example_all_time_total").state == "360000"


async def test_goal_sensor_created(hass, mock_api):
    """A sensor is created for each goal."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_code_2_hrs_per_day")
    assert state is not None
    assert state.state == "success"
```

> Entity IDs follow `sensor.<device_name>_<entity_name>` slugified. Device name is `Dev Example` → `dev_example`. If your HA version slugifies differently, adjust the expected entity IDs after the first run (the test failure will print the actual IDs).

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_sensor.py -v`
Expected: FAIL — current `sensor.py` uses `hass.data[DOMAIN]` (removed), old keys, and lacks the new sensors.

- [ ] **Step 3: Overwrite `sensor.py`**

Overwrite `custom_components/wakatime/sensor.py`:

```python
"""Sensor platform for the Wakatime integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import WakatimeConfigEntry
from .const import (
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_GOALS,
    CONF_MONITORED_PROJECTS,
    ICON_AVERAGE,
    ICON_BEST_DAY,
    ICON_CATEGORY,
    ICON_CODING,
    ICON_COUNT,
    ICON_DEPENDENCY,
    ICON_EDITOR,
    ICON_GOAL,
    ICON_LANGUAGE,
    ICON_MACHINE,
    ICON_OPERATING_SYSTEM,
    ICON_PRODUCTIVITY,
    ICON_PROJECT,
    ICON_TOTAL,
)
from .coordinator import WakatimeDataUpdateCoordinator
from .entity import WakatimeEntity


def _today_seconds(data: dict) -> int:
    """Return today's coding seconds from the summaries list."""
    for day in data.get("summaries", []):
        grand_total = day.get("grand_total")
        if grand_total:
            return int(grand_total.get("total_seconds", 0))
    return 0


def _today_text(data: dict) -> str | None:
    """Return today's human-readable total."""
    for day in data.get("summaries", []):
        grand_total = day.get("grand_total")
        if grand_total:
            return grand_total.get("text")
    return None


def _top_name(data: dict, key: str) -> str:
    """Return the name of the top stats item for the given key."""
    items = data.get("stats", {}).get(key, [])
    return items[0].get("name", "Unknown") if items else "Unknown"


def _breakdown(data: dict, key: str) -> dict | None:
    """Return up to 10 items as a breakdown attribute."""
    items = data.get("stats", {}).get(key, [])
    if not items:
        return None
    return {
        "breakdown": [
            {
                "name": item.get("name"),
                "percent": item.get("percent"),
                "text": item.get("text"),
            }
            for item in items[:10]
        ]
    }


def _productivity(data: dict) -> str:
    """Map daily average seconds to a coarse productivity level."""
    avg = data.get("stats", {}).get("daily_average", 0)
    if avg > 14400:
        return "High"
    if avg > 7200:
        return "Medium"
    if avg > 0:
        return "Low"
    return "Unknown"


@dataclass(frozen=True, kw_only=True)
class WakatimeSensorEntityDescription(SensorEntityDescription):
    """Describes a Wakatime sensor with value/attribute extractors."""

    value_fn: Callable[[dict], StateType]
    attr_fn: Callable[[dict], dict | None] = lambda _data: None


SENSOR_TYPES: tuple[WakatimeSensorEntityDescription, ...] = (
    WakatimeSensorEntityDescription(
        key="daily_total",
        translation_key="daily_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL,
        icon=ICON_CODING,
        value_fn=_today_seconds,
        attr_fn=lambda d: {"human_readable": _today_text(d)},
    ),
    WakatimeSensorEntityDescription(
        key="range_total",
        translation_key="range_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_TOTAL,
        value_fn=lambda d: int(d.get("stats", {}).get("total_seconds", 0)),
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get("human_readable_total"),
            "range": d.get("stats", {}).get("range"),
        },
    ),
    WakatimeSensorEntityDescription(
        key="daily_average",
        translation_key="daily_average",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_AVERAGE,
        value_fn=lambda d: int(d.get("stats", {}).get("daily_average", 0)),
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get(
                "human_readable_daily_average"
            )
        },
    ),
    WakatimeSensorEntityDescription(
        key="all_time_total",
        translation_key="all_time_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon=ICON_TOTAL,
        value_fn=lambda d: int(d.get("all_time", {}).get("total_seconds", 0)),
        attr_fn=lambda d: {"human_readable": d.get("all_time", {}).get("text")},
    ),
    WakatimeSensorEntityDescription(
        key="best_day",
        translation_key="best_day",
        icon=ICON_BEST_DAY,
        value_fn=lambda d: d.get("stats", {}).get("best_day", {}).get("date")
        or "Unknown",
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get("best_day", {}).get("text"),
            "total_seconds": d.get("stats", {})
            .get("best_day", {})
            .get("total_seconds"),
        },
    ),
    WakatimeSensorEntityDescription(
        key="top_language",
        translation_key="top_language",
        icon=ICON_LANGUAGE,
        value_fn=lambda d: _top_name(d, "languages"),
        attr_fn=lambda d: _breakdown(d, "languages"),
    ),
    WakatimeSensorEntityDescription(
        key="top_project",
        translation_key="top_project",
        icon=ICON_PROJECT,
        value_fn=lambda d: _top_name(d, "projects"),
        attr_fn=lambda d: _breakdown(d, "projects"),
    ),
    WakatimeSensorEntityDescription(
        key="top_editor",
        translation_key="top_editor",
        icon=ICON_EDITOR,
        value_fn=lambda d: _top_name(d, "editors"),
        attr_fn=lambda d: _breakdown(d, "editors"),
    ),
    WakatimeSensorEntityDescription(
        key="top_os",
        translation_key="top_operating_system",
        icon=ICON_OPERATING_SYSTEM,
        value_fn=lambda d: _top_name(d, "operating_systems"),
        attr_fn=lambda d: _breakdown(d, "operating_systems"),
    ),
    WakatimeSensorEntityDescription(
        key="top_category",
        translation_key="top_category",
        icon=ICON_CATEGORY,
        value_fn=lambda d: _top_name(d, "categories"),
        attr_fn=lambda d: _breakdown(d, "categories"),
    ),
    WakatimeSensorEntityDescription(
        key="top_machine",
        translation_key="top_machine",
        icon=ICON_MACHINE,
        value_fn=lambda d: _top_name(d, "machines"),
        attr_fn=lambda d: _breakdown(d, "machines"),
    ),
    WakatimeSensorEntityDescription(
        key="top_dependency",
        translation_key="top_dependency",
        icon=ICON_DEPENDENCY,
        value_fn=lambda d: _top_name(d, "dependencies"),
        attr_fn=lambda d: _breakdown(d, "dependencies"),
    ),
    WakatimeSensorEntityDescription(
        key="languages_count",
        translation_key="languages_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_COUNT,
        value_fn=lambda d: len(d.get("stats", {}).get("languages", [])),
    ),
    WakatimeSensorEntityDescription(
        key="projects_count",
        translation_key="projects_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_COUNT,
        value_fn=lambda d: len(d.get("projects", [])),
    ),
    WakatimeSensorEntityDescription(
        key="active_machines",
        translation_key="active_machines",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MACHINE,
        value_fn=lambda d: len(d.get("machines", [])),
        attr_fn=lambda d: {
            "machines": [
                {"name": m.get("name"), "last_seen": m.get("last_seen_at")}
                for m in d.get("machines", [])
            ]
        },
    ),
    WakatimeSensorEntityDescription(
        key="productivity_level",
        translation_key="productivity_level",
        icon=ICON_PRODUCTIVITY,
        value_fn=_productivity,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WakatimeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wakatime sensors from a config entry."""
    coordinator = entry.runtime_data
    options = entry.options
    enabled = options.get(CONF_ENABLED_SENSORS)

    entities: list[SensorEntity] = [
        WakatimeSensor(coordinator, description)
        for description in SENSOR_TYPES
        if enabled is None or description.key in enabled
    ]

    monitored_goals = options.get(CONF_MONITORED_GOALS)
    for goal in coordinator.data.get("goals", []):
        title = goal.get("title") or str(goal.get("id"))
        if monitored_goals is None or title in monitored_goals:
            entities.append(WakatimeGoalSensor(coordinator, goal.get("id"), title))

    for name in options.get(CONF_MONITORED_PROJECTS) or []:
        entities.append(WakatimeProjectSensor(coordinator, name))

    async_add_entities(entities)


class WakatimeSensor(WakatimeEntity, SensorEntity):
    """A declarative Wakatime sensor."""

    entity_description: WakatimeSensorEntityDescription

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        description: WakatimeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the sensor state."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes, dropping None values."""
        if not self.coordinator.data:
            return None
        attrs = self.entity_description.attr_fn(self.coordinator.data)
        if not attrs:
            return None
        return {k: v for k, v in attrs.items() if v is not None}


class WakatimeGoalSensor(WakatimeEntity, SensorEntity):
    """A sensor representing a single WakaTime goal."""

    _attr_icon = ICON_GOAL

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        goal_id: str,
        title: str,
    ) -> None:
        """Initialize the goal sensor."""
        super().__init__(coordinator)
        self._goal_id = goal_id
        self._attr_name = title
        self._attr_unique_id = f"{coordinator.entry.entry_id}_goal_{goal_id}"

    def _goal(self) -> dict:
        for goal in self.coordinator.data.get("goals", []):
            if goal.get("id") == self._goal_id:
                return goal
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the goal's status."""
        goal = self._goal()
        return goal.get("average_status") or goal.get("status") or "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return goal metadata."""
        goal = self._goal()
        if not goal:
            return None
        return {
            "title": goal.get("title"),
            "type": goal.get("type"),
            "is_enabled": goal.get("is_enabled"),
            "target_seconds": goal.get("seconds"),
            "delta": goal.get("delta"),
            "range": goal.get("range"),
        }


class WakatimeProjectSensor(WakatimeEntity, SensorEntity):
    """A sensor tracking coding time for one project over the configured range."""

    _attr_icon = ICON_PROJECT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        project_name: str,
    ) -> None:
        """Initialize the project sensor."""
        super().__init__(coordinator)
        self._project_name = project_name
        slug = project_name.lower().replace(" ", "_")
        self._attr_name = f"Project {project_name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_project_{slug}"

    def _project(self) -> dict:
        for project in self.coordinator.data.get("stats", {}).get("projects", []):
            if project.get("name") == self._project_name:
                return project
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the project's coding seconds for the range."""
        return int(self._project().get("total_seconds", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return project metadata."""
        project = self._project()
        if not project:
            return None
        return {
            "human_readable": project.get("text"),
            "percent": project.get("percent"),
        }
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/test_sensor.py -v`
Expected: PASS (4 passed). If entity IDs differ, copy the actual IDs from the failure output into the test and re-run.

- [ ] **Step 5: Run the init test again (it depends on sensor.py)**

Run: `python -m pytest tests/test_init.py tests/test_config_flow.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/wakatime/sensor.py tests/test_sensor.py
git commit -m "feat: declarative sensor set plus dynamic goal and project sensors"
```

---

### Task 9: Diagnostics

**Files:**
- Create: `custom_components/wakatime/diagnostics.py`

- [ ] **Step 1: Create `diagnostics.py`**

Create `custom_components/wakatime/diagnostics.py`:

```python
"""Diagnostics support for the Wakatime integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from . import WakatimeConfigEntry

TO_REDACT = {CONF_API_KEY, "email", "ip", "id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: WakatimeConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "import custom_components.wakatime.diagnostics as d; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add custom_components/wakatime/diagnostics.py
git commit -m "feat: add redacted config-entry diagnostics"
```

---

### Task 10: Translations (en + pt-BR)

**Files:**
- Modify: `custom_components/wakatime/translations/en.json` (full rewrite)
- Modify: `custom_components/wakatime/translations/pt-BR.json` (full rewrite)

- [ ] **Step 1: Overwrite `en.json`**

Overwrite `custom_components/wakatime/translations/en.json`:

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Connect to Wakatime",
                "description": "Enter your Wakatime API key. You can find it in your Wakatime account settings.",
                "data": {
                    "api_key": "API Key"
                }
            }
        },
        "error": {
            "invalid_auth": "Invalid authentication",
            "cannot_connect": "Failed to connect to Wakatime",
            "unknown": "Unexpected error"
        },
        "abort": {
            "already_configured": "This Wakatime account is already configured"
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "Wakatime options",
                "data": {
                    "scan_interval": "Update interval (minutes)",
                    "stats_range": "Stats range",
                    "enabled_sensors": "Enabled sensors",
                    "monitored_goals": "Monitored goals",
                    "monitored_projects": "Monitored projects"
                }
            }
        }
    },
    "selector": {
        "stats_range": {
            "options": {
                "last_7_days": "Last 7 days",
                "last_30_days": "Last 30 days",
                "last_6_months": "Last 6 months",
                "last_year": "Last year",
                "all_time": "All time"
            }
        }
    },
    "entity": {
        "sensor": {
            "daily_total": { "name": "Daily Total" },
            "range_total": { "name": "Range Total" },
            "daily_average": { "name": "Daily Average" },
            "all_time_total": { "name": "All-Time Total" },
            "best_day": { "name": "Best Day" },
            "top_language": { "name": "Top Language" },
            "top_project": { "name": "Top Project" },
            "top_editor": { "name": "Top Editor" },
            "top_operating_system": { "name": "Top Operating System" },
            "top_category": { "name": "Top Category" },
            "top_machine": { "name": "Top Machine" },
            "top_dependency": { "name": "Top Dependency" },
            "languages_count": { "name": "Languages Count" },
            "projects_count": { "name": "Projects Count" },
            "active_machines": { "name": "Active Machines" },
            "productivity_level": { "name": "Productivity Level" }
        }
    }
}
```

- [ ] **Step 2: Overwrite `pt-BR.json`**

Overwrite `custom_components/wakatime/translations/pt-BR.json`:

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Conectar ao Wakatime",
                "description": "Digite sua chave de API Wakatime. Você a encontra nas configurações da sua conta Wakatime.",
                "data": {
                    "api_key": "Chave API"
                }
            }
        },
        "error": {
            "invalid_auth": "Autenticação inválida",
            "cannot_connect": "Falha ao conectar ao Wakatime",
            "unknown": "Erro inesperado"
        },
        "abort": {
            "already_configured": "Esta conta Wakatime já está configurada"
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "Opções do Wakatime",
                "data": {
                    "scan_interval": "Intervalo de atualização (minutos)",
                    "stats_range": "Período das estatísticas",
                    "enabled_sensors": "Sensores habilitados",
                    "monitored_goals": "Metas monitoradas",
                    "monitored_projects": "Projetos monitorados"
                }
            }
        }
    },
    "selector": {
        "stats_range": {
            "options": {
                "last_7_days": "Últimos 7 dias",
                "last_30_days": "Últimos 30 dias",
                "last_6_months": "Últimos 6 meses",
                "last_year": "Último ano",
                "all_time": "Desde o início"
            }
        }
    },
    "entity": {
        "sensor": {
            "daily_total": { "name": "Total diário" },
            "range_total": { "name": "Total do período" },
            "daily_average": { "name": "Média diária" },
            "all_time_total": { "name": "Total geral" },
            "best_day": { "name": "Melhor dia" },
            "top_language": { "name": "Linguagem principal" },
            "top_project": { "name": "Projeto principal" },
            "top_editor": { "name": "Editor principal" },
            "top_operating_system": { "name": "Sistema operacional principal" },
            "top_category": { "name": "Categoria principal" },
            "top_machine": { "name": "Máquina principal" },
            "top_dependency": { "name": "Dependência principal" },
            "languages_count": { "name": "Quantidade de linguagens" },
            "projects_count": { "name": "Quantidade de projetos" },
            "active_machines": { "name": "Máquinas ativas" },
            "productivity_level": { "name": "Nível de produtividade" }
        }
    }
}
```

- [ ] **Step 3: Validate JSON**

Run: `python -c "import json; json.load(open('custom_components/wakatime/translations/en.json')); json.load(open('custom_components/wakatime/translations/pt-BR.json')); print('valid')"`
Expected: `valid`

- [ ] **Step 4: Commit**

```bash
git add custom_components/wakatime/translations/en.json custom_components/wakatime/translations/pt-BR.json
git commit -m "feat: translations for new sensors and options flow (en, pt-BR)"
```

---

### Task 11: Manifest, README, and CI test workflow

**Files:**
- Modify: `custom_components/wakatime/manifest.json`
- Modify: `README.md`
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Update `manifest.json`**

Overwrite `custom_components/wakatime/manifest.json`:

```json
{
  "domain": "wakatime",
  "name": "Wakatime",
  "config_flow": true,
  "documentation": "https://github.com/hudsonbrendon/HA-wakatime",
  "issue_tracker": "https://github.com/hudsonbrendon/HA-wakatime/issues",
  "dependencies": [],
  "codeowners": [
    "@hudsonbrendon"
  ],
  "requirements": [],
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "loggers": ["custom_components.wakatime"],
  "version": "1.0.0"
}
```

- [ ] **Step 2: Update the README "Sensors" and "Configuration" sections**

In `README.md`, replace the `## Sensors` section (lines beginning `## Sensors` through the end of its bullet list) with:

```markdown
## Sensors

Static sensors (each can be toggled on/off in the integration **Options**):

- **Daily Total** — coding time today (seconds, attr: human-readable)
- **Range Total** — total coding time over the selected range
- **Daily Average** — average coding time per day over the range
- **All-Time Total** — total coding time ever recorded
- **Best Day** — date of your most productive day (attrs: total seconds, text)
- **Top Language / Project / Editor / Operating System / Category / Machine / Dependency** — each with a `breakdown` attribute listing the top 10
- **Languages Count / Projects Count / Active Machines** — counters
- **Productivity Level** — High / Medium / Low derived from your daily average

Dynamic sensors:

- **Goal sensors** — one per WakaTime goal you choose to monitor, state = goal status
- **Project sensors** — one per project you choose to monitor, state = coding time over the range

## Options

After adding the integration, open its **Configure** dialog to set:

- **Update interval** (5–1440 minutes, default 30)
- **Stats range** (last 7 days / 30 days / 6 months / year / all time)
- **Enabled sensors** (pick which static sensors to create)
- **Monitored goals** and **Monitored projects**

Changing options reloads the integration automatically.
```

- [ ] **Step 3: Fix the automations example entity id in the README**

In `README.md`, the automation example references `sensor.wakatime_daily_total`. Replace that line with the device-scoped id pattern:

```yaml
      entity_id: sensor.<your_wakatime_user>_daily_total
```

- [ ] **Step 4: Create the CI test workflow**

Create `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install --requirement requirements.txt
      - name: Run tests
        run: python -m pytest -v
```

- [ ] **Step 5: Commit**

```bash
git add custom_components/wakatime/manifest.json README.md .github/workflows/test.yml
git commit -m "docs: update README, bump manifest to 1.0.0, add CI test workflow"
```

---

### Task 12: Full suite + lint gate

**Files:** none (verification only)

- [ ] **Step 1: Run the whole test suite**

Run: `python -m pytest -v`
Expected: all tests pass (test_api: 4, test_init: 1, test_config_flow: 3, test_sensor: 4).

- [ ] **Step 2: Run lint**

Run: `./scripts/lint`
Expected: `ruff format` makes no changes (or only reformats); `ruff check . --fix` exits 0. Fix any reported violations, then re-run until clean.

- [ ] **Step 3: Confirm no leftover blueprint references anywhere**

Run: `grep -rn "IntegrationBlueprint\|integration_blueprint\|ATTRIBUTION" custom_components/wakatime/ | grep -v "const.py" || echo "clean"`
Expected: `clean` (the only `ATTRIBUTION` is the definition in `const.py` and its use in `entity.py`; adjust the grep if `entity.py` legitimately references it).

- [ ] **Step 4: Final commit (if lint changed anything)**

```bash
git add -A
git commit -m "chore: lint pass for WakaTime refactor"
```

---

## Self-Review

**Spec coverage:**
- *Maximum data* → Task 8 exposes daily/range/all-time totals, daily average, best day, top language/project/editor/OS/category/machine/dependency with breakdowns, counts, productivity, plus dynamic goal & project sensors (covers stats, summaries, all_time, goals, machines, projects endpoints). ✅
- *Configurable* → Task 7 options flow: scan interval, stats range, sensor selection, monitored goals, monitored projects; Task 6 reloads on change. ✅
- *Remove dead blueprint code* → Task 5 deletes `switch.py`/`binary_sensor.py`/`data.py`, rewrites `entity.py`/`coordinator.py`. ✅
- *Full test suite (TDD)* → Tasks 1,3,6,7,8 add tests written before implementation. ✅
- *Auth fix* (bonus, required for anything to work) → Task 3 base64. ✅

**Placeholder scan:** No TBD/TODO; every code step contains complete file contents or exact edits. Entity-ID assumptions in `test_sensor.py` are flagged with the recovery instruction (copy actual IDs from failure output) — this is a known HA slugify variance, not a placeholder.

**Type consistency:** `WakatimeApiClient` method names (`get_user_info`, `get_stats`, `get_summary_today`, `get_all_time_since_today`, `get_goals`, `get_machine_names`, `get_projects`) are identical across `api.py`, `coordinator.py`, and `conftest.py` mock. `WakatimeDataUpdateCoordinator(hass, entry, client)` signature matches its call in `__init__.py`. Normalized data keys (`user`, `stats`, `summaries`, `all_time`, `goals`, `machines`, `projects`) are produced in `coordinator._async_update_data` and consumed consistently in `sensor.py`, `entity.py`, `config_flow.py`, and `diagnostics.py`. `WakatimeConfigEntry` is defined in `__init__.py` and imported by `sensor.py`/`diagnostics.py`. Option keys (`CONF_*`) defined once in `const.py`.

**Known risks called out in-plan:** (1) test execution order — `test_init`/`test_config_flow` exercise `sensor.py`, so re-run them after Task 8; (2) HA entity-ID slugification may differ — adjust expected IDs after first run.
