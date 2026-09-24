import os
import uuid
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


COPYLEAKS_LOGIN_URL = "https://id.copyleaks.com/v3/account/login/api"
COPYLEAKS_SUBMIT_URL = "https://api.copyleaks.com/v3/scans/submit/file"


class CopyleaksError(Exception):
    """Raised when a Copyleaks API operation fails."""
    pass


class CopyleaksClient:
    def __init__(
        self,
        email=None,
        api_key=None,
        sandbox=None,
        timeout=60
    ):
        self.email = email or os.getenv("COPYLEAKS_EMAIL")
        self.api_key = api_key or os.getenv("COPYLEAKS_API_KEY")

        if sandbox is None:
            sandbox_value = os.getenv("COPYLEAKS_SANDBOX", "true")
            self.sandbox = sandbox_value.lower() in (
                "true",
                "1",
                "yes",
                "y"
            )
        else:
            self.sandbox = sandbox

        self.timeout = timeout
        self.access_token = None

    # ---------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------

    def login(self):
        """
        Authenticate using Copyleaks account email + API key.
        Returns temporary access token.
        """

        if not self.email:
            raise CopyleaksError(
                "COPYLEAKS_EMAIL is missing."
            )

        if not self.api_key:
            raise CopyleaksError(
                "COPYLEAKS_API_KEY is missing."
            )

        payload = {
            "email": self.email,
            "key": self.api_key
        }

        try:
            response = requests.post(
                COPYLEAKS_LOGIN_URL,
                json=payload,
                timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not connect to Copyleaks: {exc}"
            )

        if not response.ok:
            try:
                details = response.json()
            except Exception:
                details = response.text

            raise CopyleaksError(
                f"Copyleaks authentication failed "
                f"({response.status_code}): {details}"
            )

        data = response.json()

        token = data.get("access_token")

        if not token:
            raise CopyleaksError(
                "Copyleaks did not return an access_token."
            )

        self.access_token = token

        return token

    # ---------------------------------------------------------
    # HEADERS
    # ---------------------------------------------------------

    def _headers(self):
        if not self.access_token:
            self.login()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    # ---------------------------------------------------------
    # SCAN ID
    # ---------------------------------------------------------

    @staticmethod
    def create_scan_id():
        """
        Copyleaks accepts a unique scan ID.
        UUID hex is safe and <= 36 characters.
        """

        return uuid.uuid4().hex

    # ---------------------------------------------------------
    # SUBMIT FILE
    # ---------------------------------------------------------

    def submit_file(
        self,
        file_bytes,
        filename,
        webhook_url=None,
        enable_ai=True,
        enable_plagiarism=True,
        create_pdf_report=False
    ):
        """
        Submit a file to Copyleaks.

        Copyleaks requires the file to be Base64 encoded.

        IMPORTANT:
        Production scans are asynchronous and require a reachable
        HTTP/HTTPS webhook URL.
        """

        if not file_bytes:
            raise CopyleaksError(
                "The uploaded file is empty."
            )

        if not filename:
            filename = "uploaded_file.txt"

        scan_id = self.create_scan_id()

        encoded_file = base64.b64encode(
            file_bytes
        ).decode("utf-8")

        if webhook_url:
            status_webhook = webhook_url.rstrip("/") + \
                "/copyleaks/{STATUS}/" + scan_id
        else:
            status_webhook = (
                "https://example.com/copyleaks/{STATUS}/"
                + scan_id
            )

        properties = {
            "sandbox": self.sandbox,

            "webhooks": {
                "status": status_webhook
            },

            "scanning": {
                "internet": True
            },

            "aiGeneratedText": {
                "detect": bool(enable_ai)
            },

            "pdf": {
                "create": bool(create_pdf_report)
            }
        }

        if not enable_plagiarism:
            properties["scanning"]["internet"] = False

        payload = {
            "base64": encoded_file,
            "filename": filename,
            "properties": properties
        }

        url = (
            f"{COPYLEAKS_SUBMIT_URL}/"
            f"{scan_id}"
        )

        try:
            response = requests.put(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise CopyleaksError(
                f"Could not submit file to Copyleaks: {exc}"
            )

        if not response.ok:
            try:
                details = response.json()
            except Exception:
                details = response.text

            raise CopyleaksError(
                f"Copyleaks submission failed "
                f"({response.status_code}): {details}"
            )

        try:
            result = response.json()
        except Exception:
            result = {
                "raw_response": response.text
            }

        return {
            "scan_id": scan_id,
            "response": result
        }


# -------------------------------------------------------------
# DIRECT AI TEXT DETECTION
# -------------------------------------------------------------

def detect_ai_text(
    text,
    email=None,
    api_key=None,
    sandbox=None,
    explain=False
):
    """
    Direct Copyleaks AI text detection.

    This is useful when we already extracted text from
    PDF/DOCX/TXT/etc.

    Copyleaks requires at least 255 characters for this endpoint.
    """

    if not text or not text.strip():
        raise CopyleaksError(
            "No text was supplied for AI detection."
        )

    text = text.strip()

    if len(text) < 255:
        raise CopyleaksError(
            "Copyleaks AI text detection requires at least "
            "255 characters."
        )

    client = CopyleaksClient(
        email=email,
        api_key=api_key,
        sandbox=sandbox
    )

    token = client.login()

    scan_id = client.create_scan_id()

    url = (
        "https://api.copyleaks.com/v2/"
        f"writer-detector/{scan_id}/check"
    )

    payload = {
        "text": text,
        "sandbox": client.sandbox,
        "explain": explain
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=client.timeout
        )
    except requests.RequestException as exc:
        raise CopyleaksError(
            f"Could not connect to Copyleaks AI detector: {exc}"
        )

    if not response.ok:
        try:
            details = response.json()
        except Exception:
            details = response.text

        raise CopyleaksError(
            f"Copyleaks AI detection failed "
            f"({response.status_code}): {details}"
        )

    return response.json()


# -------------------------------------------------------------
# AI RESULT PARSER
# -------------------------------------------------------------

def parse_ai_result(result):
    """
    Parse the current Copyleaks AI detection response.

    Copyleaks returns:
        summary.human
        summary.ai

    These are proportions/summary values rather than a
    plagiarism score.
    """

    if not isinstance(result, dict):
        return {
            "ai_probability": None,
            "human_probability": None,
            "raw": result
        }

    summary = result.get("summary") or {}

    ai = summary.get("ai")
    human = summary.get("human")

    ai_percentage = None
    human_percentage = None

    if isinstance(ai, (int, float)):
        ai_percentage = ai * 100 if ai <= 1 else ai

    if isinstance(human, (int, float)):
        human_percentage = human * 100 if human <= 1 else human

    return {
        "ai_probability": ai_percentage,
        "human_probability": human_percentage,
        "raw": result
    }


# -------------------------------------------------------------
# SUBMISSION RESPONSE PARSER
# -------------------------------------------------------------

def parse_submission_result(result):
    """
    Extract information returned immediately by the
    Copyleaks submit endpoint.

    In production, final results arrive through the webhook.
    """

    if not isinstance(result, dict):
        return {
            "plagiarism_score": None,
            "ai_detected": None,
            "raw": result
        }

    results = result.get("results") or {}

    score = results.get("score") or {}

    plagiarism_score = score.get("aggregatedScore")

    enabled = (
        result.get("scannedDocument", {})
        .get("enabled", {})
    )

    ai_enabled = enabled.get("aiDetection")

    alerts = (
        result.get("notifications", {})
        .get("alerts", [])
    )

    ai_detected = False

    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        code = str(
            alert.get("code", "")
        ).lower()

        if "ai" in code:
            ai_detected = True
            break

    return {
        "plagiarism_score": plagiarism_score,
        "ai_detection_enabled": ai_enabled,
        "ai_detected": ai_detected,
        "raw": result
    }


# -------------------------------------------------------------
# MAIN FUNCTION USED BY APP
# -------------------------------------------------------------

def analyze_with_copyleaks(
    file_bytes,
    filename,
    webhook_url=None,
    sandbox=None
):
    """
    Submit an uploaded file to Copyleaks for:
        - plagiarism detection
        - AI-generated content detection
    """

    client = CopyleaksClient(
        sandbox=sandbox
    )

    submission = client.submit_file(
        file_bytes=file_bytes,
        filename=filename,
        webhook_url=webhook_url,
        enable_ai=True,
        enable_plagiarism=True,
        create_pdf_report=False
    )

    parsed = parse_submission_result(
        submission["response"]
    )

    return {
        "scan_id": submission["scan_id"],
        "plagiarism_score": parsed["plagiarism_score"],
        "ai_detection_enabled": parsed[
            "ai_detection_enabled"
        ],
        "ai_detected": parsed["ai_detected"],
        "response": submission["response"]
    }


# -------------------------------------------------------------
# BACKWARD COMPATIBILITY
# -------------------------------------------------------------

def analyze_document(
    file_bytes,
    filename,
    webhook_url=None,
    sandbox=None
):
    """
    Compatibility wrapper for the existing app.py.
    """

    return analyze_with_copyleaks(
        file_bytes=file_bytes,
        filename=filename,
        webhook_url=webhook_url,
        sandbox=sandbox
    )
