"""Download native PDF set labels and retry failures using an isolated app."""

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]

from models import RebrickableSets, RebrickableThemes, User_Set, db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from pypdf import PdfReader  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402


def run():
    with TemporaryDirectory(prefix="brick-set-labels-") as directory:
        app = create_test_app()
        app.root_path = str(ROOT / "brick_manager")
        app.template_folder = "templates"
        app.config["OUTPUT_FOLDER"] = directory
        with app.app_context():
            db.create_all()
            db.session.add(RebrickableThemes(id=1, name="Dreamzzz"))
            db.session.flush()
            db.session.add(
                RebrickableSets(
                    set_num="71486-1",
                    name='Castle "A & B"',
                    year=2024,
                    theme_id=1,
                    num_parts=1805,
                )
            )
            db.session.flush()
            db.session.add(User_Set(id=187, set_num="71486-1", label_printed=False))
            db.session.commit()
        server = make_server("127.0.0.1", 0, app, threaded=True)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        errors = []
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    channel=os.environ.get("BRICK_BROWSER_CHANNEL"),
                    args=["--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"],
                )
                page = browser.new_page(accept_downloads=True)
                page.on("pageerror", lambda error: errors.append(str(error)))
                source = origin + "/set_maintain?box_id=187&label=not-printed"
                page.goto(source)
                row = page.locator("#set-box-187")
                feedback = row.locator(".set-label-feedback")
                checkbox = row.locator(".set-label-printed-checkbox")
                expect(checkbox).not_to_be_checked()

                # Errors must be visible, preserve status/context, and allow retry.
                page.route(
                    "**/set_maintain/generate_label",
                    lambda route: route.fulfill(
                        status=503,
                        content_type="application/json",
                        body='{"error":"Label service temporarily unavailable"}',
                    ),
                    times=1,
                )
                big = row.get_by_role("button", name="MB-4 PDF")
                big.click()
                expect(feedback).to_have_text("Label service temporarily unavailable")
                expect(feedback).to_have_class("set-label-feedback text-danger")
                expect(big).to_be_enabled()
                expect(checkbox).not_to_be_checked()
                assert page.url == source

                for size, title in (
                    ("MB-4", "MB-4 PDF"),
                    ("MB-1", "MB-1 PDF"),
                    ("BIG-BOX", "Big Box PDF"),
                ):
                    with page.expect_download() as pending:
                        row.get_by_role("button", name=title).click()
                    download = pending.value
                    assert download.suggested_filename == f"187_{size}.pdf"
                    assert download.failure() is None
                    artifact = Path(download.path()).read_bytes()
                    reader = PdfReader(BytesIO(artifact))
                    assert (
                        len(reader.pages) == {"MB-1": 1, "MB-4": 2, "BIG-BOX": 3}[size]
                    )
                    assert (
                        artifact == (Path(directory) / f"187_{size}.pdf").read_bytes()
                    )
                    expect(feedback).to_contain_text(
                        "PDF ready. Print at 100% / actual size."
                    )
                    expect(feedback).to_contain_text("Set image unavailable")
                    expect(checkbox).to_be_checked()
                    expect(row.locator(".set-label-status small")).to_have_text(
                        "Printed"
                    )
                    expect(row.get_by_role("button", name=title)).to_be_enabled()
                    assert page.url == source
                assert not errors, errors
                browser.close()
            with app.app_context():
                assert db.session.get(User_Set, 187).label_printed is True
            print(
                "PASS: all three PDF formats, page counts, image warning, visible failure/retry, filters and printed status"
            )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
            with app.app_context():
                db.session.remove()
                db.drop_all()
                db.engine.dispose()


if __name__ == "__main__":
    run()
