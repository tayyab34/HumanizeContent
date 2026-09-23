# plagiarism.py

import json
import os
from typing import Any, Dict, List, Optional

import requests


TURNITIN_API_URL = os.getenv(
    "TURNITIN_API_URL",
    "https://turnitin-api.herokuapp.com"
)

DEFAULT_TIMEOUT = 60


class TurnitinAPIError(Exception):
    """Raised when the Turnitin API request fails."""


class TurnitinAPIClient:
    """
    Client for the unofficial r2dev2/Turnitin-API.

    Supported operations:
        - Login
        - Get courses
        - Get assignments
        - Download submission
        - Submit document

    Note:
        The upstream API does not document a dedicated plagiarism
        percentage or AI-writing detection endpoint.
    """

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = TURNITIN_API_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.email = email.strip()
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.auth: Optional[Dict[str, Any]] = None

    # ---------------------------------------------------------
    # Internal request helper
    # ---------------------------------------------------------

    def _post_json(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Any:

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TurnitinAPIError(
                f"Could not connect to Turnitin API: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise TurnitinAPIError(
                f"Turnitin API returned HTTP "
                f"{response.status_code}: {response.text[:500]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise TurnitinAPIError(
                "Turnitin API returned an invalid JSON response."
            ) from exc

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------

    def login(self) -> Dict[str, Any]:

        if not self.email:
            raise TurnitinAPIError(
                "Turnitin email is required."
            )

        if not self.password:
            raise TurnitinAPIError(
                "Turnitin password is required."
            )

        result = self._post_json(
            "/login",
            {
                "email": self.email,
                "password": self.password,
            },
        )

        if not isinstance(result, dict):
            raise TurnitinAPIError(
                "Unexpected response received from Turnitin login."
            )

        if "auth" not in result:
            raise TurnitinAPIError(
                "Turnitin login failed: authentication information "
                "was not returned."
            )

        self.auth = result

        return result

    # ---------------------------------------------------------
    # AUTH CHECK
    # ---------------------------------------------------------

    def _require_auth(self):

        if not self.auth:
            raise TurnitinAPIError(
                "You must login to Turnitin before continuing."
            )

    # ---------------------------------------------------------
    # COURSES
    # ---------------------------------------------------------

    def get_courses(self) -> List[Dict[str, Any]]:

        self._require_auth()

        result = self._post_json(
            "/courses",
            self.auth,
        )

        if not isinstance(result, list):
            raise TurnitinAPIError(
                "Unexpected courses response from Turnitin."
            )

        return result

    # ---------------------------------------------------------
    # ASSIGNMENTS
    # ---------------------------------------------------------

    def get_assignments(
        self,
        course: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        self._require_auth()

        if not course:
            raise TurnitinAPIError(
                "A Turnitin course is required."
            )

        payload = dict(self.auth)

        payload["course"] = course

        result = self._post_json(
            "/assignments",
            payload,
        )

        if not isinstance(result, list):
            raise TurnitinAPIError(
                "Unexpected assignments response from Turnitin."
            )

        return result

    # ---------------------------------------------------------
    # DOWNLOAD
    # ---------------------------------------------------------

    def download_submission(
        self,
        assignment: Dict[str, Any],
        pdf: bool = False,
    ) -> bytes:

        self._require_auth()

        if not assignment:
            raise TurnitinAPIError(
                "A Turnitin assignment is required."
            )

        payload = dict(self.auth)

        payload["assignment"] = assignment
        payload["pdf"] = pdf

        url = f"{self.base_url}/download"

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TurnitinAPIError(
                f"Could not download the Turnitin submission: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise TurnitinAPIError(
                f"Turnitin download failed with HTTP "
                f"{response.status_code}."
            )

        return response.content

    # ---------------------------------------------------------
    # SUBMIT
    # ---------------------------------------------------------

    def submit_document(
        self,
        assignment: Dict[str, Any],
        filename: str,
        file_bytes: bytes,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:

        self._require_auth()

        if not assignment:
            raise TurnitinAPIError(
                "A Turnitin assignment is required."
            )

        if not filename:
            raise TurnitinAPIError(
                "A filename is required."
            )

        if not file_bytes:
            raise TurnitinAPIError(
                "The uploaded document is empty."
            )

        title = title or filename

        # The repository expects auth and assignment as JSON strings
        # inside multipart/form-data.
        form_data = {
            "auth": json.dumps(self.auth["auth"]),
            "assignment": json.dumps(assignment),
            "title": title,
            "filename": filename,
        }

        files = {
            "userfile": (
                filename,
                file_bytes,
            )
        }

        url = f"{self.base_url}/submit"

        try:
            response = self.session.post(
                url,
                data=form_data,
                files=files,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TurnitinAPIError(
                f"Could not submit document to Turnitin: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise TurnitinAPIError(
                f"Turnitin submission failed with HTTP "
                f"{response.status_code}: {response.text[:500]}"
            )

        try:
            result = response.json()
        except ValueError as exc:
            raise TurnitinAPIError(
                "Turnitin returned an invalid submission response."
            ) from exc

        if not isinstance(result, dict):
            raise TurnitinAPIError(
                "Unexpected Turnitin submission response."
            )

        return result


# =============================================================
# HIGH-LEVEL PLAGIARISM ANALYSIS
# =============================================================

def analyze_with_turnitin(
    email: str,
    password: str,
    filename: str,
    file_bytes: bytes,
    course_title: Optional[str] = None,
    assignment_title: Optional[str] = None,
    base_url: str = TURNITIN_API_URL,
) -> Dict[str, Any]:
    """
    Submit a document through the r2dev2 Turnitin API.

    Workflow:

        Login
          ↓
        Courses
          ↓
        Select Course
          ↓
        Assignments
          ↓
        Select Assignment
          ↓
        Submit Document

    Returns:
        Turnitin submission response.
    """

    client = TurnitinAPIClient(
        email=email,
        password=password,
        base_url=base_url,
    )

    # ---------------------------------------------------------
    # Login
    # ---------------------------------------------------------

    client.login()

    # ---------------------------------------------------------
    # Courses
    # ---------------------------------------------------------

    courses = client.get_courses()

    if not courses:
        raise TurnitinAPIError(
            "No Turnitin courses were returned."
        )

    selected_course = None

    if course_title:

        for course in courses:

            if course.get("title") == course_title:
                selected_course = course
                break

        if selected_course is None:
            # Also allow partial title matching.
            for course in courses:

                title = str(
                    course.get("title", "")
                ).lower()

                if course_title.lower() in title:
                    selected_course = course
                    break

    if selected_course is None:
        selected_course = courses[0]

    # ---------------------------------------------------------
    # Assignments
    # ---------------------------------------------------------

    assignments = client.get_assignments(
        selected_course
    )

    if not assignments:
        raise TurnitinAPIError(
            "No Turnitin assignments were returned "
            "for the selected course."
        )

    selected_assignment = None

    if assignment_title:

        for assignment in assignments:

            if assignment.get("title") == assignment_title:
                selected_assignment = assignment
                break

        if selected_assignment is None:

            for assignment in assignments:

                title = str(
                    assignment.get("title", "")
                ).lower()

                if assignment_title.lower() in title:
                    selected_assignment = assignment
                    break

    if selected_assignment is None:
        selected_assignment = assignments[0]

    # ---------------------------------------------------------
    # Submit
    # ---------------------------------------------------------

    result = client.submit_document(
        assignment=selected_assignment,
        filename=filename,
        file_bytes=file_bytes,
        title=filename,
    )

    # ---------------------------------------------------------
    # Normalize result
    # ---------------------------------------------------------

    return {
        "success": result.get("status") == 1,
        "status": result.get("status"),
        "uuid": result.get("uuid"),
        "file_name": result.get("file_name"),
        "file_size": result.get("file_size"),
        "page_count": result.get("page_count"),
        "word_count": result.get("word_count"),
        "char_count": result.get("char_count"),
        "image_url_stub": result.get("image_url_stub"),
        "course": selected_course,
        "assignment": selected_assignment,
        "raw_response": result,
    }


# =============================================================
# COMPATIBILITY FUNCTION
# =============================================================

def analyze_document(
    text: str = "",
    reference_files=None,
    use_gemini_embeddings: bool = False,
    embedding_model: Optional[str] = None,
    **kwargs,
):
    """
    Compatibility wrapper.

    This function intentionally does NOT claim that local semantic
    similarity is Turnitin plagiarism detection.

    It is kept so existing application code does not break.

    For actual Turnitin processing, use:

        analyze_with_turnitin(...)
    """

    word_count = len(
        text.split()
    ) if text else 0

    sentence_count = 0

    if text:
        sentence_count = sum(
            text.count(char)
            for char in [".", "!", "?"]
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
        "message": (
            "No Turnitin similarity percentage is calculated "
            "by this function. Use analyze_with_turnitin() "
            "to submit the document to Turnitin."
        ),
    }
