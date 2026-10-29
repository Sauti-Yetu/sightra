from apps.privacy import legal_config as lc
from apps.privacy.constants import POLICY_EFFECTIVE_DATE, POLICY_VERSION


def legal_org(request):
    return {
        "legal": lc.business_lines(),
        "policy_version": POLICY_VERSION,
        "policy_effective_date": POLICY_EFFECTIVE_DATE,
    }
