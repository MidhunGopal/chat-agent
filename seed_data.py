"""
Seed script – Populates the SQLite DataHub and ChromaDB vector store
with sample insurance data so the system works out of the box.
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from data.hub import get_data_hub
from vectorstore.store import get_vector_store
from utils.helpers import now_iso, new_id


def seed_users(hub):
    """Seed sample users (customers, agents, admin)."""
    users = [
        # Customers
        {
            "user_id": "CUS-001",
            "username": "john.smith",
            "password": "password123",
            "full_name": "John Smith",
            "role": "customer",
            "email": "john.smith@email.com",
        },
        {
            "user_id": "CUS-002",
            "username": "sarah.johnson",
            "password": "password123",
            "full_name": "Sarah Johnson",
            "role": "customer",
            "email": "sarah.johnson@email.com",
        },
        {
            "user_id": "CUS-003",
            "username": "robert.williams",
            "password": "password123",
            "full_name": "Robert Williams",
            "role": "customer",
            "email": "robert.williams@email.com",
        },
        {
            "user_id": "CUS-004",
            "username": "maria.garcia",
            "password": "password123",
            "full_name": "Maria Garcia",
            "role": "customer",
            "email": "maria.garcia@email.com",
        },
        {
            "user_id": "CUS-005",
            "username": "james.brown",
            "password": "password123",
            "full_name": "James Brown",
            "role": "customer",
            "email": "james.brown@email.com",
        },
        {
            "user_id": "CUS-006",
            "username": "david.lee",
            "password": "password123",
            "full_name": "David Lee",
            "role": "customer",
            "email": "david.lee@email.com",
        },
        {
            "user_id": "CUS-007",
            "username": "jennifer.chen",
            "password": "password123",
            "full_name": "Jennifer Chen",
            "role": "customer",
            "email": "jennifer.chen@email.com",
        },
        {
            "user_id": "CUS-008",
            "username": "michael.taylor",
            "password": "password123",
            "full_name": "Michael Taylor",
            "role": "customer",
            "email": "michael.taylor@email.com",
        },
        {
            "user_id": "CUS-009",
            "username": "emily.davis",
            "password": "password123",
            "full_name": "Emily Davis",
            "role": "customer",
            "email": "emily.davis@email.com",
        },
        # Agents
        {
            "user_id": "AGT-001",
            "username": "agent.wilson",
            "password": "agent123",
            "full_name": "Tom Wilson",
            "role": "agent",
            "email": "tom.wilson@insureco.com",
        },
        {
            "user_id": "AGT-002",
            "username": "agent.martinez",
            "password": "agent123",
            "full_name": "Lisa Martinez",
            "role": "agent",
            "email": "lisa.martinez@insureco.com",
        },
        # Admins
        {
            "user_id": "ADM-001",
            "username": "admin",
            "password": "admin123",
            "full_name": "System Administrator",
            "role": "admin",
            "email": "admin@insureco.com",
        },
    ]
    for u in users:
        u["created_at"] = now_iso()
        hub.upsert_user(u)
    print(f"  \u2713 Seeded {len(users)} users (customers, agents, admin)")


def seed_policies(hub):
    """Seed sample policies (ApplicationSystem)."""
    policies = [
        {
            "policy_id": "POL-001",
            "holder_name": "John Smith",
            "policy_type": "Term Life Insurance",
            "status": "active",
            "premium": 150.00,
            "start_date": "2024-01-15",
            "end_date": "2044-01-15",
            "details": {"coverage_amount": 500000, "beneficiary": "Jane Smith"},
            "customer_id": "CUS-001",
            "agent_id": "AGT-001",
        },
        {
            "policy_id": "POL-002",
            "holder_name": "Sarah Johnson",
            "policy_type": "Whole Life Insurance",
            "status": "active",
            "premium": 320.00,
            "start_date": "2023-06-01",
            "end_date": "2073-06-01",
            "details": {"coverage_amount": 1000000, "beneficiary": "Michael Johnson", "cash_value": 12500},
            "customer_id": "CUS-002",
            "agent_id": "AGT-001",
        },
        {
            "policy_id": "POL-003",
            "holder_name": "Robert Williams",
            "policy_type": "Universal Life Insurance",
            "status": "active",
            "premium": 450.00,
            "start_date": "2022-03-10",
            "end_date": "2072-03-10",
            "details": {"coverage_amount": 750000, "beneficiary": "Emily Williams", "cash_value": 35000},
            "customer_id": "CUS-003",
            "agent_id": "AGT-002",
        },
        {
            "policy_id": "POL-004",
            "holder_name": "Maria Garcia",
            "policy_type": "Health Insurance",
            "status": "active",
            "premium": 280.00,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "details": {"plan": "Gold PPO", "deductible": 1500, "out_of_pocket_max": 6000},
            "customer_id": "CUS-004",
            "agent_id": "AGT-002",
        },
        {
            "policy_id": "POL-005",
            "holder_name": "James Brown",
            "policy_type": "Auto Insurance",
            "status": "lapsed",
            "premium": 120.00,
            "start_date": "2024-07-01",
            "end_date": "2025-07-01",
            "details": {"vehicle": "2022 Toyota Camry", "coverage": "Full Coverage", "deductible": 500},
            "customer_id": "CUS-005",
            "agent_id": "AGT-001",
        },
    ]
    for p in policies:
        hub.upsert_policy(p)
    print(f"  ✓ Seeded {len(policies)} policies")


def seed_applications(hub):
    """Seed sample applications (UnderwritingSystem)."""
    applications = [
        {
            "application_id": "APP-001",
            "applicant_name": "David Lee",
            "application_type": "Term Life Insurance",
            "status": "under_review",
            "submitted_date": "2025-12-01",
            "underwriting_status": "in_progress",
            "details": {"requested_coverage": 500000, "age": 35},
            "customer_id": "CUS-006",
            "agent_id": "AGT-001",
        },
        {
            "application_id": "APP-002",
            "applicant_name": "Jennifer Chen",
            "application_type": "Whole Life Insurance",
            "status": "submitted",
            "submitted_date": "2025-12-15",
            "underwriting_status": "pending",
            "details": {"requested_coverage": 250000, "age": 28},
            "customer_id": "CUS-007",
            "agent_id": "AGT-002",
        },
        {
            "application_id": "APP-003",
            "applicant_name": "Michael Taylor",
            "application_type": "Health Insurance",
            "status": "approved",
            "submitted_date": "2025-11-20",
            "underwriting_status": "approved",
            "details": {"plan": "Silver HMO", "family_size": 4},
            "customer_id": "CUS-008",
            "agent_id": "AGT-001",
        },
        {
            "application_id": "APP-004",
            "applicant_name": "Emily Davis",
            "application_type": "Disability Insurance",
            "status": "pending_documents",
            "submitted_date": "2026-01-05",
            "underwriting_status": "pending",
            "details": {"occupation": "Software Engineer", "income": 120000},
            "customer_id": "CUS-009",
            "agent_id": "AGT-002",
        },
    ]
    for a in applications:
        hub.upsert_application(a)
    print(f"  ✓ Seeded {len(applications)} applications")


def seed_underwriting(hub):
    """Seed underwriting records (PolicyAdminSystem)."""
    records = [
        {
            "underwriting_id": "UW-001",
            "application_id": "APP-001",
            "status": "in_progress",
            "risk_score": 0.35,
            "notes": "Medical exam completed. Awaiting lab results. Applicant is a non-smoker with BMI 24.5.",
            "updated_at": "2025-12-10",
        },
        {
            "underwriting_id": "UW-002",
            "application_id": "APP-002",
            "status": "pending",
            "risk_score": None,
            "notes": "Application received. Pending initial review.",
            "updated_at": "2025-12-16",
        },
        {
            "underwriting_id": "UW-003",
            "application_id": "APP-003",
            "status": "approved",
            "risk_score": 0.15,
            "notes": "Standard risk. Approved at standard rates.",
            "updated_at": "2025-12-01",
        },
    ]
    for r in records:
        hub.upsert_underwriting(r)
    print(f"  ✓ Seeded {len(records)} underwriting records")


def seed_knowledge_base(hub, vs):
    """Seed knowledge base articles into both SQLite and ChromaDB."""
    articles = [
        {
            "article_id": "KB-001",
            "category": "application",
            "title": "How to Apply for Life Insurance",
            "content": (
                "To apply for life insurance with us, follow these steps:\n\n"
                "1. Choose your coverage type: Term Life, Whole Life, or Universal Life.\n"
                "2. Determine your coverage amount based on your needs (typically 10-15x annual income).\n"
                "3. Complete the online application form with personal and health information.\n"
                "4. Schedule a medical exam if required (for coverage over £100,000).\n"
                "5. Submit required documents: government ID, proof of income, medical records.\n"
                "6. Wait for underwriting review (typically 2-4 weeks).\n"
                "7. Review and accept the policy terms and premium quote.\n\n"
                "You can start your application online, through your advisor, or by calling our "
                "customer service line at 1-800-555-LIFE."
            ),
        },
        {
            "article_id": "KB-002",
            "category": "policy",
            "title": "Understanding Your Policy Coverage",
            "content": (
                "Your insurance policy provides financial protection for you and your loved ones. "
                "Key terms to understand:\n\n"
                "- **Premium**: The monthly or annual payment to keep your policy active.\n"
                "- **Coverage Amount (Face Value)**: The total amount paid out to beneficiaries.\n"
                "- **Beneficiary**: The person(s) designated to receive the death benefit.\n"
                "- **Cash Value**: (Whole/Universal Life only) The savings component that grows over time.\n"
                "- **Deductible**: (Health/Auto) The amount you pay before insurance kicks in.\n"
                "- **Riders**: Optional add-ons for additional coverage (e.g., waiver of premium, "
                "accidental death benefit).\n\n"
                "Review your policy documents carefully and contact your advisor with any questions."
            ),
        },
        {
            "article_id": "KB-003",
            "category": "underwriting",
            "title": "The Underwriting Process Explained",
            "content": (
                "Underwriting is the process by which we evaluate the risk of insuring you. "
                "Here's what to expect:\n\n"
                "1. **Application Review**: Our underwriters review your application details.\n"
                "2. **Medical Evaluation**: Depending on coverage, a medical exam or health "
                "questionnaire may be required.\n"
                "3. **Risk Assessment**: We evaluate factors including age, health, lifestyle, "
                "occupation, and family history.\n"
                "4. **Decision**: Your application will be approved at standard rates, approved "
                "with modified rates, or declined.\n\n"
                "**Timeline**: Most applications are processed within 2-4 weeks. Complex cases "
                "may take 4-8 weeks.\n\n"
                "**Status Updates**: You can check your application status online or by contacting "
                "your advisor. Statuses include: Pending, In Progress, Under Review, Approved, "
                "and Declined."
            ),
        },
        {
            "article_id": "KB-004",
            "category": "general",
            "title": "Types of Insurance We Offer",
            "content": (
                "We offer a comprehensive range of insurance products:\n\n"
                "**Life Insurance:**\n"
                "- Term Life: Affordable coverage for a specific period (10, 20, or 30 years)\n"
                "- Whole Life: Permanent coverage with a cash value component\n"
                "- Universal Life: Flexible premium and coverage with investment options\n\n"
                "**Health Insurance:**\n"
                "- HMO Plans: Lower cost, network-based care\n"
                "- PPO Plans: Greater flexibility in choosing providers\n"
                "- High-Deductible Health Plans (HDHP): Lower premiums with HSA eligibility\n\n"
                "**Other Products:**\n"
                "- Disability Insurance: Income protection if you can't work\n"
                "- Long-Term Care: Coverage for extended care needs\n"
                "- Annuities: Retirement income solutions\n\n"
                "Contact an advisor to find the right coverage for your needs."
            ),
        },
        {
            "article_id": "KB-005",
            "category": "policy",
            "title": "How to File a Claim",
            "content": (
                "To file an insurance claim, follow these steps:\n\n"
                "1. **Contact Us**: Call 1-800-555-CLAIM or log in to your account online.\n"
                "2. **Provide Policy Details**: Have your policy number and relevant information ready.\n"
                "3. **Submit Documentation**: Depending on the claim type:\n"
                "   - Life Insurance: Death certificate, beneficiary identification\n"
                "   - Health Insurance: Medical bills, explanation of benefits\n"
                "   - Auto Insurance: Police report, photos of damage, repair estimates\n"
                "4. **Claim Review**: Our claims team will review within 5-10 business days.\n"
                "5. **Settlement**: Once approved, payment is issued within 3-5 business days.\n\n"
                "Track your claim status online or contact your claims representative."
            ),
        },
        {
            "article_id": "KB-006",
            "category": "general",
            "title": "Contact Information and Office Hours",
            "content": (
                "We're here to help!\n\n"
                "**Customer Service**: 1-800-555-HELP (Mon-Fri 8am-8pm, Sat 9am-5pm)\n"
                "**Claims**: 1-800-555-CLAIM (24/7)\n"
                "**New Applications**: 1-800-555-APPLY (Mon-Fri 8am-6pm)\n\n"
                "**Online**: Log in at www.insureco.com/myaccount\n"
                "**Email**: support@insureco.com\n"
                "**Mail**: InsureCo, PO Box 12345, Insurance City, IC 54321\n\n"
                "**Advisor Portal**: advisors.insureco.com\n"
                "**Agent Hub**: agents.insureco.com"
            ),
        },
        {
            "article_id": "KB-007",
            "category": "document",
            "title": "Required Documents for Applications",
            "content": (
                "Depending on the type of insurance application, you may need to provide:\n\n"
                "**Life Insurance:**\n"
                "- Government-issued photo ID\n"
                "- Proof of income (pay stubs or tax returns)\n"
                "- Medical exam results (for coverage over £100,000)\n"
                "- Medical records (if pre-existing conditions)\n\n"
                "**Health Insurance:**\n"
                "- Government-issued photo ID\n"
                "- Proof of residence\n"
                "- Social Security numbers for all covered members\n\n"
                "**Disability Insurance:**\n"
                "- Government-issued photo ID\n"
                "- Proof of income\n"
                "- Employment verification letter\n"
                "- Medical records\n\n"
                "Upload documents securely through your online account or mail to our processing center."
            ),
        },
        {
            "article_id": "KB-008",
            "category": "policy",
            "title": "Policy Changes and Amendments",
            "content": (
                "You can make the following changes to your existing policy:\n\n"
                "- **Beneficiary Changes**: Update who receives your benefits\n"
                "- **Coverage Adjustments**: Increase or decrease coverage amounts\n"
                "- **Add/Remove Riders**: Modify optional coverage add-ons\n"
                "- **Payment Method**: Change how you pay your premiums\n"
                "- **Address Update**: Keep your contact information current\n"
                "- **Policy Loan**: (Whole/Universal Life) Borrow against your cash value\n\n"
                "Most changes can be made online or by contacting your advisor. "
                "Some changes may require additional underwriting."
            ),
        },
    ]

    # Store in SQLite
    for a in articles:
        a["created_at"] = now_iso()
        hub.add_knowledge_article(a)

    # Store in ChromaDB with chunking
    documents = [
        {"text": a["content"], "metadata": {"article_id": a["article_id"], "category": a["category"], "title": a["title"]}}
        for a in articles
    ]
    vs.add_documents_batch(documents, id_prefix="kb")

    print(f"  ✓ Seeded {len(articles)} knowledge base articles (SQLite + ChromaDB)")


def seed_all():
    """Run all seed functions."""
    print("🌱 Seeding databases...")
    hub = get_data_hub()
    vs = get_vector_store("insurance_knowledge")

    seed_users(hub)
    seed_policies(hub)
    seed_applications(hub)
    seed_underwriting(hub)
    seed_knowledge_base(hub, vs)

    print(f"\n✅ Seeding complete!")
    print(f"   SQLite DB: {hub.db_path}")
    print(f"   ChromaDB: {vs.persist_dir} ({vs.count()} vectors)")


if __name__ == "__main__":
    seed_all()
