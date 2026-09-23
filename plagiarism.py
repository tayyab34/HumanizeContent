import base64
import os
import time
import uuid
from typing import Any, Dict, Optional

import requests


# ============================================================
# CONFIGURATION
# ============================================================

COPYLEAKS_LOGIN_URL = (
    "https://id.copyleaks.com/v3/account/login/api"
)

COPYLEAKS_SCAN_URL = (
    "https://api.copyleaks.com/v3/scans/submit/file"
)

COPYLEAKS_RESULT_URL = (
    "https://api.copyleaks.com/v3/scans"
)

DEFAULT_TIMEOUT = 60

# For development/testing.
# Set to false for real Copyleaks scanning.
COPYLEAKS_SANDBOX = (
    os.getenv("COPYLEAKS_SANDBOX", "false").lower()
    == "true"
)


# ============================================================
# ERROR
# ============================================================

class CopyleaksError(Exception):
    """Raised when a Copyleaks request fails."""


# ============================================================
# COPYLEAKS CLIENT
# ============================================================

class CopyleaksClient:

    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.email = (
            email
            or os.getenv("COPYLEAKS_EMAIL")
            or ""
        ).strip()

        self.api_key = (
            api_key
            or os.getenv("COPYLEAKS_API_KEY")
            or ""
        ).strip()

        self.timeout = timeout

        self.access_token: Optional[str] = None

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def login(self) -> str:

        if not self.email:
            raise CopyleaksError(
                "COPYLEAKS_EMAIL is not configured."
            )

        if not self.api_key:
            raise CopyleaksError(
                "COPYLEAKS_API_KEY is not configured."
            )

        payload = {
            "email": self.email,
            "key": self.api_key,
        }

        try:
            response = requests.post(
                COPYLEAKS_LOGIN_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )

        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not connect to Copyleaks: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise CopyleaksError(
                "Copyleaks authentication failed. "
                f"HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()

        except ValueError as exc:
            raise CopyleaksError(
                "Copyleaks returned an invalid authentication response."
            ) from exc

        token = data.get("access_token")

        if not token:
            raise CopyleaksError(
                "Copyleaks authentication succeeded but "
                "no access token was returned."
            )

        self.access_token = token

        return token

    # ========================================================
    # AUTH HEADER
    # ========================================================

    def _headers(self) -> Dict[str, str]:

        if not self.access_token:
            self.login()

        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            ),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ========================================================
    # SUBMIT FILE
    # ========================================================

    def submit_file(
        self,
        filename: str,
        file_bytes: bytes,
        scan_id: Optional[str] = None,
        sandbox: Optional[bool] = None,
    ) -> str:

        if not filename:
            raise CopyleaksError(
                "Filename is required."
            )

        if not file_bytes:
            raise CopyleaksError(
                "The uploaded file is empty."
            )

        if not scan_id:
            scan_id = (
                f"document-"
                f"{uuid.uuid4().hex}"
            )

        if sandbox is None:
            sandbox = COPYLEAKS_SANDBOX

        encoded_file = base64.b64encode(
            file_bytes
        ).decode("utf-8")

        payload = {
            "base64": encoded_file,
            "filename": filename,

            "properties": {
                "sandbox": sandbox,

                # Webhook is intentionally omitted here.
                # We poll the result from Streamlit instead.
            },
        }

        url = (
            f"{COPYLEAKS_SCAN_URL}/"
            f"{scan_id}"
        )

        try:
            response = requests.put(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )

        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not submit file to Copyleaks: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise CopyleaksError(
                "Copyleaks file submission failed. "
                f"HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )

        return scan_id

    # ========================================================
    # GET SCAN STATUS
    # ========================================================

    def get_scan_status(
        self,
        scan_id: str,
    ) -> Any:

        url = (
            f"{COPYLEAKS_RESULT_URL}/"
            f"{scan_id}/status"
        )

        try:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )

        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not retrieve Copyleaks status: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise CopyleaksError(
                "Could not retrieve Copyleaks scan status. "
                f"HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            return response.json()

        except ValueError:
            return {
                "raw": response.text
            }

    # ========================================================
    # GET COMPLETED RESULT
    # ========================================================

    def get_result(
        self,
        scan_id: str,
    ) -> Any:

        url = (
            f"{COPYLEAKS_RESULT_URL}/"
            f"{scan_id}/result"
        )

        try:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )

        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not retrieve Copyleaks result: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise CopyleaksError(
                "Could not retrieve Copyleaks result. "
                f"HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )

        try:
            return response.json()

        except ValueError:
            return {
                "raw": response.text
            }

    # ========================================================
    # WAIT FOR RESULT
    # ========================================================

    def wait_for_result(
        self,
        scan_id: str,
        max_wait_seconds: int = 180,
        poll_seconds: int = 5,
    ) -> Dict[str, Any]:

        start_time = time.time()

        while (
            time.time() - start_time
            < max_wait_seconds
        ):

            status = self.get_scan_status(
                scan_id
            )

            if status:

                status_text = str(
                    status.get(
                        "status",
                        ""
                    )
                ).lower()

                # Copyleaks may expose different status
                # structures depending on the scan.
                if status_text in {
                    "completed",
                    "complete",
                    "finished",
                    "done",
                    "success",
                }:

                    result = self.get_result(
                        scan_id
                    )

                    return {
                        "scan_id": scan_id,
                        "status": status_text,
                        "result": result,
                    }

                if status_text in {
                    "failed",
                    "error",
                    "cancelled",
                }:

                    raise CopyleaksError(
                        f"Copyleaks scan failed: {status}"
                    )

            time.sleep(
                max(1, poll_seconds)
            )

        raise CopyleaksError(
            "Copyleaks scan did not complete "
            f"within {max_wait_seconds} seconds."
        )


# ============================================================
# GENERIC VALUE EXTRACTION
# ============================================================

def _find_values(
    data: Any,
    keywords,
    path="",
):
    """
    Recursively search Copyleaks responses.

    This keeps the parser tolerant of response
    structure changes.
    """

    results = []

    if isinstance(data, dict):

        for key, value in data.items():

            current_path = (
                f"{path}.{key}"
                if path
                else str(key)
            )

            key_lower = str(key).lower()

            if any(
                keyword in key_lower
                for keyword in keywords
            ):

                if isinstance(
                    value,
                    (int, float, str, bool),
                ):
                    results.append(
                        {
                            "field": current_path,
                            "value": value,
                        }
                    )

            results.extend(
                _find_values(
                    value,
                    keywords,
                    current_path,
                )
            )

    elif isinstance(data, list):

        for index, value in enumerate(data):

            results.extend(
                _find_values(
                    value,
                    keywords,
                    f"{path}[{index}]",
                )
            )

    return results


# ============================================================
# EXTRACT PLAGIARISM INFORMATION
# ============================================================

def extract_plagiarism_result(
    result: Any,
) -> Dict[str, Any]:

    matches = _find_values(
        result,
        [
            "match",
            "similarity",
            "plagiarism",
            "identical",
            "risk",
        ],
    )

    sources = _find_values(
        result,
        [
            "source",
            "url",
            "domain",
        ],
    )

    return {
        "matches": matches,
        "sources": sources,
        "raw": result,
    }


# ============================================================
# EXTRACT AI INFORMATION
# ============================================================

def extract_ai_result(
    result: Any,
) -> Dict[str, Any]:

    ai_values = _find_values(
        result,
        [
            "ai",
            "generated",
            "human",
            "classification",
        ],
    )

    return {
        "ai_values": ai_values,
        "raw": result,
    }


# ============================================================
# MAIN DOCUMENT ANALYSIS
# ============================================================

def analyze_with_copyleaks(
    filename: str,
    file_bytes: bytes,
    email: Optional[str] = None,
    api_key: Optional[str] = None,
    max_wait_seconds: int = 180,
    sandbox: Optional[bool] = None,
) -> Dict[str, Any]:

    client = CopyleaksClient(
        email=email,
        api_key=api_key,
    )

    # Authenticate
    client.login()

    # Create unique scan ID
    scan_id = (
        f"humanizecontent-"
        f"{uuid.uuid4().hex}"
    )

    # Submit
    client.submit_file(
        filename=filename,
        file_bytes=file_bytes,
        scan_id=scan_id,
        sandbox=sandbox,
    )

    # Wait
    response = client.wait_for_result(
        scan_id=scan_id,
        max_wait_seconds=max_wait_seconds,
    )

    raw_result = response.get(
        "result",
        {},
    )

    plagiarism = extract_plagiarism_result(
        raw_result
    )

    ai = extract_ai_result(
        raw_result
    )

    return {
        "success": True,

        "provider": "Copyleaks",

        "scan_id": scan_id,

        "status": response.get(
            "status"
        ),

        "filename": filename,

        "plagiarism": plagiarism,

        "ai_detection": ai,

        "raw_result": raw_result,
    }


# ============================================================
# EXISTING APP COMPATIBILITY
# ============================================================

def analyze_document(
    main_text: str,
    reference_files=None,
    use_gemini_embeddings=False,
    embedding_model=None,
    **kwargs,
):
    """
    Compatibility function for the existing Streamlit app.

    IMPORTANT:
    This function only performs the existing local-reference
    analysis interface.

    Copyleaks analysis requires the ORIGINAL FILE bytes,
    therefore call:

        analyze_with_copyleaks(...)

    from the Streamlit upload handler.
    """

    word_count = (
        len(main_text.split())
        if main_text
        else 0
    )

    sentence_count = 0

    if main_text:
        sentence_count = sum(
            main_text.count(character)
            for character in [".", "!", "?"]
        )

    reference_count = (
        len(reference_files)
        if reference_files
        else 0
    )

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "reference_count": reference_count,
        "reference_chunk_count": 0,
        "overall_similarity": None,
        "source_scores": [],
        "matches": [],
        "provider": "Copyleaks",
        "message": (
            "Use analyze_with_copyleaks() "
            "for Copyleaks plagiarism and AI detection."
        ),
    }
