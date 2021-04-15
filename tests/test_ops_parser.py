import os
import datetime
import pytest
import python_ops_parser as parser

from .samples import SAMPLES, SAMPLE_DIR

"""Fixtures"""


@pytest.fixture(scope="session")
def xmlsamples():
    return {
        name: open(os.path.join(SAMPLE_DIR, f"{name}.xml"), encoding="utf-8").read()
        for name in SAMPLES
    }


@pytest.fixture(scope="session")
def register_document(xmlsamples):
    tree = parser.xml_tree(xmlsamples["99203729"])
    data = parser.world_patent_data(tree)
    return data["register_search"]["register_documents"][0]


@pytest.fixture(scope="session")
def bibliographic_data(register_document):
    return register_document["bibliographic_data"]


@pytest.fixture(scope="session")
def procedural_data(register_document):
    return register_document["procedural_data"]


@pytest.fixture(scope="session")
def event_data(register_document):
    return register_document["events"]


@pytest.fixture(scope="session")
def ep00102678(xmlsamples):
    xml_string = xmlsamples["00102678"]
    tree = parser.xml_tree(xml_string)
    data = parser.world_patent_data(tree)
    return data["register_search"]["register_documents"][0]


@pytest.fixture(scope="session")
def register_search(xmlsamples):
    tree = parser.xml_tree(xmlsamples["register_search"])
    data = parser.world_patent_data(tree)
    yield data


"""Patent status"""


def test_status(register_document):
    status = register_document["statuses"]
    assert status[0] == {
        "date": "",
        "code": "7",
        "text": "No opposition filed within time limit",
    }


"""Bibliographic data"""


def test_country_code(bibliographic_data):
    assert bibliographic_data["country_code"] == "EP"


def test_application_number(bibliographic_data):
    assert bibliographic_data["application_number"] == "99203729"


def test_filing_date(bibliographic_data):
    assert bibliographic_data["filing_date"] == datetime.date(1999, 11, 8)


def test_publications(bibliographic_data):
    publications = bibliographic_data["publications"]
    assert len(publications) == 2
    p = publications[0]
    assert p["country"] == "EP"
    assert p["number"] == "1000000"
    assert p["kind"] == "A1"
    assert p["date"] == datetime.date(2000, 5, 17)


def test_priorities(bibliographic_data):
    priority_claims = bibliographic_data["priority_claims"]
    assert len(priority_claims) == 1
    assert len(priority_claims[0]) == 1
    assert priority_claims[0][0]["kind"] == "national"
    assert priority_claims[0][0]["country"] == "NL"
    assert priority_claims[0][0]["number"] == "19981010536"
    assert priority_claims[0][0]["date"] == datetime.date(1998, 11, 12)


def test_applicants(bibliographic_data):
    applicant = bibliographic_data["applicants"][0][0]
    assert applicant["name"] == "Beheermaatschappij De Boer Nijmegen B.V."
    assert applicant["address"] == ("Koopvaardijweg 2\n" "6541 BS Nijmegen")
    assert applicant["country"] == "NL"


def test_agents(bibliographic_data):
    agents = bibliographic_data["agents"]
    current_agents = agents[0]
    agent = current_agents[0]
    assert agent["name"] == "'t Jong, Bastiaan Jacobus, et al"
    assert agent["address"] == (
        "Arnold & Siedsma\n" "Sweelinckplein 1\n" "2517 GK The Hague"
    )
    assert agent["country"] == "NL"


def test_title(bibliographic_data):
    assert (
        bibliographic_data["title_en"]
        == "Apparatus for manufacturing green bricks for the brick manufacturing industry"
    )
    assert (
        bibliographic_data["title_de"]
        == "Vorrichtung zur Herstellung von Steinformlingen für die Ziegelindustrie"
    )
    assert (
        bibliographic_data["title_fr"]
        == "Dispositif pour la fabrication de briques crues utilisées dans l'industrie manufacturière des briques"
    )


def test_citations(bibliographic_data):
    citations = bibliographic_data["citations"]
    assert len(citations) == 3


def test_citation_category(bibliographic_data):
    d = bibliographic_data["citations"][0]
    assert d["category"] == "A"
    assert d["cited_phase"] == "search"


def test_citation_patent_literature(bibliographic_data):
    d = bibliographic_data["citations"][0]["document"]
    assert d["country"] == "EP"
    assert d["number"] == "0680812"
    assert d["url"].startswith(
        "http://worldwide.espacenet.com/publicationDetails/biblio"
    )


"""Bibliographic data not included in the above dataset"""


def test_citation_npl(ep00102678):
    bib = ep00102678["bibliographic_data"]
    c = bib["citations"][9]
    assert c["cited_phase"] == "search"
    assert c["document"]["publication_type"] == "npl"
    assert c["document"]["text"].startswith("- PATENT ABSTRACTS OF JAPAN")


def test_divisionals_and_parents(ep00102678):
    bib = ep00102678["bibliographic_data"]

    assert bib["parent_applications"] == [
        {
            "country": "EP",
            "number": "19970933047",
            "kind": "D",
            "date": None,
        }
    ]

    assert bib["child_applications"][0] == {
        "country": "EP",
        "number": "20000114764",
        "kind": "D",
        "date": None,
    }

    assert [x["number"] for x in bib["child_applications"]] == [
        "20000114764",
        "20020017698",
        "20040001377",
        "20040001378",
        "20100158416",
        "20100158422",
        "20100158429",
        "20100158437",
        "20100158449",
        "20100158455",
        "20100184754",
    ]


"""Procedural data"""


def test_get_procedural_data(procedural_data):
    data = procedural_data
    assert len(data) == 6


def test_procedural_step_code_and_description(procedural_data):
    data = procedural_data
    step = data[0]
    assert step["code"] == "RFEE"
    assert step["description"] == "Renewal fee payment"


def test_renewal_fee_payment(procedural_data):
    data = procedural_data
    step = next(filter(lambda x: x["code"] == "RFEE", data))
    assert step["date"] == datetime.date(2001, 11, 28)
    assert step["year"] == 3


def test_announcement_of_grant(procedural_data):
    data = procedural_data
    step = next(filter(lambda x: x["code"] == "AGRA", data))
    assert step["date"] == datetime.date(2002, 4, 23)


def test_intention_to_grant(procedural_data):
    data = procedural_data
    step = next(filter(lambda x: x["code"] == "IGRA", data))
    assert step["dispatch"] == datetime.date(2002, 8, 7)


"""Events"""


def test_get_events(event_data):
    assert len(event_data) == 32


def test_dossier_event(event_data):
    event = event_data[0]
    assert event["code"] == "EPIDOSDTIPA"
    assert event["date"] == datetime.date(2014, 6, 7)
    assert event["description"] == "Deletion: Observations by third parties"


"""Parse register search output"""


def test_register_search_number_of_documents(register_search):
    register_documents = register_search["register_search"]["register_documents"]
    assert len(register_documents) == 25


def test_register_search_first_document(register_search):
    doc = register_search["register_search"]["register_documents"][0]
    assert doc["bibliographic_data"]["application_number"] == "15171792"
    assert doc["bibliographic_data"]["applicants"][0][0]["name"] == "BASF SE"
    assert (
        doc["bibliographic_data"]["title_de"]
        == "DI(ALKYLGLYKOSID)SULFOMETHYLSUCCINAT TENSIDE"
    )


def test_total_result_count(register_search):
    assert register_search["register_search"]["count"] == 1924


def test_query(register_search):
    assert register_search["register_search"]["query"] == "pa=bosch and pd=2015"


def test_range(register_search):
    assert register_search["register_search"]["range"] == (1, 25)
