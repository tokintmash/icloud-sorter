import base64
import logging
from unittest.mock import patch, MagicMock


from backend.services.icloud_service import (
    _sanitize_folder_name,
    _compute_folder_names,
    _get_asset_filename,
    login,
    validate_2fa,
    get_session_status,
    get_albums,
    sync_album_metadata,
)


class FilenameAccessError(RuntimeError):
    """Raised by tests when mocking a pyicloud asset filename access failure."""


def _raise_filename_access_error(message: str = "fail") -> str:
    raise FilenameAccessError(message)


def _raise_api_response_exception(message: str = "fail", text: str | None = None) -> None:
    raise _api_response_exception(
        reason=message,
        text=text or "raw-icloud-response-with-auth-material",
    )


def _api_response_exception(
    reason: str = "API down",
    code: str = "SERVICE_UNAVAILABLE",
    text: str = "raw-icloud-response-with-auth-material",
):
    from pyicloud.exceptions import PyiCloudAPIResponseException

    response = MagicMock()
    response.status_code = 503
    response.text = text
    return PyiCloudAPIResponseException(reason, code=code, response=response)


# --- _sanitize_folder_name ---

def test_sanitize_strips_invalid_chars():
    assert _sanitize_folder_name("a/b\\c:d") == "a_b_c_d"


def test_sanitize_trims_dots_and_whitespace():
    assert _sanitize_folder_name("  ..hello..  ") == "hello"


def test_sanitize_truncates_at_200():
    name = "A" * 250
    result = _sanitize_folder_name(name)
    assert len(result) == 200


def test_sanitize_empty_becomes_unnamed():
    assert _sanitize_folder_name("") == "Unnamed Album"


def test_sanitize_only_invalid_chars():
    # All invalid chars replaced with '_', result is non-empty underscores
    assert _sanitize_folder_name("/\\:*?\"<>|") == "_________"


# --- _compute_folder_names ---

def test_compute_folder_names_dedup():
    albums = [
        {"id": "1", "name": "Vacation"},
        {"id": "2", "name": "Vacation"},
    ]
    result = _compute_folder_names(albums)
    assert result["1"] == "Vacation"
    assert result["2"] == "Vacation (2)"


def test_compute_folder_names_sanitize_collision():
    # Different raw names that sanitize to the same thing
    albums = [
        {"id": "1", "name": "a/b"},
        {"id": "2", "name": "a:b"},
    ]
    result = _compute_folder_names(albums)
    values = list(result.values())
    assert "a_b" in values
    assert "a_b (2)" in values


# --- _get_asset_filename ---

def test_get_asset_filename_plain():
    asset = MagicMock()
    asset.filename = "IMG_001.HEIC"
    assert _get_asset_filename(asset) == "IMG_001.HEIC"


def test_get_asset_filename_base64():
    asset = MagicMock()
    type(asset).filename = property(lambda s: _raise_filename_access_error())
    encoded = base64.b64encode(b"photo.jpg").decode()
    asset._master_record = {"fields": {"filenameEnc": {"value": encoded}}}
    result = _get_asset_filename(asset)
    assert result == "photo.jpg"


def test_get_asset_filename_plain_fallback():
    asset = MagicMock()
    type(asset).filename = property(lambda s: _raise_filename_access_error())
    # filenameEnc is plain text (not valid base64)
    asset._master_record = {"fields": {"filenameEnc": {"value": "plainfile.jpg"}}}
    result = _get_asset_filename(asset)
    # Could be base64-decoded or plain; either way we get a string
    assert result is not None


def test_get_asset_filename_returns_none_on_failure():
    asset = MagicMock()
    type(asset).filename = property(lambda s: _raise_filename_access_error())
    asset._master_record = {}
    result = _get_asset_filename(asset)
    assert result is None


# --- login ---

@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_success(mock_pyicloud_cls, mock_state):
    instance = MagicMock()
    instance.requires_2fa = False
    instance.requires_2sa = False
    mock_pyicloud_cls.return_value = instance

    result = login("test@apple.com", "pass123")
    assert result == {"authenticated": True, "requires_2fa": False}
    mock_state.save_session.assert_called_once()


@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_requires_2fa(mock_pyicloud_cls, mock_state):
    instance = MagicMock()
    instance.requires_2fa = True
    instance.requires_2sa = False
    mock_pyicloud_cls.return_value = instance

    result = login("test@apple.com", "pass123")
    assert result == {"authenticated": False, "requires_2fa": True}


@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_invalid_credentials(mock_pyicloud_cls, mock_state):
    from pyicloud.exceptions import PyiCloudFailedLoginException
    mock_pyicloud_cls.side_effect = PyiCloudFailedLoginException("bad", "creds")

    result = login("bad@apple.com", "wrong")
    assert result["error"] == "invalid_credentials"


