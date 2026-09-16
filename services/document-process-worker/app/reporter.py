import httpx

from app.config import settings

TIMEOUT_SECONDS = 5.0


def report_status(document_id: str, status: str) -> None:
    url = f"{settings.document_service_url}/documents/{document_id}/status"

    try:
        response = httpx.patch(
            url,
            json={"status": status},
            timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()

        print(f"[{document_id}] status reported: {status}")

    except Exception as exc:
        # Best effort: a status report must never fail the actual processing.
        print(f"[{document_id}] could not report status '{status}': {exc}")
