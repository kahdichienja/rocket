"""End-to-end integration contract test of AsyncSmartClient workflows."""

from decimal import Decimal

import pytest
import respx

from smart_access import (
    AsyncSmartClient,
    ClaimCode,
    ClaimDiagnosis,
    ClaimInvoice,
    ClaimInvoiceLine,
    InvoiceNumber,
    LocationCode,
    MedicalAidCode,
    MemberNumber,
    PatientNumber,
    PaymentModifier,
    PaymentModifierType,
    PolicyId,
    PreauthItem,
    PreauthRequest,
    PreauthRule,
    SchemeCode,
    SessionId,
    SmartClaim,
    SmartSettings,
    SpId,
    VisitNumber,
)
from smart_access.domain.clinical import (
    AdmissionDetails,
    ClinicalRecord,
    ClinicalRequests,
    DischargeDetails,
    ItemMapping,
    PrescriptionItem,
)


@pytest.mark.asyncio
@respx.mock
async def test_full_smart_client_claim_flow() -> None:
    base = "https://data.smartapplicationsgroup.com/providerapi-dev"

    # 1. Auth endpoint
    respx.post(f"{base}/oauth/token").respond(
        status_code=200,
        json={"access_token": "valid-token", "token_type": "bearer", "expires_in": 3600},
    )

    # 2. Visit endpoints
    respx.get(f"{base}/api/visit").respond(
        status_code=200,
        json=[
            {
                "id": 12345,
                "patient_number": "PT000001",
                "sessionStatus": "PENDING",
                "sp_id": 678,
                "location_code": "100",
                "member_number": "8306004943-00",
            }
        ],
    )
    respx.put(f"{base}/api/visit/12345/visit-number/AC000001").respond(
        status_code=200,
        json={"code": "200", "message": "Session linked successfully", "response_type": "SUCCESS"},
    )

    # 3. Member endpoint
    respx.get(f"{base}/api/member").respond(
        status_code=200,
        json={
            "admit_id": "5678",
            "benefits": [
                {
                    "id": 154663,
                    "amount": 25000,
                    "claimable": True,
                    "pool_desc": "Outpatient Benefit",
                    "pool_nr": "3",
                    "sp_id": 678,
                }
            ],
            "global_id": "KE0002714501",
            "has_copay": True,
            "co_pay_amount": 500,
            "medicalaid_code": "MIC",
            "medicalaid_name": "Madson Insurance",
            "medicalaid_number": "8306004943-00",
            "medicalaid_scheme_code": "SAI",
            "medicalaid_scheme_name": "Smart Applications",
            "patient_surname": "Murphy",
            "patient_forenames": "James",
            "patient_dob": "1985-05-15",
        },
    )

    # 4. Rules check endpoint
    respx.post(f"{base}/api/sbb-rules").respond(
        status_code=200,
        json={
            "code": "200",
            "content": [
                {
                    "items": [
                        {
                            "item_code": "OPT00001",
                            "item_name": "optical frames",
                            "preauth_required": True,
                            "preauth_amount": 2000,
                            "preauth_rule_code": "RULE1",
                            "excluded": False,
                            "price_amount": 2000,
                        }
                    ]
                }
            ],
        },
    )

    # 5. Preauth request endpoint
    respx.post(f"{base}/api/preauth-request").respond(
        status_code=201,
        json={"preauth_request_id": "PR-998811", "visit_number": "AC000001", "status": "Approved"},
    )

    # 6. Claim posting endpoint
    respx.post(f"{base}/api/claims").respond(
        status_code=200,
        json={"code": "200", "message": "Claim posted successfully", "response_type": "SUCCESS"},
    )

    # 7. Claim status polling endpoint
    respx.get(f"{base}/api/claim-status").respond(
        status_code=200,
        json=[
            {
                "session_id": 12345,
                "claim_status": "Billed",
                "payer_name": "Madson Insurance",
                "patient_number": "PT000001",
                "visit_number": "AC000001",
                "scheme_name": "Smart Applications",
                "amount": 3000,
                "invoice_number": "INV-00000001",
            }
        ],
    )

    # 8. Close session endpoint
    respx.put(f"{base}/api/visit/12345/close-session").respond(
        status_code=200,
        json={"code": "200", "message": "Session closed successfully", "response_type": "SUCCESS"},
    )

    # Run the client flow
    settings = SmartSettings(
        provider_key="SKSP_6245",
        username="cashier1",
        password="secretpassword",
        base_url=base,
    )

    async with AsyncSmartClient(settings) as client:
        # Step 1: Check Auth
        assert await client.auth.check() is True

        # Step 2: Fetch Pending Session
        session = await client.sessions.fetch_pending("PT000001")
        assert session is not None
        assert session.session_id == 12345

        # Step 3: Link Session
        link_res = await session.link("AC000001")
        assert link_res.success is True
        assert session.session is not None
        assert session.session.is_active is True

        # Step 4: Get Members & Benefits
        members = await session.get_members()
        assert len(members) == 1
        member = members[0]
        assert member.full_name == "James Murphy"
        pool = member.find_pool(3)
        assert pool is not None
        assert pool.amount == Decimal("25000")

        # Step 5: Check Rules
        rule_res = await session.validate_rules(
            items=[("OPT00001", 1900, 3)],
            medical_aid_code="MIC",
            medical_aid_number="8306004943-00",
            medical_aid_plan="MIC.SAI",
            policy_id=1001065,
        )
        assert rule_res.any_preauth_required is True

        # Step 6: Submit Preauth
        preauth_req = PreauthRequest(
            admit_id=5678,
            condition_diagnosis_date="2025-01-21",
            copay_amount=Decimal(200),
            copay_type="1",
            diagnosis_code="B51|J00",
            doctor_name="DR. T.J. Peter",
            global_id=member.global_id,
            invoice_number=InvoiceNumber("INV-00000001"),
            medical_aid_code=member.medicalaid_code,
            medical_aid_number=member.medicalaid_number,
            medical_aid_plan="1001065.MIC2",
            patient_file_no=PatientNumber("PT000001"),
            phone_number="254718222009",
            policy_id=PolicyId(1001065),
            pool_number=3,
            location_code=LocationCode("100"),
            rules=(
                PreauthRule(
                    rule_code="RULE1",
                    request_amount=Decimal(2000),
                    items=(
                        PreauthItem(
                            item_code="OPT00001",
                            item_name="optical frames",
                            quantity=1,
                            unit_amount=Decimal(2000),
                            total_amount=Decimal(2000),
                        ),
                    ),
                ),
            ),
            treatment_cost_estimate=Decimal(2000),
            treatment_date="2025-01-21",
            visit_number=VisitNumber("AC000001"),
        )
        preauth_res = await session.submit_preauth(preauth_req)
        assert preauth_res.is_approved is True
        assert preauth_res.preauth_request_id == "PR-998811"

        # Step 7: Post Claim
        claim = SmartClaim(
            claim_code=ClaimCode("INV-00000001"),
            payer_code=MedicalAidCode("MIC"),
            payer_name="Madson Insurance",
            medicalaid_code=MedicalAidCode("MIC"),
            amount=Decimal(3000),
            gross_amount=Decimal(4000),
            batch_number="batch1",
            dispatch_date="2025-01-21 12:00:00",
            patient_number=PatientNumber("PT000001"),
            patient_name="James Murphy",
            location_code=LocationCode("100"),
            location_name="CASHIER1",
            scheme_code=SchemeCode("SAI"),
            scheme_name="Smart Applications",
            member_number=MemberNumber("8306004943-00"),
            visit_number=VisitNumber("AC000001"),
            session_id=SessionId(12345),
            visit_start="2025-01-21 09:00:00",
            visit_end="2025-01-21 11:00:00",
            sp_id=SpId(678),
            pool_number=3,
            diagnosis=(
                ClaimDiagnosis(
                    code="B51",
                    name="Plasmodium vivax malaria",
                ),
            ),
            invoices=(
                ClaimInvoice(
                    amount=Decimal(3000),
                    gross_amount=Decimal(4000),
                    invoice_date="2025-01-21 00:00:00",
                    invoice_number=InvoiceNumber("INV-00000001"),
                    invoice_ref_number=InvoiceNumber("INV-00000001"),
                    lines=(
                        ClaimInvoiceLine(
                            item_code="OPT00001",
                            item_name="optical frames",
                            quantity=1,
                            unit_price=Decimal(4000),
                            amount=Decimal(4000),
                            service_group="Optical",
                            charge_date="2025-01-21",
                            charge_time="10:00:00",
                        ),
                    ),
                ),
            ),
            payment_modifiers=(
                PaymentModifier(
                    type=PaymentModifierType.COPAY_FIXED,
                    amount=Decimal(500),
                    reference_number="recp001",
                ),
            ),
        )

        claim_res = await session.post_claim(claim)
        assert claim_res.success is True

        # Step 8: Poll Claim Status
        status = await session.check_claim_status("INV-00000001", "AC000001")
        assert status is not None
        assert status.is_billed is True

        # Step 9: Close Session
        close_res = await session.close()
        assert close_res.success is True


