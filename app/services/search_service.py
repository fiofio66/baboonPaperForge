"""
Template search service.

Two-stage: LLM resolves abbreviations (iotj → IEEE Internet of Things Journal),
then built-in mapping finds the download URL. Zero network for known journals.

Every entry has aliases for broad matching: searching "ieee" returns all IEEE variants.
"""

from __future__ import annotations

# ===================================================================
# Built-in mapping — each entry has journal name + aliases + URLs
# ===================================================================
_JOURNAL_DB: list[dict] = [
    {
        "id": "ieee-tran",
        "name": "IEEE Transactions / Journals (IEEEtran)",
        "aliases": ["ieee", "ieeetran", "ieee journal", "ieee transactions", "ieee trans", "ieee access",
                     "ieee internet of things", "ieee iot", "ieee iotj", "iotj", "iot-j", "ieee sensors",
                     "ieee signal processing", "ieee communications", "ieee power", "ieee t", "ieee trans on",
                     "ieee transactions on", "ieee 期刊", "ieee 论文"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/IEEEtran.zip",
            "https://mirror.ctan.org/macros/latex/contrib/IEEEtran.zip",
        ],
    },
    {
        "id": "ieee-conf",
        "name": "IEEE Conference (IEEEconf)",
        "aliases": ["ieee conference", "ieee conf", "ieee 会议", "ieeecon"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/IEEEconf.zip",
            "https://mirror.ctan.org/macros/latex/contrib/IEEEconf.zip",
        ],
    },
    {
        "id": "acm",
        "name": "ACM (acmart)",
        "aliases": ["acm", "acmart", "acm transactions", "acm sig", "acm conference", "acm journal"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/acmart.zip",
            "https://mirror.ctan.org/macros/latex/contrib/acmart.zip",
        ],
    },
    {
        "id": "elsevier",
        "name": "Elsevier / ScienceDirect (elsarticle)",
        "aliases": ["elsevier", "elsarticle", "els artical", "elsevier journal", "sciencedirect",
                     "information sciences", "ins", "expert systems with applications", "eswa",
                     "neurocomputing", "pattern recognition", "knowledge based systems", "kbs"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/elsarticle.zip",
        ],
    },
    {
        "id": "springer-lncs",
        "name": "Springer LNCS (llncs)",
        "aliases": ["springer", "lncs", "llncs", "springer lncs", "lecture notes", "springer conference",
                     "springer journal"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/llncs.zip",
        ],
    },
    {
        "id": "nature",
        "name": "Nature",
        "aliases": ["nature", "nature journal", "nature communications", "nature comm", "nat comm",
                     "nature methods", "nature medicine", "nature physics", "scientific reports", "sci rep"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/nature.zip",
        ],
    },
    {
        "id": "science",
        "name": "Science / AAAS",
        "aliases": ["science", "science journal", "aaas", "science advances"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/science.zip",
        ],
    },
    {
        "id": "aps-revtex",
        "name": "APS / Physical Review (REVTeX)",
        "aliases": ["aps", "revtex", "phys rev", "physical review", "prl", "prb", "prd", "pre",
                     "physical review letters", "physical review b", "physical review d", "physical review e",
                     "rev tex"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/revtex.zip",
        ],
    },
    {
        "id": "iop",
        "name": "IOP Publishing (iopart)",
        "aliases": ["iop", "iop publishing", "iopart", "iop journal", "iop science", "iop conf"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/iopart.zip",
        ],
    },
    {
        "id": "aip",
        "name": "AIP Publishing",
        "aliases": ["aip", "aip journal", "aip publishing", "applied physics letters", "apl", "journal of applied physics", "jap"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/aip.zip",
        ],
    },
    {
        "id": "rsc",
        "name": "Royal Society of Chemistry (RSC)",
        "aliases": ["rsc", "rsc journal", "chemical communications", "chem comm", "rsc advances",
                     "chemical society", "journal of materials chemistry", "jmc"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/rsc.zip",
        ],
    },
    {
        "id": "ams",
        "name": "American Mathematical Society (AMS)",
        "aliases": ["ams", "amsmath", "american mathematical", "ams journal", "jams", "proceedings ams", "math"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/amsmath.zip",
        ],
    },
    {
        "id": "sage",
        "name": "SAGE Publications",
        "aliases": ["sage", "sage journal", "sagepub", "sage publications"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/sage_latex_template.zip",
        ],
    },
    {
        "id": "wiley",
        "name": "Wiley",
        "aliases": ["wiley", "wiley journal", "wiley online", "advanced materials", "adv mater",
                     "angewandte chemie", "angew chem"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/wiley.zip",
        ],
    },
    {
        "id": "taylor-francis",
        "name": "Taylor & Francis (tandf)",
        "aliases": ["taylor", "t&f", "taylor francis", "taylor & francis", "tandf", "t and f"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/tandf.zip",
        ],
    },
    {
        "id": "mdpi",
        "name": "MDPI",
        "aliases": ["mdpi", "sensors mdpi", "applied sciences mdpi", "ijms", "ijerph", "mdpi journal"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/mdpi.zip",
        ],
    },
    {
        "id": "spie",
        "name": "SPIE",
        "aliases": ["spie", "spie journal", "optical engineering", "spie proceedings"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/spie.zip",
        ],
    },
    # --- ML/AI conferences ---
    {
        "id": "neurips",
        "name": "NeurIPS",
        "aliases": ["neurips", "nips", "neural information processing", "neurips conference"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/neurips.zip",
        ],
    },
    {
        "id": "icml",
        "name": "ICML",
        "aliases": ["icml", "international conference on machine learning", "icml conference"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/icml.zip",
        ],
    },
    {
        "id": "cvpr",
        "name": "CVPR / ICCV",
        "aliases": ["cvpr", "iccv", "computer vision and pattern recognition", "cvpr conference",
                     "international conference on computer vision", "eccv", "wacv"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/cvpr.zip",
        ],
    },
    {
        "id": "acl",
        "name": "ACL / EMNLP / NAACL",
        "aliases": ["acl", "emnlp", "naacl", "association for computational linguistics", "acl conference",
                     "eacl", "coling"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/acl.zip",
        ],
    },
    {
        "id": "aaai",
        "name": "AAAI",
        "aliases": ["aaai", "aaai conference", "association for the advancement of artificial intelligence"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/aaai.zip",
        ],
    },
    {
        "id": "ijcai",
        "name": "IJCAI",
        "aliases": ["ijcai", "international joint conference on artificial intelligence"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/ijcai.zip",
        ],
    },
    {
        "id": "arxiv",
        "name": "ArXiv",
        "aliases": ["arxiv", "arxiv preprint"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/arxiv.zip",
        ],
    },
    {
        "id": "自动化学报",
        "name": "自动化学报",
        "aliases": ["自动化学报", "acta automatica sinica", "automatica sinica", "aas"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/cas-latex-template.zip",
        ],
    },
    {
        "id": "计算机学报",
        "name": "计算机学报 / 软件学报 / 计算机研究与发展",
        "aliases": ["计算机学报", "软件学报", "计算机研究与发展", "cjc", "jcr", "chinese journal of computers",
                     "journal of software", "jos"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/cjc-latex-template.zip",
        ],
    },
    {
        "id": "中国科学",
        "name": "中国科学 / 科学通报",
        "aliases": ["中国科学", "科学通报", "science china", "science china information sciences", "scis"],
        "latex_urls": [
            "https://mirror.ctan.org/macros/latex/contrib/science_china.zip",
        ],
    },
]

