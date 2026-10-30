
import os
import json
import uuid
import requests
from datetime import date
from dotenv import load_dotenv
from anthropic import Anthropic

# Load API configuration from the .env file
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "").strip()

client = (
    Anthropic(api_key=ANTHROPIC_API_KEY)
    if ANTHROPIC_API_KEY
    else None
)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "TRACE-ResearchAgent/1.0"
})


def reconstruct_abstract(inverted_index):
    """Convert OpenAlex's indexed abstract into readable text."""
    if not inverted_index:
        return ""

    words = {}
    for word, positions in inverted_index.items():
        for position in positions:
            words[position] = word

    return " ".join(words[i] for i in sorted(words))


def search_openalex(question, max_results=10):
    """Retrieve scholarly work metadata from OpenAlex."""
    response = SESSION.get(
        "https://api.openalex.org/works",
        params={
            "search": question,
            "per-page": max_results,
            "filter": "type:article|preprint",
            "select": (
                "id,doi,title,publication_year,publication_date,"
                "type,authorships,primary_location,open_access,"
                "abstract_inverted_index,cited_by_count"
            ),
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json().get("results", [])


def assess_relevance(question, sources):
    """
    Ask Claude to assess relevance using retrieved metadata.
    Claude must not invent sources or evidence.
    """
    if not sources:
        return sources

    # Keep the original source order if Claude is unavailable.
    for source in sources:
        source["relevance"] = {
            "score": None,
            "reason": "Not assessed",
            "assessment_status": "pending",
        }

    if not client or not ANTHROPIC_MODEL:
        for source in sources:
            source["relevance"]["assessment_status"] = (
                "skipped_missing_configuration"
            )
        return sources

    papers_for_claude = [
        {
            "source_id": source["source_id"],
            "title": source["title"],
            "year": source["publication_year"],
            "abstract": source["abstract"][:3500],
        }
        for source in sources
    ]

    prompt = f"""
You are the relevance-assessment component of TRACE,
a research evidence system.

Research question:
{question}

Assess how relevant each supplied paper is to the question.
Use only the supplied titles, years, and abstracts.

Score each paper from 0 to 100:
- 90-100: directly addresses the question
- 70-89: strongly relevant
- 40-69: partially relevant
- 1-39: weakly relevant
- 0: irrelevant based on available information

Do not invent facts, findings, sources, or quotations.
An abstract may be incomplete or unavailable.
Relevance does not prove that a paper's claims are true.

Return ONLY valid JSON in this format:
{{
  "assessments": [
    {{
      "source_id": "S001",
      "score": 85,
      "reason": "Brief explanation based on the supplied metadata"
    }}
  ]
}}

Include every supplied source_id exactly once.

Supplied papers:
{json.dumps(papers_for_claude, ensure_ascii=False)}
"""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        text_response = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()

        # Handle JSON enclosed in Markdown fences, if returned.
        if text_response.startswith("```"):
            text_response = text_response.split("\n", 1)[1]
            text_response = text_response.rsplit("```", 1)[0].strip()

        parsed = json.loads(text_response)
        assessments = parsed.get("assessments", [])

        by_id = {
            item.get("source_id"): item
            for item in assessments
            if isinstance(item, dict)
        }

        for source in sources:
            assessment = by_id.get(source["source_id"])

            if not assessment:
                source["relevance"]["assessment_status"] = (
                    "assessment_missing"
                )
                continue

            score = assessment.get("score")

            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 100
            ):
                source["relevance"]["assessment_status"] = (
                    "invalid_score"
                )
                continue

            source["relevance"] = {
                "score": score,
                "reason": str(assessment.get("reason", ""))[:500],
                "assessment_status": "assessed_by_claude",
            }

        return sources

    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Relevance assessment failed: {error}")
    except Exception as error:
        print(f"Claude assessment failed: {error}")

    for source in sources:
        if source["relevance"]["assessment_status"] == "pending":
            source["relevance"]["assessment_status"] = "failed"

    return sources


def research_agent(question, max_results=10):
    research_id = str(uuid.uuid4())[:8]
    sources = []

    try:
        papers = search_openalex(question, max_results)

        for index, paper in enumerate(papers, start=1):
            abstract = reconstruct_abstract(
                paper.get("abstract_inverted_index")
            )

            authors = [
                item.get("author", {}).get("display_name", "")
                for item in (paper.get("authorships") or [])
                if item.get("author")
            ]

            location = paper.get("primary_location") or {}
            venue = location.get("source") or {}
            access = paper.get("open_access") or {}
            doi = paper.get("doi")

            sources.append({
                "source_id": f"S{index:03d}",
                "source_type": paper.get("type", "unknown"),
                "title": paper.get("title") or "Untitled",
                "url": (
                    doi
                    or access.get("oa_url")
                    or paper.get("id")
                ),
                "doi": doi,
                "authors": authors,
                "published_date": paper.get("publication_date"),
                "publication_year": paper.get("publication_year"),
                "retrieved_date": date.today().isoformat(),
                "journal": venue.get("display_name"),
                "abstract": abstract,
                "snippet": abstract,
                "content": abstract,
                "citations": paper.get("cited_by_count", 0),
                "openalex_id": paper.get("id"),
                "access": {
                    "is_open_access": access.get("is_oa"),
                    "full_text_url": access.get("oa_url"),
                    "status": (
                        "open_access_link_available"
                        if access.get("is_oa")
                        else "access_not_confirmed"
                    ),
                },
                "journal_quartile": {
                    "value": None,
                    "status": "not_verified",
                    "source": "SCImago",
                },
                "evidence": [],
                "limitations": (
                    ["Abstract unavailable; evidence is limited"]
                    if not abstract else
                    ["Only abstract metadata retrieved; "
                     "full-text evidence not yet extracted"]
                ),
            })

    except requests.RequestException as error:
        return {
            "research_id": research_id,
            "question": question,
            "sources": [],
            "error": f"Academic search failed: {error}",
        }

    # Ask Claude to assess relevance after retrieving real papers.
    sources = assess_relevance(question, sources)

    # Put the most relevant papers first.
    sources.sort(
        key=lambda source: (
            source["relevance"]["score"] is not None,
            source["relevance"]["score"] or 0,
        ),
        reverse=True,
    )

    return {
        "research_id": research_id,
        "question": question,
        "sources": sources,
    }


if __name__ == "__main__":
    question = input("Enter your research question: ").strip()

    if not question:
        print("Please enter a research question.")
    else:
        result = research_agent(question)
        print(json.dumps(result, indent=2, ensure_ascii=False))
