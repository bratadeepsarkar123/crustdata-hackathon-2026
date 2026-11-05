from typing import List, Tuple, Optional
from src.quotes.models import Quote
from .models import ProcurementPolicy, PolicyEvaluationResult
from .exceptions import ExceptionsQueue


class PolicyEvaluator:
    """Evaluates supplier quotes against buyer procurement policy rules (Step 6)."""

    def __init__(self, policy: Optional[ProcurementPolicy] = None):
        self.policy = policy or ProcurementPolicy()
        self.exceptions_queue = ExceptionsQueue()

    def evaluate_quote(
        self,
        quote: Quote,
        supplier: Optional[dict] = None
    ) -> PolicyEvaluationResult:
        """Evaluates a single quote against all procurement policy rules.
        
        Can accept an optional candidate/verified supplier dict from Person 2
        to inspect `headcount_total_internal` or other internal verification attributes.
        """
        checks = {}
        failure_reasons = []

        # 1. Budget Check (Critical acceptance check)
        effective_total = quote.total_price or (quote.unit_price * quote.quantity)
        if effective_total <= self.policy.budget_ceiling_usd:
            checks["budget_check"] = f"PASS (${effective_total:,.2f} <= ${self.policy.budget_ceiling_usd:,.2f})"
        else:
            diff = effective_total - self.policy.budget_ceiling_usd
            reason = (
                f"OVER_BUDGET: Total price ${effective_total:,.2f} exceeds "
                f"budget ceiling ${self.policy.budget_ceiling_usd:,.2f} by ${diff:,.2f}"
            )
            checks["budget_check"] = f"FAIL ({reason})"
            failure_reasons.append(reason)

        # 2. Lead Time / Delivery Deadline Check
        if quote.lead_time_days <= self.policy.required_delivery_days:
            checks["delivery_check"] = (
                f"PASS ({quote.lead_time_days} days <= {self.policy.required_delivery_days} days)"
            )
        else:
            reason = (
                f"LEAD_TIME_EXCEEDED: Lead time of {quote.lead_time_days} days exceeds "
                f"required delivery deadline of {self.policy.required_delivery_days} days"
            )
            checks["delivery_check"] = f"FAIL ({reason})"
            failure_reasons.append(reason)

        # 3. Vendor Headcount Check (read from _internal fields per handoff or Person 2 supplier object)
        internal_data = quote._internal or {}
        headcount = internal_data.get("headcount_total_internal")
        if headcount is None and supplier:
            headcount = supplier.get("headcount_total_internal")
        if headcount is None:
            headcount = internal_data.get("claimed_headcount")

        if headcount is not None:
            if headcount >= self.policy.min_vendor_headcount:
                checks["headcount_check"] = (
                    f"PASS ({headcount} >= {self.policy.min_vendor_headcount})"
                )
            else:
                reason = (
                    f"INSUFFICIENT_HEADCOUNT: Vendor headcount {headcount} is below "
                    f"minimum requirement of {self.policy.min_vendor_headcount}"
                )
                checks["headcount_check"] = f"FAIL ({reason})"
                failure_reasons.append(reason)
        else:
            checks["headcount_check"] = "SKIPPED (no headcount data in quote _internal)"

        # 4. Payment Terms Check
        if quote.payment_terms:
            if quote.payment_terms in self.policy.allowed_payment_terms:
                checks["payment_terms_check"] = f"PASS ({quote.payment_terms} allowed)"
            else:
                reason = (
                    f"UNAUTHORIZED_PAYMENT_TERMS: '{quote.payment_terms}' not in allowed "
                    f"terms {self.policy.allowed_payment_terms}"
                )
                checks["payment_terms_check"] = f"FAIL ({reason})"
                failure_reasons.append(reason)

        is_compliant = len(failure_reasons) == 0
        primary_exception = "; ".join(failure_reasons) if not is_compliant else None

        result = PolicyEvaluationResult(
            display_label=quote.display_label,
            is_compliant=is_compliant,
            total_price=effective_total,
            unit_price=quote.unit_price,
            lead_time_days=quote.lead_time_days,
            quote=quote,
            checks=checks,
            exception_reason=primary_exception,
            label="SIMULATED"
        )

        if not is_compliant:
            self.exceptions_queue.add_exception(
                display_label=quote.display_label,
                reason=primary_exception,
                quote=quote
            )

        return result

    def evaluate_all(
        self,
        quotes: List[Quote],
        suppliers: Optional[List[dict]] = None
    ) -> Tuple[List[PolicyEvaluationResult], ExceptionsQueue]:
        """Evaluates multiple quotes, ranks compliant ones, and routes non-compliant to exceptions.
        
        Optionally takes candidate/verified supplier records from Person 2 to link headcount or metadata.
        """
        supplier_map = {s.get("display_label"): s for s in (suppliers or []) if isinstance(s, dict)}
        results = [self.evaluate_quote(q, supplier=supplier_map.get(q.display_label)) for q in quotes]
        
        # Split compliant vs non-compliant
        compliant = [r for r in results if r.is_compliant]
        
        # Rank compliant: primary sort by total_price asc, secondary by lead_time_days asc
        compliant.sort(key=lambda r: (r.total_price, r.lead_time_days))
        for idx, r in enumerate(compliant, 1):
            r.rank = idx

        return results, self.exceptions_queue