_TUNA_MIRROR = "https://mirror.ctan.org"


def list_all_journals() -> list[dict]:
    """Return all known journal entries (id + name + aliases)."""
    return [
        {"id": e["id"], "name": e["name"], "aliases": e["aliases"][:5]}
        for e in _JOURNAL_DB
    ]


def match_all(query: str) -> list[dict]:
    """Return ALL entries whose aliases or name match the query.

    Fuzzy: each word in the query is matched independently.
    e.g. "ieee" → returns IEEEtran + IEEEconf
         "iotj" → returns IEEEtran (via 'ieee iotj' alias)
         "cv"   → returns CVPR/ICCV
    """
    q = query.lower().strip()
    words = q.split()
    results = []

    for entry in _JOURNAL_DB:
        searchable = " ".join(entry["aliases"] + [entry["name"]]).lower()
        # All query words must appear somewhere in aliases+name
        if all(w in searchable for w in words):
            results.append(entry)

    # Sort: exact alias match first, then partial name match
    def _score(e: dict) -> int:
        s = 0
        aliases_lower = [a.lower() for a in e["aliases"]]
        if any(q == a for a in aliases_lower):
            s += 100
        if any(q in a for a in aliases_lower):
            s += 50
        if q in e["name"].lower():
            s += 30
        return -s  # negate so higher score sorts first

    results.sort(key=_score)
    return results


