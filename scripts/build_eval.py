"""
Build data/eval/queries.json — a hand-written retrieval evaluation set. Each
query lists the record id(s) a correct system should return. Includes deliberate
should-fail queries (empty expected set) to test that the system admits ignorance
instead of hallucinating. Verse ids are validated against verses.json at build.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
EVAL_DIR = os.path.join(ROOT, "data", "eval")
VERSES = os.path.join(ROOT, "data", "rag", "verses.jsonl")


def Q(id, query, typ, expected, notes=""):
    return {"id": id, "query": query, "type": typ,
            "expected_ids": expected, "notes": notes}


QUERIES = [
    # --- verse lookups (Bhagavad Gita) ---
    Q("Q001", "What does the Gita say about doing your duty without attachment to the results?",
      "verse", ["BG2.47"], "karma-yoga core verse"),
    Q("Q002", "Where does Krishna say the soul is never born and never dies?",
      "verse", ["BG2.20"], "eternity of the atman"),
    Q("Q003", "Which verse says weapons cannot cut the soul, nor fire burn it?",
      "verse", ["BG2.23"], "indestructibility of the soul"),
    Q("Q004", "Whenever righteousness declines, Krishna says he manifests himself — which verse?",
      "verse", ["BG4.7"], "yada yada hi dharmasya"),
    Q("Q005", "The verse about protecting the good and destroying the wicked, age after age.",
      "verse", ["BG4.8"], "paritranaya sadhunam"),
    Q("Q006", "Abandon all duties and surrender to me alone — where is this said?",
      "verse", ["BG18.66"], "sarva-dharman parityajya"),
    Q("Q007", "Krishna promises to carry what his devotees lack — which verse?",
      "verse", ["BG9.22"], "yoga-kshemam vahamy aham"),
    Q("Q008", "Better to do one's own duty imperfectly than another's well.",
      "verse", ["BG3.35", "BG18.47"], "sva-dharma; appears twice"),
    Q("Q009", "How does attachment lead to anger and ruin, step by step?",
      "verse", ["BG2.62", "BG2.63"], "dhyayato vishayan"),
    Q("Q010", "One should lift oneself by oneself and not degrade oneself.",
      "verse", ["BG6.5"], "uddhared atmanatmanam"),
    Q("Q011", "The opening verse of the Gita naming the field of dharma at Kurukshetra.",
      "verse", ["BG1.1"], "dharmakshetre kurukshetre"),
    # --- verse lookups (epics, Itihasa) ---
    Q("Q012", "The very first verse of the Ramayana, where Valmiki questions Narada.",
      "verse", ["ITIH1"], "opening of the Ramayana"),
    # --- entity / identity queries ---
    Q("Q020", "Who was Bhishma?", "entity", ["ENT-bhishma"], ""),
    Q("Q021", "Who is Arjuna in the Mahabharata?", "entity", ["ENT-arjuna"], ""),
    Q("Q022", "Who was the ten-headed king who abducted Sita?", "entity", ["ENT-ravana"], ""),
    Q("Q023", "Tell me about Hanuman.", "entity", ["ENT-hanuman"], ""),
    Q("Q024", "Who narrates the battle to the blind king Dhritarashtra?",
      "entity", ["ENT-sanjaya"], ""),
    Q("Q025", "Who was Karna's real mother?", "entity", ["ENT-karna", "ENT-kunti"], ""),
    # --- place queries ---
    Q("Q030", "Where was the Mahabharata war fought?", "place", ["ENT-kurukshetra"], ""),
    Q("Q031", "What is Ayodhya?", "place", ["ENT-ayodhya"], ""),
    Q("Q032", "Which island kingdom did Ravana rule?", "place", ["ENT-lanka"], ""),
    # --- glossary / concept queries ---
    Q("Q040", "What does dharma mean?", "glossary", ["GLO-dharma"], ""),
    Q("Q041", "What is karma?", "glossary", ["GLO-karma"], ""),
    Q("Q042", "Explain moksha.", "glossary", ["GLO-moksha"], ""),
    Q("Q043", "What is the difference between atman and brahman?",
      "glossary", ["GLO-atman", "GLO-brahman"], ""),
    Q("Q044", "What are the three gunas?",
      "glossary", ["GLO-guna", "GLO-sattva", "GLO-rajas", "GLO-tamas"], ""),
    Q("Q045", "What does ahimsa mean?", "glossary", ["GLO-ahimsa"], ""),
    Q("Q046", "What is bhakti?", "glossary", ["GLO-bhakti"], ""),
    Q("Q047", "Meaning of the syllable Om.", "glossary", ["GLO-om"], ""),
    # --- should-fail: not in the corpus; system must admit it doesn't know ---
    Q("Q900", "What does the Bhagavad Gita say about the internet?",
      "should_fail", [], "anachronism, not in corpus"),
    Q("Q901", "Which verse gives Krishna's opinion on democracy versus monarchy?",
      "should_fail", [], "no such teaching"),
    Q("Q902", "Who was Napoleon Bonaparte?", "should_fail", [], "out of domain"),
    Q("Q903", "Summarize the Quran's view of dharma.", "should_fail", [], "out of corpus"),
    Q("Q904", "What is the stock price of the Kuru kingdom?", "should_fail", [], "nonsensical"),
    Q("Q905", "Give me the recipe Draupadi used in the Akshaya Patra.",
      "should_fail", [], "not in the source texts"),
    Q("Q906", "What did Gandhi say about the Gita?", "should_fail", [],
      "modern commentary not in dataset"),
    Q("Q907", "Which Upanishad discusses quantum mechanics?", "should_fail", [], "anachronism"),
]


def main():
    os.makedirs(EVAL_DIR, exist_ok=True)
    with open(VERSES, encoding="utf-8") as f:
        verse_ids = {json.loads(ln)["id"] for ln in f if ln.strip()}

    # validate that non-verse expected ids look right and verse ids exist
    missing = []
    for q in QUERIES:
        for eid in q["expected_ids"]:
            if eid.startswith("BG") or eid.startswith("ITIH"):
                if eid not in verse_ids:
                    missing.append((q["id"], eid))
    if missing:
        print("WARNING — expected verse ids not found in verses.json:")
        for qid, eid in missing:
            print(f"  {qid}: {eid}")

    ids = {q["id"] for q in QUERIES}
    assert len(ids) == len(QUERIES), "duplicate query id"
    out = os.path.join(EVAL_DIR, "queries.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(QUERIES, f, ensure_ascii=False, indent=2)
    types = {}
    for q in QUERIES:
        types[q["type"]] = types.get(q["type"], 0) + 1
    print(f"wrote {len(QUERIES)} queries ({types}) -> {out}")
    print(f"validated verse ids missing: {len(missing)}")


if __name__ == "__main__":
    main()
