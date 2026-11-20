import os
import json
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

st.set_page_config(page_title="DarGlobal & Wasalt AI Assistant",
                   page_icon="🏢", layout="centered")
st.title("🏢 DarGlobal & Wasalt Real Estate AI")
st.caption("Ask about luxury branded residences, Saudi & Oman developments, and Wasalt property listings.")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
MODEL_NAME = "openrouter/free"

DATA_PATH = os.path.join("data", "data.json")


@st.cache_resource
def load_rag_index():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [f"{d['title']} | {d['content']}" for d in docs]
    embeddings = embedder.encode(texts, convert_to_numpy=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
    return docs, embedder, index


docs, embedder, index = load_rag_index()


def retrieve_context(query: str, k: int = 5):
    q_vec = embedder.encode([query], convert_to_numpy=True).astype("float32")
    _, indices = index.search(q_vec, k)

    context_blocks = []
    sources = {}
    for idx in indices[0]:
        if 0 <= idx < len(docs):
            doc = docs[idx]
            context_blocks.append(f"[{doc['title']}]\n{doc['content']}")
            sources[doc["source"]] = doc["title"]

    return "\n\n---\n\n".join(context_blocks), sources


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome! Ask me anything about DarGlobal developments (Saudi Arabia, Oman, Dubai, Qatar, Spain) or Wasalt properties.",
            "sources": {},
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for url, title in msg["sources"].items():
                    st.markdown(f"- [{title}]({url})")

if prompt := st.chat_input("e.g., What DarGlobal projects are in Saudi Arabia and Oman?"):
    if not OPENROUTER_API_KEY:
        st.error(
            "OPENROUTER_API_KEY is missing. Add it to your .env file or Hugging Face Secrets.")
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": prompt, "sources": {}})
    with st.chat_message("user"):
        st.markdown(prompt)

    context, sources = retrieve_context(prompt)
    system_prompt = (
        "You are an expert real estate assistant for DarGlobal and Wasalt. "
        "Answer the user's question accurately using ONLY the retrieved context below. "
        "Format your response clearly with bullet points where helpful. "
        "If the context does not contain the answer, state that clearly without guessing.\n\n"
        f"Retrieved Context:\n{context}"
    )

    with st.chat_message("assistant"):
        with st.spinner("Searching DarGlobal & Wasalt listings..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[-4:]],
                ],
                temperature=0.2,
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            if sources:
                with st.expander("Sources"):
                    for url, title in sources.items():
                        st.markdown(f"- [{title}]({url})")

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "sources": sources})
