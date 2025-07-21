import streamlit as st
from openai import OpenAI
import re
import time

# Init OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL = "gpt-4.1-nano"

st.set_page_config(page_title="📘 Word Explorer", page_icon="📚")

# Top tabs
tab1, tab2 = st.tabs(["📖 Word Explorer", "🧩 Sentence in All Tenses"])

# Utility: Linkify synonyms and similar words
def linkify_list_section(text: str, section_header_keywords: list[str]) -> str:
    lines = text.splitlines()
    result = []
    current_section = None

    for line in lines:
        line_strip = line.strip().lower()
        for keyword in section_header_keywords:
            if keyword in line_strip:
                current_section = keyword
                break

        if current_section in ["synonym", "phonetically"] and re.match(r"^- ", line.strip()):
            phrase = line.strip().lstrip("- ").strip()
            if phrase:
                link = f"[{phrase}](?word={phrase.replace(' ', '%20')})"
                result.append(f"- {link}")
        else:
            result.append(line)

    return "\n".join(result)


# OpenAI prompt function with spinner
def ask_openai(prompt, spinner_message="Loading..."):
    with st.spinner(spinner_message):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful English teacher."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                timeout=30,
            )
            response = response.choices[0].message.content.strip()
            print(f"OpenAI response: {response}")  # Debugging output
            return response
        except Exception as e:
            return f"Error: {str(e)}"

# ---- Tab 1: Word Explorer ----
with tab1:
    st.title("📘 Word Explorer")
    st.markdown("Type an English word to explore definitions, examples, levels, and clickable synonyms.")

    query_params = st.query_params
    initial_word = query_params.get("word", "")
    col1, col2 = st.columns([4, 1])
    with col1:
        word = st.text_input("Enter a word", value=initial_word, placeholder="e.g., precarious")
    with col2:
        trigger_word = st.button("🔍 Explore Word")

    if trigger_word and word:
        with st.container():
 # --- CEFR Level & Frequency ---
            prompt_meta = f"""
Give only the CEFR level (A1–C2) and word frequency (common, medium, rare) for the English word: "{word}".
Format exactly like this:
CEFR: B2
Frequency: Medium
"""
            meta = ask_openai(prompt_meta, spinner_message="Analyzing CEFR level & frequency...")
            st.markdown(f"**📊 Word Level Info**\n\n{meta}")

            # --- Definition ---
            st.markdown("### 📖 Definition")
            definition_prompt = f"Provide a concise definition of the word '{word}' using simple language. If the word has multiple meanings, include each meaning separately in a short, clear format. Do not include introductions or conclusions."
            definition = ask_openai(definition_prompt, spinner_message="Loading definition...")
            st.markdown(definition)

            # --- Contextual Example ---
            st.markdown("### 🧠 Contextual Example")
            example_prompt = f"Write 1–2 short, natural English sentences using the word '{word}' in context. If there are multiple meanings, include one sentence per meaning. Do not add any commentary or explanation."
            example = ask_openai(example_prompt, spinner_message="Loading contextual example...")
            st.markdown(example)

            # --- Synonyms ---
            st.markdown("### 🔁 Synonyms")
            synonym_prompt = f"List 3–5 synonyms of the word '{word}' as a clean bullet list. If the word has multiple meanings, provide synonyms for each meaning, but make output one. Start with '### Synonyms' and do not include any explanation or intro text."
            synonyms = ask_openai(synonym_prompt, spinner_message="Loading synonyms...")
            linked_synonyms = linkify_list_section(synonyms, section_header_keywords=["synonym"])
            linked_synonyms = re.sub(r"^### Synonyms\n", "", linked_synonyms, flags=re.MULTILINE)
            st.markdown(linked_synonyms)

            # --- Phonetically Similar Words ---
            st.markdown("### 🔊 Phonetically Similar Words")
            phonetic_prompt = f"List 3 English words that sound similar to '{word}'. Format as a bullet list starting with '### Phonetically Similar Words'. Do not include any explanation or filler text."
            phonetics = ask_openai(phonetic_prompt, spinner_message="Loading phonetically similar words...")
            linked_phonetics = linkify_list_section(phonetics, section_header_keywords=["phonetically"])
            linked_phonetics = re.sub(r"^### Phonetically Similar Words\n", "", linked_phonetics, flags=re.MULTILINE)
            st.markdown(linked_phonetics)

            # External link for pronunciation
            st.markdown(f"[📚 Hear on Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/{word.lower()})")


# ---- Tab 2: Sentence Tense Transformer ----
with tab2:
    st.title("🧩 Sentence in All Tenses")
    st.markdown("Enter any sentence to see it rewritten in major English tenses with highlighted structures.")

    col1, col2 = st.columns([4, 1])
    with col1:
        user_sentence = st.text_input("✏️ Your sentence:", value="She writes a letter.")
    with col2:
        trigger_sentence = st.button("🔍 Transform Sentence")

    if trigger_sentence and user_sentence:
        tense_prompt = f"""
Take the following sentence and rewrite it in the major English tenses. Add explanations for each tense (how to form it) and highlight the tense constructions (e.g., **bold** the helping verbs or main tense indicators). If necessary, extend the sentence slightly for clarity (e.g., for Past Perfect).

Sentence: "{user_sentence}"

Include:
- Present Simple
- Present Continuous
- Past Simple
- Past Continuous
- Future Simple
- Present Perfect
- Past Perfect
- Future Perfect
- First Conditional
- Second Conditional
- Third Conditional

Format each tense as follows:
1. Tense Name
2. Example sentence (with highlighted structure using **bold**)
2. Description of how it works
3. How to form it

Use markdown formatting only. Do not include any introductory or summary text.
"""
        tenses_output = ask_openai(tense_prompt, spinner_message="Generating tense variations...")
        st.markdown(tenses_output)

        if st.button("🔁 Regenerate Tenses", key="retenses"):
            st.rerun()
