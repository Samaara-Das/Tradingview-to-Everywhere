"""Tests for tte/config.py — ComboConfig validation and YAML loading."""

import yaml

from tte.config import ComboConfig, _load_yaml


class TestComboConfigValidation:
    """Test ComboConfig.validate() method."""

    def test_validate_success_with_all_valid_fields(self, monkeypatch):
        """Valid configuration should return empty error list."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        errors = config.validate()
        assert errors == []

    def test_validate_fails_without_webhook_url(self, monkeypatch):
        """Missing webhook URL should produce validation error."""
        monkeypatch.delenv("COMBO_WEBHOOK_URL", raising=False)
        config = ComboConfig()
        config.webhook_url = ""
        errors = config.validate()
        assert len(errors) == 1
        assert "COMBO_WEBHOOK_URL is required" in errors[0]

    def test_validate_fails_with_batch_size_below_minimum(self, monkeypatch):
        """batch_size < 1 should fail validation."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        config.batch_size = 0
        errors = config.validate()
        assert any("batch_size must be between 1 and 4" in e for e in errors)

    def test_validate_fails_with_batch_size_above_maximum(self, monkeypatch):
        """batch_size > 4 should fail validation (TradingView hard limit)."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        config.batch_size = 5
        errors = config.validate()
        assert any("batch_size must be between 1 and 4" in e for e in errors)

    def test_validate_fails_with_recalc_wait_below_minimum(self, monkeypatch):
        """recalc_wait < 0.5 should fail validation."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        config.recalc_wait = 0.3
        errors = config.validate()
        assert any("recalc_wait must be at least 0.5 seconds" in e for e in errors)

    def test_validate_fails_with_maintenance_interval_below_minimum(self, monkeypatch):
        """maintenance_interval < 60 should fail validation."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        config.maintenance_interval = 30
        errors = config.validate()
        assert any("maintenance_interval must be at least 60 seconds" in e for e in errors)

    def test_validate_fails_with_invalid_bar_style(self, monkeypatch):
        """Invalid bar_style should fail validation."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        config.bar_style = "invalid_style"
        errors = config.validate()
        assert any("bar_style must be one of:" in e for e in errors)

    def test_validate_accepts_all_valid_bar_styles(self, monkeypatch):
        """All documented bar styles should pass validation."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        valid_styles = [
            "bar",
            "candle",
            "hollowCandle",
            "volCandles",
            "line",
            "lineWithMarkers",
            "stepline",
            "area",
            "hlcArea",
            "baseline",
            "column",
            "hilo",
            "ha",
            "renko",
            "pb",
            "kagi",
            "pnf",
            "range",
        ]
        for style in valid_styles:
            config = ComboConfig()
            config.bar_style = style
            errors = config.validate()
            assert not any("bar_style" in e for e in errors), f"Style '{style}' should be valid"

    def test_validate_accumulates_multiple_errors(self, monkeypatch):
        """Multiple validation errors should all be returned."""
        monkeypatch.delenv("COMBO_WEBHOOK_URL", raising=False)
        config = ComboConfig()
        config.webhook_url = ""
        config.batch_size = 10
        config.recalc_wait = 0.1
        config.maintenance_interval = 15
        config.bar_style = "invalid"
        errors = config.validate()
        assert len(errors) == 5


class TestComboConfigIsValid:
    """Test ComboConfig.is_valid() wrapper method."""

    def test_is_valid_returns_true_for_valid_config(self, monkeypatch):
        """is_valid() should return True when validate() returns empty list."""
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://example.com/webhook")
        config = ComboConfig()
        assert config.is_valid() is True

    def test_is_valid_returns_false_for_invalid_config(self, monkeypatch):
        """is_valid() should return False when validate() returns errors."""
        monkeypatch.delenv("COMBO_WEBHOOK_URL", raising=False)
        config = ComboConfig()
        config.webhook_url = ""
        assert config.is_valid() is False


class TestYAMLLoading:
    """Test YAML loading and default value handling."""

    def test_load_yaml_with_valid_file(self, temp_yaml_file, monkeypatch):
        """Valid YAML file should be loaded correctly."""
        # Write valid YAML
        yaml_content = {
            "chart": {"layout_name": "TestLayout", "chart_timeframe": "5 minutes"},
            "alerts": {"batch_size": 2},
        }
        with open(temp_yaml_file, "w") as f:
            yaml.dump(yaml_content, f)

        # Temporarily replace SETTINGS_FILE
        import tte.config

        original_settings = tte.config.SETTINGS_FILE
        try:
            tte.config.SETTINGS_FILE = temp_yaml_file
            loaded = _load_yaml()
            assert loaded["chart"]["layout_name"] == "TestLayout"
            assert loaded["chart"]["chart_timeframe"] == "5 minutes"
            assert loaded["alerts"]["batch_size"] == 2
        finally:
            tte.config.SETTINGS_FILE = original_settings

    def test_load_yaml_with_missing_file(self, monkeypatch, tmp_path):
        """Missing YAML file should return empty dict and log warning."""
        import tte.config

        nonexistent_file = tmp_path / "nonexistent.yaml"
        original_settings = tte.config.SETTINGS_FILE
        try:
            tte.config.SETTINGS_FILE = nonexistent_file
            loaded = _load_yaml()
            assert loaded == {}
        finally:
            tte.config.SETTINGS_FILE = original_settings

    def test_load_yaml_with_empty_file(self, temp_yaml_file, monkeypatch):
        """Empty YAML file should return empty dict."""
        # Write empty file
        with open(temp_yaml_file, "w") as f:
            f.write("")

        import tte.config

        original_settings = tte.config.SETTINGS_FILE
        try:
            tte.config.SETTINGS_FILE = temp_yaml_file
            loaded = _load_yaml()
            assert loaded == {}
        finally:
            tte.config.SETTINGS_FILE = original_settings

    def test_default_values_are_correct(self, monkeypatch):
        """Default values should match loaded configuration.

        Note: This test runs against the actual combo_settings.yaml file in the
        project directory, so it reflects production settings rather than code defaults.
        """
        monkeypatch.delenv("COMBO_WEBHOOK_URL", raising=False)
        config = ComboConfig()

        # Chart settings (from combo_settings.yaml)
        assert config.layout_name == "Screener"
        assert config.chart_timeframe == "1 minute"
        assert config.bar_style == "line"
        assert config.headless is True

        # Screener settings (from combo_settings.yaml)
        assert config.screener_shorttitle == "Screener"
        assert config.screener_name == "TTE Screener"

        # Alert settings (from combo_settings.yaml)
        assert config.batch_size == 3
        assert config.alert_creation_delay == 1.5
        assert config.recalc_wait == 1.5

        # Maintenance setting (from combo_settings.yaml)
        assert config.maintenance_interval == 300

        # Progress setting (from combo_settings.yaml)
        assert config.progress_file == "combo_progress.json"

    def test_env_var_overrides_yaml_for_webhook_url(self, temp_yaml_file, monkeypatch):
        """COMBO_WEBHOOK_URL env var should take precedence over YAML."""
        # Write YAML with webhook URL
        yaml_content = {"webhook": {"url": "https://yaml.example.com/hook"}}
        with open(temp_yaml_file, "w") as f:
            yaml.dump(yaml_content, f)

        # Set env var
        monkeypatch.setenv("COMBO_WEBHOOK_URL", "https://env.example.com/hook")

        import tte.config

        original_settings = tte.config.SETTINGS_FILE
        try:
            tte.config.SETTINGS_FILE = temp_yaml_file
            # Reload module to pick up new settings
            import importlib

            importlib.reload(tte.config)
            from tte.config import ComboConfig

            config = ComboConfig()
            assert config.webhook_url == "https://env.example.com/hook"
        finally:
            tte.config.SETTINGS_FILE = original_settings
            importlib.reload(tte.config)