@pytest.mark.asyncio
@respx.mock
async def test_clinical_and_mapping_endpoints() -> None:
    base = "https://data.smartapplicationsgroup.com/providerapi-dev"

    respx.post(f"{base}/oauth/token").respond(
        status_code=200,
        json={"access_token": "valid-token", "token_type": "bearer", "expires_in": 3600},
    )
    respx.post(f"{base}/api/clinic-record").respond(status_code=200, json={"code": "200"})
    respx.post(f"{base}/api/requests").respond(status_code=200, json={"code": "200"})
    respx.post(f"{base}/api/admission").respond(status_code=200, json={"code": "200"})
    respx.post(f"{base}/api/discharge").respond(status_code=200, json={"code": "200"})
    respx.post(f"{base}/api/new-mapping").respond(status_code=200, json={"code": "200"})

    settings = SmartSettings(provider_key="KEY", username="user", password="pwd", base_url=base)
    async with AsyncSmartClient(settings) as client:
        # Clinical Record
        rec = ClinicalRecord(
            invoice_number=InvoiceNumber("INV-1"),
            member_number=MemberNumber("MEM-1"),
            patient_number=PatientNumber("PT-1"),
            session_id=SessionId(1),
            visit_number=VisitNumber("VN-1"),
            diagnosis=(ClaimDiagnosis(code="A01", name="Typhoid"),),
        )
        assert await client.clinical.post_record(rec) is True

        # Requests
        reqs = ClinicalRequests(
            member_number=MemberNumber("MEM-1"),
            patient_number=PatientNumber("PT-1"),
            visit_number=VisitNumber("VN-1"),
            prescription=(
                PrescriptionItem(
                    item_code="DRUG1",
                    item_name="Paracetamol",
                    dosage="1g",
                    duration="3 days",
                    frequency="TDS",
                    price=Decimal(10),
                    quantity=6,
                    amount=Decimal(60),
                ),
            ),
        )
        assert await client.clinical.post_requests(reqs) is True

        # Admission
        adm = AdmissionDetails(
            admission_number="ADM-01",
            visit_number=VisitNumber("VN-1"),
            patient_number=PatientNumber("PT-1"),
            admission_type="INHOUSE",
            admission_date="2025-01-21",
            admitting_doctor="Dr. Peter",
            admitting_doctor_type="RESIDENT",
            ward_name="Male Ward",
            ward_number="W1",
            bed_type="Standard",
            bed_number="B10",
            inpatient_number="IP-100",
            admission_notes="Routine admission",
        )
        assert await client.clinical.post_admission(adm) is True

        # Discharge
        dis = DischargeDetails(
            admission_number="ADM-01",
            patient_number=PatientNumber("PT-1"),
            discharge_date="2025-01-23",
            discharging_doctor="Dr. Peter",
            discharge_summary="Recovered",
        )
        assert await client.clinical.post_discharge(dis) is True

        # Item Mapping
        mapping = ItemMapping(
            group_code="GRP1",
            group_name="Consultation",
            item_code="CONS1",
            item_name="Specialist Consultation",
            provider_key="KEY",
        )
        assert await client.clinical.post_mapping(mapping) is True
