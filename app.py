import streamlit as st
from openai import OpenAI
import re
import time

# Init OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL = "gpt-4.1-nano"

st.set_page_config(page_title="📘 Word Explorer", page_icon="📚")

# ---- ✅ Language selector moved here (before tabs) ----
query_params = st.query_params
initial_language = query_params.get("lang", "English")
language = st.selectbox("🌍 Select Language", ["English", "Italian"], index=0 if initial_language == "English" else 1)

# Top tabs
tab1, tab2 = st.tabs(["📖 Word Explorer", "🧩 Sentence in All Tenses"])


# Utility: Linkify synonyms and similar words
def linkify_list_section(text: str, section_header_keywords: list[str], lang: str) -> str:
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
                link = f"[{phrase}](?word={phrase.replace(' ', '%20')}&lang={lang})"
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
    initial_language = query_params.get("lang", "English")


    if language == "Italian":
        initial_word = initial_word or "precarietà"
    else:
        initial_word = initial_word or "precarious"
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
Word: {word} (correct form if typo)
CEFR: B2
Frequency: Medium
Use markdown formatting only, no explanations or additional text.
"""
            meta = ask_openai(prompt_meta, spinner_message="Analyzing CEFR level & frequency...")
            st.markdown(f"**📊 Word Level Info**\n\n{meta}")

            # --- Definition ---
            st.markdown("### 📖 Definition")
            definition_prompt = f"Provide a concise definition of the word '{word}' using simple language in English. If the word has multiple meanings, include each meaning separately in a short, clear format. Do not include introductions or conclusions."
            definition = ask_openai(definition_prompt, spinner_message="Loading definition...")
            st.markdown(definition)

            # --- Contextual Example ---
            st.markdown("### 🧠 Contextual Example")
            example_prompt = f"Write 1–2 short, natural {language} sentences using the word '{word}' in context. If there are multiple meanings, include one sentence per meaning. Do not add any commentary or explanation."
            example = ask_openai(example_prompt, spinner_message="Loading contextual example...")
            st.markdown(example)

            # --- Synonyms ---
            st.markdown("### 🔁 Synonyms")
            synonym_prompt = f"List max 3 (if exist) '{language}' synonyms of the word '{word}' as a clean bullet list. If the word has multiple meanings, provide synonyms for each meaning, but make output one. Start with '### Synonyms' and do not include any explanation or intro text."
            synonyms = ask_openai(synonym_prompt, spinner_message="Loading synonyms...")
            linked_synonyms = linkify_list_section(synonyms, section_header_keywords=["synonym"], lang=language)
            linked_synonyms = re.sub(r"^### Synonyms\n", "", linked_synonyms, flags=re.MULTILINE)
            st.markdown(linked_synonyms)

            # --- Phonetically Similar Words ---
            st.markdown("### 🔊 Phonetically Similar Words")
            phonetic_prompt = f"List max 3 (if exist) {language} words that sound similar to '{word}', excluding {word}. Format as a bullet list starting with '### Phonetically Similar Words'. Do not include any explanation or filler text."
            phonetics = ask_openai(phonetic_prompt, spinner_message="Loading phonetically similar words...")
            linked_phonetics = linkify_list_section(phonetics, section_header_keywords=["phonetically"], lang=language)
            linked_phonetics = re.sub(r"^### Phonetically Similar Words\n", "", linked_phonetics, flags=re.MULTILINE)
            st.markdown(linked_phonetics)

            # External link for pronunciation
            if language == "English":
                st.markdown(f"[📚 Hear on Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/{word.lower()})")


# ---- Tab 2: Sentence Tense Transformer ----
with tab2:
    st.title("🧩 Sentence in All Tenses")
    st.markdown("Enter any sentence to see it rewritten in major tenses with highlighted structures.")

    # Default example sentence depending on selected language
    if language == "Italian":
        sentence = "Scrive una lettera."
    else:
        sentence = "She writes a letter."

    col1, col2 = st.columns([4, 1])
    with col1:
        user_sentence = st.text_input("✏️ Your sentence:", value=sentence)
    with col2:
        trigger_sentence = st.button("🔍 Transform Sentence")

    if trigger_sentence and user_sentence:
        if language == "Italian":
            tense_list = """- Presente
- Imperfetto
- Passato Prossimo
- Passato Remoto
- Trapassato Prossimo
- Futuro Semplice
- Futuro Anteriore
- Condizionale Presente
- Condizionale Passato
- Congiuntivo Presente
- Congiuntivo Imperfetto
- Congiuntivo Passato
- Congiuntivo Trapassato"""
            tense_instruction = "Rewrite the sentence in the major **Italian** tenses listed below."
        else:
            tense_list = """- Present Simple
- Present Continuous
- Past Simple
- Past Continuous
- Future Simple
- Present Perfect
- Past Perfect
- Future Perfect
- First Conditional
- Second Conditional
- Third Conditional"""
            tense_instruction = "Rewrite the sentence in the major **English** tenses listed below."

        tense_prompt = f"""
{tense_instruction}  
Add explanations for each tense (how to form it) and highlight the tense constructions (e.g., **bold** the helping verbs or tense indicators).  
If necessary, extend the sentence slightly for clarity.

Sentence: "{user_sentence}"  
Use response language: English  
Include:
{tense_list}

Format each tense as follows:
1. Tense Name
2. Example sentence (with highlighted structure using **bold**)
3. Description of how it works
4. How to form it

Use markdown formatting only. Do not include any introductory or summary text.
"""
        tenses_output = ask_openai(tense_prompt, spinner_message="Generating tense variations...")
        st.markdown(tenses_output)

        if st.button("🔁 Regenerate Tenses", key="retenses"):
            st.rerun()

