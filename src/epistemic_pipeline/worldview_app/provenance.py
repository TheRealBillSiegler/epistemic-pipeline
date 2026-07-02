"""Turn a raw source origin into a stable, canonical root id.

A "root" is where a piece of evidence ultimately comes from. Two records
that trace to the same root must produce the same id, so belief fusion can
group them and not double-count one source. This is deterministic by
design: it normalizes ids the caller supplies (a URL, a DOI, a vault
path); it never guesses provenance from a document's contents.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query parameters that identify a click, not the resource. Dropped so the
# same article shared two ways collapses to one root. Bare "ref" is left OUT
# on purpose: some sites use it to name the resource, not the click (GitHub
# ?ref=main vs ?ref=dev are different pages), so stripping it would merge
# distinct sources. "ref_src" (Twitter) is unambiguous tracking, so it stays.
_TRACKING = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
     "fbclid", "gclid", "ref_src"}
)
# A bare DOI, e.g. "10.1145/2700475".
_DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def canonicalize_origin(origin: str) -> str:
    """Return a stable root id for ``origin``.

    Example: ``https://Blog.com/x?utm_source=tw&id=7#frag`` and
    ``https://blog.com/x?id=7`` both return ``https://blog.com/x?id=7``.
    """
    o = origin.strip()
    low = o.lower()
    if low.startswith(("http://", "https://")):
        parts = urlsplit(o)
        # Fold http/https and a leading "www." so the same article fetched
        # either way is one root (spec D1). They almost always name the same
        # page; if they rarely do not, merging under-counts settledness --
        # the safe direction (spec section 3: fail toward not inflating).
        host = parts.netloc.lower().removeprefix("www.")
        path = parts.path.rstrip("/") or "/"
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit(("https", host, path, urlencode(kept), ""))
    if low.startswith("doi:"):
        return "doi:" + o[4:].strip().lower()
    if low.startswith("arxiv:"):
        # A version suffix (v1, v2, ...) is a content version, not a new
        # identity, so two versions of one preprint share a root.
        arxiv_id = re.sub(r"v\d+$", "", o[6:].strip().lower())
        return "arxiv:" + arxiv_id
    if _DOI.match(low):
        return "doi:" + low
    return o
