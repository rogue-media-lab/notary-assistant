"""Fee calculation and plain-text invoice generation (stdlib only)."""

from datetime import date

SC_FEE_PER_SIGNATURE = 5.00


def calculate_fee(num_signatures: int, travel_fee: float = 0.0) -> dict:
    """Return a fee breakdown dict."""
    notary_fee = round(num_signatures * SC_FEE_PER_SIGNATURE, 2)
    total = round(notary_fee + travel_fee, 2)
    return {
        "num_signatures": num_signatures,
        "fee_per_signature": SC_FEE_PER_SIGNATURE,
        "notary_fee": notary_fee,
        "travel_fee": round(travel_fee, 2),
        "total": total,
    }


def generate_invoice_text(
    invoice_number: str,
    invoice_date: str,
    client_name: str,
    document_type: str,
    fee_breakdown: dict,
    cfg: dict,
) -> str:
    """Generate a plain-text invoice string using stdlib only."""
    business_name = cfg.get("business_name", "Stamp and Certify Co")
    legal_entity = cfg.get("legal_entity", "Roberts and Associates LLC")
    notary_name = cfg.get("notary_name", "")
    county = cfg.get("county", "")

    lines = [
        "=" * 60,
        f"  {business_name}",
        f"  {legal_entity}",
    ]
    if county:
        lines.append(f"  {county} County, South Carolina")
    lines += [
        "=" * 60,
        "",
        f"  INVOICE #{invoice_number}",
        f"  Date:   {invoice_date}",
        f"  To:     {client_name}",
        "",
        "-" * 60,
        "  SERVICES RENDERED",
        "-" * 60,
        f"  Document Type:       {document_type or 'Notarial Services'}",
        f"  Number of Signatures: {fee_breakdown['num_signatures']}",
        f"  Notary Fee:          ${fee_breakdown['notary_fee']:.2f}",
        f"    (${fee_breakdown['fee_per_signature']:.2f} x {fee_breakdown['num_signatures']} signature(s))",
    ]

    if fee_breakdown["travel_fee"] > 0:
        lines.append(f"  Travel Fee:          ${fee_breakdown['travel_fee']:.2f}")

    lines += [
        "-" * 60,
        f"  TOTAL DUE:           ${fee_breakdown['total']:.2f}",
        "=" * 60,
        "",
        "  Thank you for your business!",
        "",
    ]

    if notary_name:
        lines += [
            f"  {notary_name}",
            f"  Notary Public, State of South Carolina",
        ]

    lines += [
        "",
        "  * Notary fees set per SC Code of Laws § 26-1-120",
        "=" * 60,
    ]

    return "\n".join(lines)
