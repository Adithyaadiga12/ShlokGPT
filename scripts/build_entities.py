"""
Build data/rag/entities.json — curated character/place records for the epics +
Gita, so identity queries ("who was Bhishma", "where is Ayodhya") resolve to a
real record instead of 20 verses that merely mention the name. Descriptions are
concise factual summaries (public-domain narrative facts), not copyrighted text.
"""
import json
import os

RAG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "rag")


def E(id, name, skt, typ, aliases, sources, desc):
    return {"id": f"ENT-{id}", "name": name, "sanskrit": skt, "type": typ,
            "aliases": aliases, "sources": sources, "description": desc}


ENTITIES = [
    # --- Mahabharata / Gita characters ---
    E("bhishma", "Bhishma", "भीष्म", "character", ["Devavrata", "Gangaputra", "Pitamaha"],
      ["Mahabharata", "Bhagavad Gita"],
      "Son of King Shantanu and the goddess Ganga. He took a vow of lifelong celibacy and "
      "renounced his claim to the throne of Hastinapura, earning the boon of choosing the time "
      "of his own death. The grand-uncle and elder statesman of both the Pandavas and Kauravas, "
      "he was the Kaurava army's first commander-in-chief and fell on a bed of arrows at Kurukshetra."),
    E("arjuna", "Arjuna", "अर्जुन", "character", ["Partha", "Dhananjaya", "Savyasachi", "Gudakesha"],
      ["Mahabharata", "Bhagavad Gita"],
      "The third Pandava, son of Kunti and the god Indra, and the greatest archer of his age. "
      "His crisis of conscience before the battle of Kurukshetra prompts Krishna's teaching in the "
      "Bhagavad Gita. Krishna serves as his charioteer."),
    E("krishna", "Krishna", "कृष्ण", "character", ["Vasudeva", "Govinda", "Keshava", "Hari", "Madhava"],
      ["Mahabharata", "Bhagavad Gita", "Bhagavata Purana"],
      "An avatar of Vishnu, prince of the Yadavas, and the speaker of the Bhagavad Gita. He acts as "
      "Arjuna's charioteer and counsellor at Kurukshetra and is central to the Bhagavata Purana, which "
      "narrates his life and deeds."),
    E("yudhishthira", "Yudhishthira", "युधिष्ठिर", "character", ["Dharmaraja", "Ajatashatru"],
      ["Mahabharata"],
      "The eldest Pandava, son of Kunti and the god Dharma, renowned for his righteousness and "
      "truthfulness. He becomes emperor after the Pandavas' victory at Kurukshetra."),
    E("bhima", "Bhima", "भीम", "character", ["Bhimasena", "Vrikodara"],
      ["Mahabharata"],
      "The second Pandava, son of Kunti and the god Vayu, famed for immense strength. He kills "
      "Duryodhana and the other Kauravas in the war."),
    E("duryodhana", "Duryodhana", "दुर्योधन", "character", ["Suyodhana"],
      ["Mahabharata"],
      "The eldest of the hundred Kaurava brothers and son of Dhritarashtra. His refusal to grant the "
      "Pandavas their kingdom precipitates the Kurukshetra war; he is the principal antagonist."),
    E("karna", "Karna", "कर्ण", "character", ["Radheya", "Vasusena", "Angaraja"],
      ["Mahabharata"],
      "Son of Kunti and the sun god Surya, born before her marriage and raised by a charioteer. A peerless "
      "warrior and loyal friend of Duryodhana, he fights for the Kauravas and is killed by Arjuna."),
    E("draupadi", "Draupadi", "द्रौपदी", "character", ["Panchali", "Krishnaa", "Yajnaseni"],
      ["Mahabharata"],
      "Daughter of King Drupada and the common wife of the five Pandavas. Her public humiliation in the "
      "Kaurava court is a key cause of the war."),
    E("dhritarashtra", "Dhritarashtra", "धृतराष्ट्र", "character", [],
      ["Mahabharata", "Bhagavad Gita"],
      "The blind king of Hastinapura, father of the Kauravas. The Bhagavad Gita is framed as the narration "
      "of the battle told to him by his charioteer Sanjaya."),
    E("sanjaya", "Sanjaya", "सञ्जय", "character", [],
      ["Mahabharata", "Bhagavad Gita"],
      "Charioteer and adviser to Dhritarashtra, granted divine sight to witness the battle of Kurukshetra. "
      "He narrates the events, including the Bhagavad Gita, to the blind king."),
    E("drona", "Drona", "द्रोण", "character", ["Dronacharya"],
      ["Mahabharata"],
      "The martial preceptor of both the Pandavas and Kauravas. He becomes the Kaurava army's second "
      "commander-in-chief and is slain at Kurukshetra."),
    E("kunti", "Kunti", "कुन्ती", "character", ["Pritha"],
      ["Mahabharata"],
      "Mother of the three eldest Pandavas and, earlier, of Karna. Through a boon she could invoke gods "
      "to father her sons."),
    E("vyasa", "Vyasa", "व्यास", "character", ["Krishna Dvaipayana", "Vedavyasa"],
      ["Mahabharata", "Puranas"],
      "The sage traditionally regarded as the author of the Mahabharata and compiler of the Vedas and "
      "Puranas, and a figure within the Mahabharata's own narrative."),
    # --- Ramayana characters ---
    E("rama", "Rama", "राम", "character", ["Ramachandra", "Raghava", "Kakutstha"],
      ["Ramayana"],
      "Prince of Ayodhya, eldest son of King Dasharatha, and an avatar of Vishnu. The hero of the "
      "Ramayana, he is exiled for fourteen years, and rescues his wife Sita from the demon king Ravana."),
    E("sita", "Sita", "सीता", "character", ["Vaidehi", "Janaki", "Maithili"],
      ["Ramayana"],
      "Wife of Rama and daughter of King Janaka of Videha, considered an incarnation of Lakshmi. Her "
      "abduction by Ravana drives the central conflict of the Ramayana."),
    E("lakshmana", "Lakshmana", "लक्ष्मण", "character", ["Saumitri"],
      ["Ramayana"],
      "Devoted younger brother of Rama who accompanies him into exile and fights alongside him against Ravana."),
    E("hanuman", "Hanuman", "हनुमान्", "character", ["Anjaneya", "Maruti", "Pavanaputra"],
      ["Ramayana"],
      "The vanara (monkey) devotee of Rama, son of the wind god Vayu, renowned for strength and devotion. "
      "He leaps to Lanka to find Sita and is central to the war against Ravana."),
    E("ravana", "Ravana", "रावण", "character", ["Dashagriva", "Lankesha"],
      ["Ramayana"],
      "The ten-headed rakshasa king of Lanka who abducts Sita, and the chief antagonist of the Ramayana. "
      "He is a learned devotee of Shiva but undone by pride; Rama kills him."),
    E("dasharatha", "Dasharatha", "दशरथ", "character", [],
      ["Ramayana"],
      "King of Ayodhya and father of Rama. Bound by a promise to his queen Kaikeyi, he reluctantly exiles "
      "Rama and dies of grief."),
    E("ravana_bharata", "Bharata", "भरत", "character", [],
      ["Ramayana"],
      "Younger brother of Rama who refuses the throne of Ayodhya in his absence, ruling as regent in Rama's "
      "name and placing Rama's sandals on the throne."),
    E("valmiki", "Valmiki", "वाल्मीकि", "character", [],
      ["Ramayana"],
      "The sage traditionally regarded as the author of the Ramayana, the 'first poem' (adi-kavya), and a "
      "character who shelters Sita in the epic's later portion."),
    # --- Deities / cosmic ---
    E("vishnu", "Vishnu", "विष्णु", "character", ["Narayana", "Hari"],
      ["Puranas", "Bhagavad Gita", "Ramayana", "Mahabharata"],
      "One of the principal deities, the preserver of the cosmos, who descends in avatars including Rama "
      "and Krishna. Central to the Vaishnava Puranas."),
    E("shiva", "Shiva", "शिव", "character", ["Mahadeva", "Rudra", "Shankara"],
      ["Puranas"],
      "One of the principal deities, associated with destruction and transformation, asceticism and yoga. "
      "Central to the Shiva Purana and Linga Purana."),
    E("brahma", "Brahma", "ब्रह्मा", "character", ["Pitamaha", "Svayambhu"],
      ["Puranas"],
      "The creator deity of the cosmos in Puranic cosmology, from whom creation proceeds."),
    # --- Places ---
    E("kurukshetra", "Kurukshetra", "कुरुक्षेत्र", "place", ["Dharmakshetra"],
      ["Mahabharata", "Bhagavad Gita"],
      "The sacred plain in northern India where the eighteen-day Mahabharata war is fought and the Bhagavad "
      "Gita is spoken. The Gita opens by calling it dharmakshetra, 'the field of dharma.'"),
    E("hastinapura", "Hastinapura", "हस्तिनापुर", "place", [],
      ["Mahabharata"],
      "Capital of the Kuru kingdom and the throne contested between the Pandavas and Kauravas."),
    E("ayodhya", "Ayodhya", "अयोध्या", "place", [],
      ["Ramayana"],
      "Capital of the Kosala kingdom and Rama's birthplace and home, ruled by the Ikshvaku dynasty."),
    E("lanka", "Lanka", "लङ्का", "place", [],
      ["Ramayana"],
      "The island fortress-kingdom ruled by the rakshasa king Ravana, where Sita is held captive."),
    E("indraprastha", "Indraprastha", "इन्द्रप्रस्थ", "place", [],
      ["Mahabharata"],
      "The capital built by the Pandavas on the Khandava plain, their share of the divided Kuru kingdom."),
    E("naimisha", "Naimisha", "नैमिष", "place", ["Naimisharanya"],
      ["Puranas", "Mahabharata"],
      "A sacred forest where sages gather to hear the Puranas and epics recited; a common narrative frame "
      "for the Puranas."),
]


def main():
    os.makedirs(RAG_DIR, exist_ok=True)
    ids = {e["id"] for e in ENTITIES}
    assert len(ids) == len(ENTITIES), "duplicate entity id"
    out = os.path.join(RAG_DIR, "entities.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ENTITIES, f, ensure_ascii=False, indent=2)
    types = {}
    for e in ENTITIES:
        types[e["type"]] = types.get(e["type"], 0) + 1
    print(f"wrote {len(ENTITIES)} entities ({types}) -> {out}")


if __name__ == "__main__":
    main()
