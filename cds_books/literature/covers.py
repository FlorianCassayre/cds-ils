# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
#
# CDS Books is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Literature covers."""

import os
from functools import partial

from invenio_app_ils.literature.covers_builder import build_placeholder_urls


def is_record_with_cover(record):
    """Check if this type of record has cover."""
    if '$schema' in record:
        schema = record["$schema"]
        if schema.endswith("document-v1.0.0.json") or schema.endswith(
            "series-v1.0.0.json"
        ):
            return True
    return False


def has_already_cover(record):
    """Check if record has already valid cover in cover_metadata."""
    cover_metadata = record.get("cover_metadata", {})
    return cover_metadata.get("ISBN", False) or cover_metadata.get(
        "ISSN", False
    )


def preemptively_set_first_isbn_as_cover(sender, *args, **kwargs):
    """Update cover metadata of the record with identifier."""
    record = kwargs.get("record", {})
    if not is_record_with_cover(record):
        return

    if has_already_cover(record):
        return

    identifiers = record.get("identifiers")
    if not identifiers:
        return

    record.setdefault("cover_metadata", {})
    schema = record.get("$schema")

    if schema.endswith("series-v1.0.0.json"):
        for ident in identifiers:
            if ident["scheme"] == "ISSN":
                record["cover_metadata"]["ISSN"] = ident["value"]
                return

    for ident in identifiers:
        if ident["scheme"] == "ISBN":
            record["cover_metadata"]["ISBN"] = ident["value"]
            return


def build_syndetic_cover_urls(metadata):
    """Decorate literature with cover urls for all sizes."""
    client = os.environ.get("SYNDETIC_CLIENT")
    url = "https://secure.syndetics.com/index.aspx"

    cover_metadata = metadata.get("cover_metadata", {})

    issn = cover_metadata.get("ISSN", "")
    if issn:
        scheme = "ISSN"
        scheme_value = issn

    isbn = cover_metadata.get("ISBN", "")
    if isbn:
        scheme = "ISBN"
        scheme_value = isbn

    if issn or isbn:
        _url = "{url}?client={client}&{sheme}={value}/{size}.gif"
        partial_url = partial(
            _url.format,
            url=url,
            client=client,
            sheme=scheme,
            value=scheme_value,
        )
        return {
            "is_placeholder": False,
            "small": partial_url(size="SC"),
            "medium": partial_url(size="MC"),
            "large": partial_url(size="LC"),
        }
    return build_placeholder_urls()
