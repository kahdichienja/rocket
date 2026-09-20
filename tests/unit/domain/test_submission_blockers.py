from decimal import Decimal

from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    Invoice,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.enums import PaymentMechanism
from sha_claim.domain.identifiers import AttachmentId, ConsentToken, LineGuid
from sha_claim.domain.money import Money

CS = InterventionCode("SHA-08-006")
CONSULT = InterventionCode("SHA-12-001")


def intervention(
    code: InterventionCode,
    *,
    needs_preauth: bool = False,
    preauth_exists: bool = False,
    required_docs: tuple[str, ...] = (),
    state: str = "ACTIVE",
) -> ClaimIntervention:
    return ClaimIntervention(
        code,
        "",
        PaymentMechanism.CASE_BASED,
        needs_preauth,
        preauth_exists,
        state,
        required_preauth_document_types=required_docs,
    )


def line(code: InterventionCode, amount: str) -> ClaimLine:
    return ClaimLine(
        LineGuid("L"), code, "", "", Decimal(1), Money.kes(amount), Money.kes(amount), Money.kes(amount)
    )


def claim(**kw) -> VirtualClaim:  # type: ignore[no-untyped-def]
    base = dict(
        consent_token=ConsentToken("CR1-TOKEN12345"),
        guid=None,
        claim_id=1,
        workflow_state="OPEN",
        claim_auth_status="",
        service_type=None,
        patient_name="",
        member_number="",
        payer_name="",
        scheme_name="",
        currency="KES",
        total_amount=Money.kes(1000),
        net_amount=Money.kes(1000),
    )
    return VirtualClaim(**{**base, **kw})


def codes(c: VirtualClaim) -> list[str]:
    return [b.code for b in c.submission_blockers()]


def test_healthy_claim_has_no_blockers() -> None:
    c = claim(
        interventions=(intervention(CONSULT),),
        diagnoses=(ClaimDiagnosis(Icd11Code("1A00"), "", CONSULT),),
        invoices=(
            Invoice("i", None, "", "", "", Money.kes(1000), Money.kes(1000), lines=(line(CONSULT, "1000"),)),
        ),
    )
    assert c.submission_blockers() == ()


def test_no_lines_and_zero_total() -> None:
    assert codes(claim(is_zero=True, total_amount=Money.kes(0))) == ["NO_BILLING_LINES"]
    with_lines = claim(
        is_zero=True,
        invoices=(Invoice("i", None, "", "", "", Money.kes(0), Money.kes(0), lines=(line(CONSULT, "0"),)),),
    )
    assert codes(with_lines) == ["ZERO_TOTAL"]
    assert codes(claim(total_amount=Money.kes(0))) == ["ZERO_TOTAL"]
    assert "NEGATIVE_TOTAL" in codes(claim(is_negative=True))


def test_preauth_outstanding_only_for_active_interventions() -> None:
    c = claim(
        interventions=(
            intervention(CS, needs_preauth=True),
            intervention(CONSULT, needs_preauth=True, state="RETIRED"),
        )
    )
    blockers = c.submission_blockers()
    assert [b.code for b in blockers] == ["PREAUTH_OUTSTANDING"]
    assert blockers[0].intervention == CS
    assert "SHA-08-006" in str(blockers[0])
    assert codes(claim(interventions=(intervention(CS, needs_preauth=True, preauth_exists=True),))) == []


def test_missing_diagnosis_only_when_diagnoses_are_known() -> None:
    both = claim(
        interventions=(intervention(CS), intervention(CONSULT)),
        diagnoses=(ClaimDiagnosis(Icd11Code("JB0Z"), "", CS),),
    )
    assert [(b.code, b.intervention) for b in both.submission_blockers()] == [("NO_DIAGNOSIS", CONSULT)]
    # server returned no diagnosis list at all → we don't guess
    assert codes(claim(interventions=(intervention(CS),))) == []


def test_required_documents() -> None:
    c = claim(
        interventions=(
            intervention(
                CS, needs_preauth=True, preauth_exists=True, required_docs=("PREAUTH_FORM", "THEATRE_NOTES")
            ),
        ),
        attachments=(ClaimAttachment(AttachmentId("a"), "", "PREAUTH_FORM", CS),),
    )
    [b] = c.submission_blockers()
    assert b.code == "MISSING_DOCUMENTS" and "THEATRE_NOTES" in b.message and "PREAUTH_FORM" not in b.message
    # documents attached without an intervention scope count for every intervention
    ok = claim(
        interventions=(
            intervention(CS, needs_preauth=True, preauth_exists=True, required_docs=("PREAUTH_FORM",)),
        ),
        attachments=(ClaimAttachment(None, "", "PREAUTH_FORM", None),),
    )
    assert ok.submission_blockers() == ()


def test_all_interventions_retired() -> None:
    assert "NO_ACTIVE_INTERVENTIONS" in codes(claim(interventions=(intervention(CS, state="retired"),)))
