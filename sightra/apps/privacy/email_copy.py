"""Footer copy for any email Sightra sends. Always include an unsubscribe path."""

from apps.privacy import legal_config as lc


def unsubscribe_url(email: str = "") -> str:
    base = lc.WEBSITE_URL.rstrip("/") + "/legal/unsubscribe/"
    if email:
        return f"{base}?email={email}"
    return base


def transactional_footer_text(email: str = "") -> str:
    return (
        f"This message was sent by {lc.OPERATOR_NAME} regarding your {lc.PRODUCT_NAME} account. "
        "It is a service email, not marketing. "
        f"To stop optional product emails, unsubscribe: {unsubscribe_url(email)}. "
        f"Privacy: {lc.WEBSITE_URL.rstrip('/')}/legal/privacy-policy/ · "
        f"Contact: {lc.CONTACT_EMAIL}"
    )


def html_footer(email: str = "") -> str:
    unsub = unsubscribe_url(email)
    privacy = lc.WEBSITE_URL.rstrip("/") + "/legal/privacy-policy/"
    return (
        f'<p style="font-size:12px;color:#4b5563;line-height:1.5">'
        f"{lc.OPERATOR_NAME} · {lc.PRODUCT_NAME}<br>"
        f'<a href="{privacy}">Privacy Policy</a> · '
        f'<a href="{unsub}">Unsubscribe from optional emails</a><br>'
        f"Questions: {lc.CONTACT_EMAIL}"
        "</p>"
    )
