import streamlit as st
from openai import AsyncOpenAI
import re
import asyncio
import time

# ==== OpenAI Setup ====
FAST_MODEL = "gpt-3.5-turbo"      # Fast, cheap tasks
REASONING_MODEL = "gpt-4.1-nano"  # Better reasoning/definitions/examples

client = AsyncOpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="📘 Word Explorer", page_icon="📚")

# ==== Language Selector ====
query_params = st.query_params
initial_language = query_params.get("lang", "English")
language = st.selectbox("🌍 Select Language", ["English", "Italian"], index=0 if initial_language == "English" else 1)

# ==== Tabs ====
tab1, tab2 = st.tabs(["📖 Word Explorer", "🧩 Sentence in All Tenses"])


# ==== Linkify Synonyms ====
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


# ==== Async OpenAI Request ====
async def ask_openai_async(prompt: str, model: str = REASONING_MODEL):
    start = time.perf_counter()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful English teacher."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            timeout=30,
        )
        duration = time.perf_counter() - start
        print(f"✅ [DEBUG] {model} request took {duration:.2f}s")
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ [DEBUG] OpenAI error: {e}")
        return f"Error: {e}"


# ==== Fetch Multiple Prompts Concurrently ====
async def fetch_word_data(word: str, language: str):
    prompts = {
        "meta": (FAST_MODEL, f"""
    Provide the CEFR level (A1–C2) and frequency (common, medium, rare) for the word "{word}".
    Respond using **exactly** this format (no extra text):

    - **Word:** {word}
    - **CEFR:** B2
    - **Frequency:** Medium
    """),

        "definition": (REASONING_MODEL, f"""
    Provide a clear, concise definition of the word "{word}" in simple English. 
    If the word has multiple meanings, list each meaning as a separate bullet point. 
    Do not include any introduction or conclusion. Use this format:

    - meaning 1
    - meaning 2
    """),

        "example": (REASONING_MODEL, f"""
    Write 1–2 short, natural {language} sentences using the word "{word}" in context. 
    If there are multiple meanings, give one example per meaning. 
    Do not add any commentary or extra text. Use this format:

    - example sentence 1
    - example sentence 2
    """),

        "synonyms": (FAST_MODEL, f"""
    List up to 3 '{language}' synonyms for the word "{word}". 
    If there are multiple meanings, group synonyms by meaning. 
    Do not add explanations. Use this format:

    ### Synonyms
    - synonym 1
    - synonym 2
    - synonym 3
    """),

        "phonetics": (FAST_MODEL, f"""
    List up to 3 {language} words that sound similar to "{word}", excluding "{word}" itself. 
    Do not add explanations. Use this format:

    ### Phonetically Similar Words
    - word 1
    - word 2
    - word 3
    """)
    }

    print(f"🔹 [DEBUG] Fetching data for '{word}' | Language: {language}")

    tasks = {name: asyncio.create_task(ask_openai_async(prompt, model)) for name, (model, prompt) in prompts.items()}
    results = {}
    for name, task in tasks.items():
        res = await task
        print(f"✅ [DEBUG] Response for '{name}': {res[:200]}...\n")
        results[name] = res

    print("🎯 [DEBUG] All requests completed!\n")
    return results


# ==== Tab 1: Word Explorer ====
with tab1:
    st.title("📘 Word Explorer")
    st.markdown("Type an English or Italian word to explore definitions, examples, and synonyms.")


    initial_word = query_params.get("word", "")
    initial_word = initial_word or ("precarietà" if language == "Italian" else "precarious")

    col1, col2 = st.columns([4, 1])
    with col1:
        word = st.text_input("Enter a word", value=initial_word)
    with col2:
        trigger_word = st.button("🔍 Explore Word")

    if trigger_word and word:
        with st.spinner("Fetching word data..."):
            results = asyncio.run(fetch_word_data(word, language))

        # Display results
        st.markdown(f"**📊 Word Level Info**\n\n{results['meta']}")
        st.markdown("### 📖 Definition")
        st.markdown(results['definition'])

        st.markdown("### 🧠 Contextual Example")
        st.markdown(results['example'])

        st.markdown("### 🔁 Synonyms")
        linked_synonyms = linkify_list_section(results['synonyms'], ["synonym"], lang=language)
        st.markdown(re.sub(r"^### Synonyms\n", "", linked_synonyms, flags=re.MULTILINE))

        st.markdown("### 🔊 Phonetically Similar Words")
        linked_phonetics = linkify_list_section(results['phonetics'], ["phonetically"], lang=language)
        st.markdown(re.sub(r"^### Phonetically Similar Words\n", "", linked_phonetics, flags=re.MULTILINE))

        if language == "English":
            st.markdown(f"[📚 Hear on Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/{word.lower()})")


# ==== Tab 2: Sentence Tense Transformer ====
with tab2:
    st.title("🧩 Sentence in All Tenses")
    st.markdown("Enter a sentence to see it rewritten in major tenses with highlighted structures.")

    sentence = "Scrive una lettera." if language == "Italian" else "She writes a letter."
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
Add explanations for each tense (how to form it) and highlight tense constructions (e.g., **bold** the helping verbs or indicators).
If needed, extend the sentence slightly.

Sentence: "{user_sentence}"
Use response language: English
Include:
{tense_list}

Format:
1. Tense Name
2. Example sentence (**highlight structure**)
3. Description
4. How to form it
"""

        with st.spinner("Generating tense variations..."):
            tenses_output = asyncio.run(ask_openai_async(tense_prompt, model=REASONING_MODEL))

        st.markdown(tenses_output)

        if st.button("🔁 Regenerate Tenses", key="retenses"):
            st.rerun()