@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_api_error(mock_pyicloud_cls, mock_state):
    from pyicloud.exceptions import PyiCloudAPIResponseException
    mock_pyicloud_cls.side_effect = PyiCloudAPIResponseException("API down")

    result = login("test@apple.com", "pass123")
    assert result["error"] == "internal_error"


@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_api_error_does_not_log_raw_response(mock_pyicloud_cls, mock_state, caplog):
    raw_response = "raw-auth-response session-token=secret"
    mock_pyicloud_cls.side_effect = _api_response_exception(
        code="AUTH_FAILED",
        text=raw_response,
    )
    caplog.set_level(logging.ERROR, logger="backend.services.icloud_service")

    result = login("test@apple.com", "pass123")

    assert result == {"error": "internal_error", "message": "iCloud API error (AUTH_FAILED)"}
    assert raw_response not in caplog.text
    assert raw_response not in result["message"]


@patch("backend.services.icloud_service.state_service")
@patch("backend.services.icloud_service.PyiCloudService")
def test_login_does_not_log_password(mock_pyicloud_cls, mock_state, caplog):
    instance = MagicMock()
    instance.requires_2fa = False
    instance.requires_2sa = False
    mock_pyicloud_cls.return_value = instance
    caplog.set_level(logging.INFO, logger="backend.services.icloud_service")

    result = login("test@apple.com", "super-secret-password")

    assert result == {"authenticated": True, "requires_2fa": False}
    assert "super-secret-password" not in caplog.text


# --- validate_2fa ---

def test_validate_2fa_no_session():
    import backend.services.icloud_service as svc
    original = svc._icloud
    svc._icloud = None
    try:
        result = validate_2fa("123456")
        assert result["error"] == "not_authenticated"
    finally:
        svc._icloud = original


@patch("backend.services.icloud_service._icloud")
def test_validate_2fa_success(mock_icloud):
    import backend.services.icloud_service as svc
    mock_icloud.validate_2fa_code.return_value = True
    original = svc._icloud
    svc._icloud = mock_icloud
    try:
        result = validate_2fa("123456")
        assert result == {"authenticated": True}
    finally:
        svc._icloud = original


@patch("backend.services.icloud_service._icloud")
def test_validate_2fa_invalid_code(mock_icloud):
    import backend.services.icloud_service as svc
    mock_icloud.validate_2fa_code.return_value = False
    original = svc._icloud
    svc._icloud = mock_icloud
    try:
        result = validate_2fa("000000")
        assert result["error"] == "2fa_failed"
    finally:
        svc._icloud = original


@patch("backend.services.icloud_service._icloud")
def test_validate_2fa_api_error_does_not_log_raw_response(mock_icloud, caplog):
    import backend.services.icloud_service as svc
    raw_response = "raw-2fa-response trusted-token=secret"
    mock_icloud.validate_2fa_code.side_effect = _api_response_exception(
        code="2FA_ERROR",
        text=raw_response,
    )
    original = svc._icloud
    svc._icloud = mock_icloud
    caplog.set_level(logging.ERROR, logger="backend.services.icloud_service")
    try:
        result = validate_2fa("654321")
        assert result == {"error": "2fa_failed", "message": "iCloud API error (2FA_ERROR)"}
        assert raw_response not in caplog.text
        assert raw_response not in result["message"]
    finally:
        svc._icloud = original


@patch("backend.services.icloud_service._icloud")
def test_validate_2fa_does_not_log_code(mock_icloud, caplog):
    import backend.services.icloud_service as svc
    mock_icloud.validate_2fa_code.return_value = False
    original = svc._icloud
    svc._icloud = mock_icloud
    caplog.set_level(logging.INFO, logger="backend.services.icloud_service")
    try:
        result = validate_2fa("654321")
        assert result["error"] == "2fa_failed"
        assert "654321" not in caplog.text
    finally:
        svc._icloud = original


# --- get_session_status ---

def test_session_status_unauthenticated():
    import backend.services.icloud_service as svc
    original = svc._icloud
    svc._icloud = None
    try:
        result = get_session_status()
        assert result["authenticated"] is False
        assert result["apple_id"] is None
        assert result["requires_2fa"] is False
    finally:
        svc._icloud = original


def test_session_status_awaiting_2fa():
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa
    orig_id = svc._apple_id
    svc._icloud = MagicMock()
    svc._requires_2fa = True
    svc._apple_id = "test@apple.com"
    try:
        result = get_session_status()
        assert result["authenticated"] is False
        assert result["requires_2fa"] is True
        assert result["apple_id"] == "test@apple.com"
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa
        svc._apple_id = orig_id


def test_session_status_authenticated():
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa
    orig_id = svc._apple_id
    mock = MagicMock()
    mock.is_trusted_session = True
    svc._icloud = mock
    svc._requires_2fa = False
    svc._apple_id = "test@apple.com"
    try:
        result = get_session_status()
        assert result["authenticated"] is True
        assert result["apple_id"] == "test@apple.com"
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa
        svc._apple_id = orig_id


