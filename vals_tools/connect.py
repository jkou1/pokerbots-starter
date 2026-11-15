"""Start a temporary connector using API-key management access, without logging secrets.

Temporary service credentials are revoked when the connector exits; no local auth config is changed.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ac2.harness.credentials import create_connector_credentials
from ac2.sdk import Client


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", default="vals-hackathon")
    p.add_argument("--upstream", default="http://127.0.0.1:8765")
    p.add_argument(
        "--credential-scope",
        choices=["project", "organization"],
        default="project",
        help="organization scope requires explicit authorization; credentials are revoked on exit",
    )
    p.add_argument("--transport", choices=["websocket", "https"], default="websocket")
    args = p.parse_args()
    client = Client(project=args.project)
    api = client._require_api()
    binding = client._project_id if args.credential_scope == "project" else None
    credentials = create_connector_credentials(api, binding)
    environment = os.environ | {
        "AC2_SERVICE_CLIENT_ID": credentials.client_id,
        "AC2_SERVICE_CLIENT_SECRET": credentials.client_secret,
    }
    print(
        f"Starting {args.credential_scope}-scoped temporary connector for {args.project}; credentials are kept in process memory.",
        flush=True,
    )
    try:
        subprocess.run(
            [
                str(Path(sys.executable).parent / "ac2"),
                "harness",
                "connect",
                "--project-id",
                client._project_id,
                "--upstream",
                args.upstream,
                "--transport",
                args.transport,
            ],
            env=environment,
            check=True,
        )
    finally:
        api.request(
            "DELETE", f"/auth/harness-connector-service-clients/{credentials.client_id}"
        )


if __name__ == "__main__":
    main()
