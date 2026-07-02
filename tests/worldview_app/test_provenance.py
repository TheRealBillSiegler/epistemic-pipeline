from epistemic_pipeline.worldview_app.provenance import canonicalize_origin


def test_urls_differing_only_by_tracking_and_case_collapse():
    a = canonicalize_origin("https://Blog.com/x?utm_source=tw&id=7#frag")
    b = canonicalize_origin("https://blog.com/x?id=7")
    assert a == b


def test_trailing_slash_is_normalized():
    assert canonicalize_origin("https://blog.com/x/") == canonicalize_origin("https://blog.com/x")


def test_doi_variants_collapse():
    assert canonicalize_origin("doi:10.1145/2700475") == canonicalize_origin("DOI:10.1145/2700475")
    assert canonicalize_origin("10.1145/2700475") == canonicalize_origin("doi:10.1145/2700475")


def test_vault_path_is_left_alone_and_distinct_sources_differ():
    assert canonicalize_origin("notes/ai-risk.md") == "notes/ai-risk.md"
    assert canonicalize_origin("notes/a.md") != canonicalize_origin("notes/b.md")


def test_arxiv_version_suffix_is_stripped():
    assert canonicalize_origin("arxiv:2301.00774v2") == canonicalize_origin("arxiv:2301.00774")


def test_arxiv_prefix_case_collapses():
    assert canonicalize_origin("arXiv:2301.00774") == canonicalize_origin("arxiv:2301.00774")


def test_http_and_https_collapse_to_one_root():
    assert canonicalize_origin("http://blog.com/x") == canonicalize_origin("https://blog.com/x")


def test_www_prefix_is_stripped():
    assert canonicalize_origin("https://www.blog.com/x") == canonicalize_origin("https://blog.com/x")


def test_spec_d1_http_www_tracking_example_collapses():
    # Spec D1's worked example: the same article over http + www + a tracking
    # param is one root.
    assert canonicalize_origin("http://www.blog.com/x?utm_source=tw") == canonicalize_origin(
        "https://blog.com/x"
    )


def test_dual_use_ref_param_is_not_stripped():
    # Bare "ref" can name the resource (e.g. a git ref), so distinct refs must
    # stay distinct roots rather than false-merging into one.
    assert canonicalize_origin("https://github.com/x?ref=main") != canonicalize_origin(
        "https://github.com/x?ref=dev"
    )
