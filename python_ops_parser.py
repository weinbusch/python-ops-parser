"""Module parser.py

Functions for parsing xml files retrieved from the ops register service

"""
import datetime
import xml.etree.ElementTree as ET

from operator import itemgetter

ns = {
    "ops": "http://ops.epo.org",
    "reg": "http://www.epo.org/register",
}


def xml_tree(xmlstring):
    return ET.fromstring(xmlstring)


def world_patent_data(root):
    return {
        "register_search": register_search(root.find("ops:register-search", ns)),
    }


def register_search(node):
    range_node = node.find("ops:range", ns)
    query_range = (int(range_node.attrib["begin"]), int(range_node.attrib["end"]))
    return {
        "register_documents": [
            register_document(x)
            for x in node.findall("reg:register-documents/reg:register-document", ns)
        ],
        "count": int(node.attrib["total-result-count"]),
        "query": get_text(node.find("ops:query", ns)),
        "range": query_range,
    }


def register_document(node):
    return {
        "statuses": ep_patent_statuses(node),
        "bibliographic_data": bibliographic_data(
            node.find("reg:bibliographic-data", ns)
        ),
        "procedural_data": procedural_data(node),
        "events": events(node),
    }


"""Patent status"""


def ep_patent_statuses(doc):
    return [
        patent_status(x)
        for x in doc.findall("reg:ep-patent-statuses/reg:ep-patent-status", ns)
    ]


def patent_status(node):
    return {
        "date": node.attrib.get("change-date", ""),
        "code": node.attrib.get("status-code", ""),
        "text": get_text(node),
    }


"""Bibliographic data"""


def bibliographic_data(bib):
    data = {
        "country_code": "EP",
    }

    application_data = [
        application_reference(node)
        for node in bib.findall("reg:application-reference", ns)
    ]
    european_application = get_latest_by_gazette_number(
        x for x in application_data if x["country"] == "EP"
    )

    data["application_number"] = european_application["number"]
    data["filing_date"] = european_application["date"]

    if international_application := [
        x for x in application_data if x["country"] == "WO"
    ]:
        data["international_application_number"] = international_application[0][
            "number"
        ]

    data["publications"] = [
        publication_reference(x) for x in bib.findall("reg:publication-reference", ns)
    ]

    data["priority_claims"] = [
        priority_claims(x) for x in bib.findall("reg:priority-claims", ns)
    ]

    data["parent_applications"] = [
        document_id(x)
        for x in bib.findall(
            "reg:related-documents/reg:division/reg:relation/reg:parent-doc/reg:document-id[@document-id-type='application number']",
            ns,
        )
    ]

    data["child_applications"] = [
        document_id(x)
        for x in bib.findall(
            "reg:related-documents/reg:division/reg:relation/reg:child-doc/reg:document-id[@document-id-type='application number']",
            ns,
        )
    ]

    data["applicants"] = [
        applicants(x) for x in bib.findall("reg:parties/reg:applicants", ns)
    ]

    data["agents"] = [agents(x) for x in bib.findall("reg:parties/reg:agents", ns)]

    for x in bib.findall("reg:invention-title", ns):
        name = "title_" + x.attrib["lang"]
        data[name] = get_text(x)

    data["citations"] = [
        citation(x) for x in bib.findall("reg:references-cited/reg:citation", ns)
    ]

    return data


def application_reference(node):
    data = document_id(node.find("reg:document-id", ns))
    data["change-gazette-num"] = node.attrib.get("change-gazette-num", "")
    return data


def publication_reference(node):
    data = document_id(node.find("reg:document-id", ns))
    data["change-gazette-num"] = node.attrib.get("change-gazette-num", "")
    return data


def priority_claims(node):
    return [priority_claim(x) for x in node.findall("reg:priority-claim", ns)]


def priority_claim(node):
    return {
        "kind": node.attrib.get("kind"),
        "country": node.find("reg:country", ns).text,
        "number": node.find("reg:doc-number", ns).text,
        "date": date(node.find("reg:date", ns)),
    }


def citation(node):
    patcit_node = node.find("reg:patcit", ns)
    if patcit_node is not None:
        document = patcit(patcit_node)
    else:
        nplcit_node = node.find("reg:nplcit", ns)
        if nplcit_node is not None:
            document = nplcit(nplcit_node)
        else:
            raise Exception("Citation node lacks patcit and nplcit nodes")
    cited_phase = node.attrib.get("cited-phase", "")
    category = get_text(node.find("reg:category", ns))
    doi_node = node.find("reg:doi", ns)
    if doi_node is not None:
        doi = get_text(doi_node)
    else:
        doi = ""
    document["doi"] = doi
    return {
        "document": document,
        "category": category,
        "cited_phase": cited_phase,
    }


def patcit(node):
    data = document_id(node.find("reg:document-id", ns))
    data["url"] = node.attrib.get("url", "")
    data["publication_type"] = "pat"
    return data


def nplcit(node):
    text_node = node.find("reg:text", ns)
    text = get_text(text_node) if text_node is not None else ""
    return {"publication_type": "npl", "text": text}


def document_id(node):
    res = {
        "country": get_text(node.find("reg:country", ns)),
        "number": get_text(node.find("reg:doc-number", ns)),
    }

    date_node = node.find("reg:date", ns)
    res["date"] = date(date_node)

    kind_node = node.find("reg:kind", ns)
    if kind_node is not None:
        res["kind"] = get_text(kind_node)

    return res


def get_latest_by_gazette_number(iterator):
    if result := sorted(iterator, key=itemgetter("change-gazette-num")):
        return result[0]
    return None


