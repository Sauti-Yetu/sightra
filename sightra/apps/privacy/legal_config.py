"""
Organisation contact details for legal pages and data requests.

Override via environment variables. Do not invent registration numbers.
"""

import os

OPERATOR_NAME = os.environ.get("SIGHTRA_OPERATOR_NAME", "Sauti Yetu Assistive Venture")
PRODUCT_NAME = os.environ.get("SIGHTRA_PRODUCT_NAME", "Sightra")
JURISDICTION = os.environ.get("SIGHTRA_JURISDICTION", "Kenya")
WEBSITE_URL = os.environ.get("SIGHTRA_WEBSITE_URL", "https://sightra.net")
CONTACT_EMAIL = os.environ.get("SIGHTRA_PRIVACY_EMAIL", "privacy@sightra.net")
DPO_CONTACT = os.environ.get("SIGHTRA_DPO_CONTACT", CONTACT_EMAIL)
POSTAL_ADDRESS = os.environ.get("SIGHTRA_POSTAL_ADDRESS", "").strip()
REGISTRATION_NUMBER = os.environ.get("SIGHTRA_REGISTRATION_NUMBER", "").strip()
FEEDBACK_EMAIL = os.environ.get("SIGHTRA_FEEDBACK_EMAIL", "support@sightra.net")
SUPPORT_EMAIL = os.environ.get("SIGHTRA_SUPPORT_EMAIL", FEEDBACK_EMAIL)
ODPC_URL = "https://www.odpc.go.ke/"
MINIMUM_AGE = 18


def postal_address_display() -> str:
    return POSTAL_ADDRESS or f"Available on request via {CONTACT_EMAIL}"


def registration_display() -> str:
    return REGISTRATION_NUMBER or "Not published; available on request from the operator"


def business_lines() -> dict:
    return {
        "operator_name": OPERATOR_NAME,
        "product_name": PRODUCT_NAME,
        "jurisdiction": JURISDICTION,
        "website_url": WEBSITE_URL,
        "contact_email": CONTACT_EMAIL,
        "dpo_contact": DPO_CONTACT,
        "support_email": SUPPORT_EMAIL,
        "feedback_email": FEEDBACK_EMAIL,
        "postal_address": postal_address_display(),
        "registration_number": registration_display(),
        "odpc_url": ODPC_URL,
        "minimum_age": MINIMUM_AGE,
    }
