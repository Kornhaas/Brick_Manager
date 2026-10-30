#!/usr/bin/env python3
"""Store the configured Rebrickable API key in the local database."""

import os
import sys


def _api_key_from_environment():
    """Return the administrator-supplied API key without exposing it."""
    api_key = os.environ.get("REBRICKABLE_TOKEN", "").strip()
    if not api_key:
        raise ValueError("REBRICKABLE_TOKEN is not configured")
    return api_key


def configure_api_key(app, db, settings_model, ask=input, output=print):
    """Create or explicitly update the database API-key setting."""
    with app.app_context():
        output("Setting up Rebrickable API configuration...")
        api_key_config = settings_model.query.filter_by(
            key="rebrickable_api_key"
        ).first()

        if api_key_config:
            output("API key already configured")
            update = ask("Do you want to update it? (y/N): ").lower().strip()
            if update != "y":
                output("API key unchanged")
                return False

            api_key_config.value = _api_key_from_environment()
            api_key_config.updated_at = db.func.current_timestamp()
            db.session.commit()
            output("API key updated successfully!")
            return True

        api_key_config = settings_model(
            key="rebrickable_api_key",
            value=_api_key_from_environment(),
            encrypted=False,
            description="Rebrickable API key for accessing the API",
        )
        db.session.add(api_key_config)
        db.session.commit()
        output("API key configured successfully!")
        return True


def main():
    """Load the application and configure its Rebrickable API key."""
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from app import app, db
        from models import ConfigSettings

        configure_api_key(app, db, ConfigSettings)
    except (ImportError, ValueError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unable to configure API key: {type(error).__name__}", file=sys.stderr)
        return 1

    print("Configuration completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