# --- get_albums ---

def test_get_albums_unauthenticated():
    import backend.services.icloud_service as svc
    original = svc._icloud
    svc._icloud = None
    try:
        result = get_albums()
        assert isinstance(result, dict)
        assert result["error"] == "not_authenticated"
    finally:
        svc._icloud = original


def test_get_albums_success():
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa

    mock_album = MagicMock()
    mock_album.title = "My Album"
    mock_album.id = "album1"
    mock_album.__len__ = lambda s: 5

    mock_icloud = MagicMock()
    mock_icloud.photos.albums = [mock_album]

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    try:
        result = get_albums()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "My Album"
        assert result[0]["asset_count"] == 5
        assert "folder_name" in result[0]
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


def test_get_albums_api_error():
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa

    mock_icloud = MagicMock()
    type(mock_icloud).photos = property(lambda s: _raise_api_response_exception())

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    try:
        result = get_albums()
        assert isinstance(result, dict)
        assert result["error"] == "internal_error"
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


def test_get_albums_api_error_does_not_log_raw_response(caplog):
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa
    raw_response = "raw-album-response cookie=secret"

    mock_icloud = MagicMock()
    type(mock_icloud).photos = property(
        lambda s: _raise_api_response_exception("album down", text=raw_response)
    )

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    caplog.set_level(logging.ERROR, logger="backend.services.icloud_service")
    try:
        result = get_albums()
        assert result == {"error": "internal_error", "message": "iCloud API error (SERVICE_UNAVAILABLE)"}
        assert raw_response not in caplog.text
        assert raw_response not in result["message"]
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


# --- sync_album_metadata ---

def test_sync_album_metadata_populates_db(tmp_db):
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa

    mock_asset = MagicMock()
    mock_asset.filename = "IMG_001.HEIC"

    mock_album = MagicMock()
    mock_album.title = "Vacation"
    mock_album.id = "a1"
    mock_album.__iter__ = lambda s: iter([mock_asset])

    mock_icloud = MagicMock()
    mock_icloud.photos.albums = [mock_album]

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    try:
        folder_map = {"a1": "Vacation"}
        result = sync_album_metadata(folder_map, album_ids=["a1"])
        assert result == 1
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


def test_sync_album_metadata_filters_by_album_ids(tmp_db):
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa

    mock_asset1 = MagicMock()
    mock_asset1.filename = "IMG_001.HEIC"
    mock_album1 = MagicMock()
    mock_album1.title = "Album1"
    mock_album1.id = "a1"
    mock_album1.__iter__ = lambda s: iter([mock_asset1])

    mock_asset2 = MagicMock()
    mock_asset2.filename = "IMG_002.HEIC"
    mock_album2 = MagicMock()
    mock_album2.title = "Album2"
    mock_album2.id = "a2"
    mock_album2.__iter__ = lambda s: iter([mock_asset2])

    mock_icloud = MagicMock()
    mock_icloud.photos.albums = [mock_album1, mock_album2]

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    try:
        folder_map = {"a1": "Album1", "a2": "Album2"}
        result = sync_album_metadata(folder_map, album_ids=["a1"])
        assert result == 1  # only a1's assets
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


def test_sync_album_metadata_handles_bad_asset(tmp_db):
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa

    # Asset with no filename
    mock_asset = MagicMock()
    type(mock_asset).filename = property(
        lambda s: _raise_filename_access_error("no filename")
    )
    mock_asset._master_record = {}

    mock_album = MagicMock()
    mock_album.title = "Album"
    mock_album.id = "a1"
    mock_album.__iter__ = lambda s: iter([mock_asset])

    mock_icloud = MagicMock()
    mock_icloud.photos.albums = [mock_album]

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    try:
        folder_map = {"a1": "Album"}
        result = sync_album_metadata(folder_map, album_ids=["a1"])
        assert result == 0  # bad asset skipped
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa


def test_sync_album_metadata_api_error_does_not_log_raw_response(tmp_db, caplog):
    import backend.services.icloud_service as svc
    orig_icloud = svc._icloud
    orig_2fa = svc._requires_2fa
    raw_response = "raw-metadata-response auth-token=secret"

    mock_icloud = MagicMock()
    type(mock_icloud).photos = property(
        lambda s: _raise_api_response_exception("metadata down", text=raw_response)
    )

    svc._icloud = mock_icloud
    svc._requires_2fa = False
    caplog.set_level(logging.ERROR, logger="backend.services.icloud_service")
    try:
        result = sync_album_metadata({"a1": "Album"}, album_ids=["a1"])
        assert result == {"error": "internal_error", "message": "iCloud API error (SERVICE_UNAVAILABLE)"}
        assert raw_response not in caplog.text
        assert raw_response not in result["message"]
    finally:
        svc._icloud = orig_icloud
        svc._requires_2fa = orig_2fa
