"""Pre-flight checklist items for notarial acts.

Ordered to match the actual workflow sequence:
  1. Review the document
  2. Verify the signer
  3. Select the act and certificate
  4. Perform the act
  5. Complete the certificate and seal
  6. Collect the fee
  7. Record in the journal
"""

PREFLIGHT_ITEMS: list[str] = [
    # --- Document review ---
    "Document is complete — no blank spaces left to be filled in after notarization",

    # --- Signer verification ---
    "Signer is physically present before me",
    "Signer's identity has been satisfactorily verified (valid government-issued photo ID examined)",
    "ID is current, not expired",
    "Signer appears to be of sound mind and acting of their own free will (no duress or incapacity)",
    "Signer is willingly signing — not coerced",

    # --- Act selection ---
    "Correct notarial act type has been selected (acknowledgment, jurat, oath, etc.)",
    "Appropriate certificate wording is attached or will be completed",

    # --- Perform the act ---
    "Signer has signed (or acknowledged their signature) in my presence",

    # --- Complete the certificate ---
    "I have completed and signed the notarial certificate",
    "My official stamp/seal has been applied legibly",

    # --- Fee ---
    "Fee charged does not exceed the statutory maximum per signature for my state",

    # --- Journal recording ---
    "ID information has been recorded in the journal",
    "Journal entry has been recorded for this act",
]
