import os
import uuid
import base64
import requests

from dotenv import load_dotenv

load_dotenv()


LOGIN_URL = "https://id.copyleaks.com/v3/account/login/api"
AI_URL = "https://api.copyleaks.com/v2/writer-detector"


class CopyleaksError(Exception):
    pass


class CopyleaksClient:

    def __init__(
        self,
        email=None,
        api_key=None,
        sandbox=True
    ):
        self.email = email or os.getenv("COPYLEAKS_EMAIL")
        self.api_key = api_key or os.getenv("COPYLEAKS_API_KEY")
        self.sandbox = sandbox
        self.access_token = None

    def login(self):

        if not self.email:
            raise CopyleaksError(
                "COPYLEAKS_EMAIL is missing."
            )

        if not self.api_key:
            raise CopyleaksError(
                "COPYLEAKS_API_KEY is missing."
            )

        response = requests.post(
            LOGIN_URL,
            json={
                "email": self.email,
                "key": self.api_key
            },
            timeout=60
        )

        if not response.ok:
            raise CopyleaksError(
                f"Copyleaks login failed "
                f"({response.status_code}): "
                f"{response.text}"
            )

        data = response.json()

        token = data.get("access_token")

        if not token:
            raise CopyleaksError(
                "Copyleaks did not return an access token."
            )

        self.access_token = token

        return token

    def headers(self):

        if not self.access_token:
            self.login()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }


def detect_ai_text(
    text,
    email=None,
    api_key=None,
    sandbox=True,
    explain=False
):

    if not text or not text.strip():
        raise CopyleaksError(
            "No text was supplied."
        )

    if len(text.strip()) < 255:
        raise CopyleaksError(
            "Copyleaks requires at least 255 characters "
            "for AI text detection."
        )

    client = CopyleaksClient(
        email=email,
        api_key=api_key,
        sandbox=sandbox
    )

    token = client.login()

    scan_id = uuid.uuid4().hex

    url = f"{AI_URL}/{scan_id}/check"

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
    "text": text,
    "sandbox": sandbox,
    "explain": explain
},
        timeout=60
    )

    if not response.ok:
        raise CopyleaksError(
            f"Copyleaks AI detection failed "
            f"({response.status_code}): "
            f"{response.text}"
        )

    return response.json()


def parse_ai_result(result):

    summary = result.get(
        "summary",
        {}
    )

    ai = summary.get("ai")
    human = summary.get("human")

    if isinstance(ai, (int, float)):
        ai_percentage = ai * 100
    else:
        ai_percentage = None

    if isinstance(human, (int, float)):
        human_percentage = human * 100
    else:
        human_percentage = None

    return {
        "ai_probability": ai_percentage,
        "human_probability": human_percentage,
        "raw": result
    }


def analyze_with_copyleaks(
    file_bytes,
    filename,
    webhook_url=None,
    sandbox=True
):

    if not file_bytes:
        raise CopyleaksError(
            "The uploaded file is empty."
        )

    client = CopyleaksClient(
        sandbox=sandbox
    )

    token = client.login()

    scan_id = uuid.uuid4().hex

    encoded = base64.b64encode(
        file_bytes
    ).decode("utf-8")

    if webhook_url:
        status_webhook = (
            webhook_url.rstrip("/")
            + "/copyleaks/{STATUS}/"
            + scan_id
        )
    else:
        status_webhook = (
            "https://example.com/copyleaks/"
            "{STATUS}/"
            + scan_id
        )

    payload = {
        "base64": encoded,
        "filename": filename,
        "properties": {
            "sandbox": sandbox,
            "webhooks": {
                "status": status_webhook
            },
            "scanning": {
                "internet": True
            },
            "aiGeneratedText": {
                "detect": True
            }
        }
    }

    url = (
        "https://api.copyleaks.com/v3/"
        f"scans/submit/file/{scan_id}"
    )

    response = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if not response.ok:
        raise CopyleaksError(
            f"Copyleaks file submission failed "
            f"({response.status_code}): "
            f"{response.text}"
        )

    try:
        data = response.json()
    except Exception:
        data = {}

    return {
        "scan_id": scan_id,
        "response": data
    }


def analyze_document(
    file_bytes,
    filename,
    webhook_url=None,
    sandbox=True
):

    return analyze_with_copyleaks(
        file_bytes=file_bytes,
        filename=filename,
        webhook_url=webhook_url,
        sandbox=sandbox
    )
