"""Statutory certificate wording.

Templates use the configured state name. The substantive wording follows
standard US notarial certificate language — verify against your state's
current Notary Public Reference Manual before use.
"""


def get_certificate_options(state: str = "your state") -> dict[str, str]:
    return {
        "Acknowledgment — Individual": f"""\
State of {state}
County of _______________

On this _____ day of _______________, 20_____, before me, the undersigned notary public, \
personally appeared _______________________________________________, known to me \
(or satisfactorily proven) to be the person whose name is subscribed to the within instrument, \
and acknowledged that he/she executed the same for the purposes therein contained.

In witness whereof I hereunto set my hand and official seal.

________________________________
Notary Public for {state}
My Commission Expires: _______________
""",

        "Acknowledgment — Representative / Corporate": f"""\
State of {state}
County of _______________

On this _____ day of _______________, 20_____, before me, the undersigned notary public, \
personally appeared _______________________________________________, known to me \
(or satisfactorily proven) to be the ______________________________ of \
_______________________________________________, and acknowledged that he/she, \
as such officer, executed the foregoing instrument for the purposes therein contained, \
as the act and deed of said entity, being duly authorized to do so.

In witness whereof I hereunto set my hand and official seal.

________________________________
Notary Public for {state}
My Commission Expires: _______________
""",

        "Jurat": f"""\
State of {state}
County of _______________

Subscribed and sworn to (or affirmed) before me on this _____ day of _______________, 20_____, \
by _______________________________________________.

________________________________
Notary Public for {state}
My Commission Expires: _______________
""",

        "Oath / Affirmation": f"""\
State of {state}
County of _______________

I, _______________________________________________, do solemnly swear (or affirm) that \
[the contents of the foregoing instrument / the statements made herein] are true and correct \
to the best of my knowledge and belief.

________________________________
[Signature of Affiant]

Sworn to (or affirmed) and subscribed before me on this _____ day of _______________, 20_____.

________________________________
Notary Public for {state}
My Commission Expires: _______________
""",
    }
