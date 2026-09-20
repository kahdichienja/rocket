import pytest

from sha_claim.domain.attachments import MAX_ATTACHMENT_BYTES, Attachment
from sha_claim.domain.codes import DocumentType
from sha_claim.domain.consent import BiometricGuid, Otp


def test_otp_numeric_and_redacted() -> None:
    assert Otp(" 123456 ").code == "123456"
    assert "123456" not in repr(Otp("123456"))
    with pytest.raises(ValueError):
        Otp("12a4")


def test_biometric_guid_non_empty() -> None:
    assert BiometricGuid(" g ").value == "g"
    with pytest.raises(ValueError, match="BiometricGuid"):
        BiometricGuid(" ")


def test_attachment_invariants(tmp_path: pytest.TempPathFactory) -> None:
    with pytest.raises(ValueError):
        Attachment("a.pdf", b"", DocumentType.INVOICE)
    with pytest.raises(ValueError):
        Attachment("a.pdf", b"x" * (MAX_ATTACHMENT_BYTES + 1), DocumentType.INVOICE)
    a = Attachment("a.pdf", b"%PDF", DocumentType.INVOICE)
    assert a.size == 4


def test_attachment_from_path_guesses_type(tmp_path) -> None:  # type: ignore[no-untyped-def]
    f = tmp_path / "summary.pdf"
    f.write_bytes(b"%PDF-1.4")
    a = Attachment.from_path(f, DocumentType.DISCHARGE_SUMMARY)
    assert a.content_type == "application/pdf" and a.filename == "summary.pdf"