def applicants(node):
    return [applicant(x) for x in node.findall("reg:applicant", ns)]


def applicant(node):
    return addressbook(node.find("reg:addressbook", ns))


def agents(node):
    return [agent(x) for x in node.findall("reg:agent", ns)]


def agent(node):
    return addressbook(node.find("reg:addressbook", ns))


def addressbook(node):
    name = get_text(node.find("reg:name", ns))
    addr = address(node.find("reg:address", ns))
    country = get_text(node.find("reg:address/reg:country", ns))
    return {"name": name, "address": addr, "country": country}


def address(node):
    return "\n".join(get_text(x) for x in node if "address" in x.tag)


"""Events"""


def events(doc):
    return [
        dossier_event(e) for e in doc.findall("reg:events-data/reg:dossier-event", ns)
    ]


def dossier_event(node):
    code = node.find("reg:event-code", ns).text
    ed = date(node.find("reg:event-date/reg:date", ns))
    description = node.find("reg:event-text", ns).text
    return {
        "date": ed,
        "code": code,
        "description": description,
    }


"""Procedural steps"""


def procedural_data(node):
    return [
        procedural_step(s)
        for s in node.findall("reg:procedural-data/reg:procedural-step", ns)
    ]


def procedural_step(node):
    code = node.find("reg:procedural-step-code", ns).text
    description = node.find(
        "reg:procedural-step-text[@step-text-type='STEP_DESCRIPTION']", ns
    ).text
    step = {"code": code, "description": description}
    if parser := step_parsers.get(code):
        step.update(parser(node))
    return step


"""Step specific parsers"""


def abex(node):
    """Amendments"""
    date = procedural_step_date(node, "DATE_OF_REQUEST")
    kind = node.find(
        "reg:procedural-step-text[@step-text-type='Kind of amendment']", ns
    )
    return {"date": date, "kind": kind.text}


def adwi(node):
    """Application deemed to be withdrawn"""
    effective = procedural_step_date(node, "DATE_EFFECTIVE")
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    reason = node.find(
        "reg:procedural-step-text[@step-text-type='STEP_DESCRIPTION_NAME']", ns
    ).text
    return {"dispatch": dispatch, "reason": reason, "effective": effective}


def agra(node):
    """Announcement of grant"""
    date = procedural_step_date(node, "DATE_OF_DISPATCH")
    return {"date": date}


def exre(node):
    """Examination report"""
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    tl = time_limit(node.find("reg:time-limit", ns))
    reply = procedural_step_date(node, "DATE_OF_REPLY")
    return {"date": dispatch, "time_limit": tl, "reply": reply}


def igra(node):
    """Intention to grant"""
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    grant_fee = procedural_step_date(node, "GRANT_FEE_PAID")
    print_fee = procedural_step_date(node, "PRINT_FEE_PAID")
    return {"dispatch": dispatch, "grant_fee": grant_fee, "print_fee": print_fee}


def isat(node):
    authority = node.find(
        "reg:procedural-step-text[@step-text-type='searching authority']", ns
    ).text
    return {"authority": authority}


def obso(node):
    """Invitation to file observations"""
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    tl = time_limit(node.find("reg:time-limit", ns))
    reply = procedural_step_date(node, "DATE_OF_REPLY")
    return {"dispatch": dispatch, "time_limit": tl, "reply": reply}


def opex(node):
    """Examination on admissibility of an opposition"""
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    reply = procedural_step_date(node, "DATE_OF_REPLY")
    sequence = node.find("[@step-text-type='sequence-number']")
    opponent = int(sequence.text) if sequence is not None else None
    return {
        "dispatch": dispatch,
        "opponent": opponent,
        "reply": reply,
    }


def prol(node):
    language = node.find(
        "reg:procedural-step-text[@step-text-type='procedure language']", ns
    ).text
    return {"language": language}


def revo(node):
    """Revocation of the patent"""
    dispatch = procedural_step_date(node, "DATE_OF_DISPATCH")
    effective = procedural_step_date(node, "DATE_EFFECTIVE")
    return {"dispatch": dispatch, "effective": effective}


def rfee(node):
    """Renewal fees"""
    payment = procedural_step_date(node, "DATE_OF_PAYMENT")
    year = int(node.find("reg:procedural-step-text[@step-text-type='YEAR']", ns).text)
    return {"date": payment, "year": year}


def rfpr(node):
    """Request for further processing"""
    request = procedural_step_date(node, "DATE_OF_REQUEST")
    result_node = node.find("reg:procedural-step-result", ns)
    result = result_node.text if result_node is not None else None
    result_date = procedural_step_date(node, "RESULT_DATE")
    return {"request": request, "result": result, "result_date": result_date}


step_parsers = {
    "ABEX": abex,
    "ADWI": adwi,
    "AGRA": agra,
    "EXRE": exre,
    "IGRA": igra,
    "ISAT": isat,
    "OBSO": obso,
    "OPEX": opex,
    "PROL": prol,
    "REVO": revo,
    "RFEE": rfee,
    "RFPR": rfpr,
}


"""Helpers"""


def get_text(node):
    return node.text.strip() if node.text else ""


def procedural_step_date(node, name):
    el = node.find(
        "reg:procedural-step-date[@step-date-type='{}']/reg:date".format(name), ns
    )
    if el is None:
        return None
    return date(el)


def time_limit(node):
    text = node.text
    if text.startswith("M"):
        text = text[1:]
    return int(text)


def date(node):
    if node is None:
        return None
    return datetime.datetime.strptime(get_text(node), "%Y%m%d").date()