async def llm_resolve_query(query: str, llm_config: dict | None = None) -> str:
    """Use LLM to resolve an ambiguous abbreviation to a canonical journal name.

    e.g. "iotj" → "IEEE Internet of Things Journal"
         "eswa" → "Expert Systems with Applications"
         "prb"  → "Physical Review B"

    Falls back to returning the original query if LLM is unavailable.
    """
    prompt = f"""You are a journal name resolver. Map the user's query to the FULL, official journal/conference name.

Examples:
  "iotj" → "IEEE Internet of Things Journal"
  "eswa" → "Expert Systems with Applications"
  "prb" → "Physical Review B"
  "neurips" → "NeurIPS"
  "cvpr" → "CVPR"
  "ins" → "Information Sciences"
  "tns" → "IEEE Transactions on Nuclear Science"
  "jmc" → "Journal of Materials Chemistry"
  "kbs" → "Knowledge-Based Systems"
  "acm" → "ACM"

Query: "{query}"

Output ONLY the full journal name, nothing else."""

    if not llm_config:
        return query

    provider = llm_config.get("provider", "openai")
    api_key = llm_config.get("api_key", "")
    base_url = llm_config.get("base_url", "")
    model = llm_config.get("model_name", "")

    if api_key and not any(api_key.startswith(p) for p in ("sk-", "ant-", "AIza")):
        try:
            from app.core.security import decrypt
            api_key = decrypt(api_key)
        except Exception:
            pass

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=model or "gpt-4o-mini", api_key=api_key or "sk-placeholder",
                             base_url=base_url or None, temperature=0)
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model=model or "claude-haiku-4-5", api_key=api_key or "ant-placeholder",
                                base_url=base_url or None, temperature=0)
        elif provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=model or "gemini-2.0-flash", google_api_key=api_key or "placeholder",
                                         temperature=0)
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model=model or "llama3.2", base_url=base_url or "http://localhost:11434", temperature=0)
        else:
            return query

        resp = await llm.ainvoke(prompt)
        result = resp.content if hasattr(resp, "content") else str(resp)
        return result.strip().strip('"').strip("'")
    except Exception:
        return query


def search_template_links(journal_name: str, template_format: str = "latex") -> list[dict]:
    """Get download URLs. Returns ALL matches, highest score first."""
    fmt = template_format.lower()
    candidates = []

    matches = match_all(journal_name)
    if not matches:
        # Last resort: DuckDuckGo
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                for r in ddgs.text(f'{journal_name} {"LaTeX" if fmt=="latex" else "Word"} template download', max_results=5):
                    url = r.get("href", "")
                    if url:
                        candidates.append({"url": url, "title": r.get("title", ""),
                                           "journal_name": journal_name, "score": 10})
        except Exception:
            pass
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates

    for entry in matches:
        key = "latex_urls" if fmt in ("latex", "tex") else "word_urls"
        urls = entry.get(key) or entry.get("latex_urls", [])
        for i, url in enumerate(urls):
            candidates.append({
                "url": str(url),
                "title": f"{entry['name']} — 模板 ({'备选' if i>0 else '首选'})",
                "journal_name": entry["name"],
                "journal_id": entry["id"],
                "score": 100 - i * 5,
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
