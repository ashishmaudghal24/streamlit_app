# app_cloud.py — Cloud-first Streamlit UI that calls your converted notebook code
import time
import importlib
import streamlit as st

# Import the converted notebook code (this file must be in the repo root)
import notebook_code  # <- your converted .py

# ====== CONFIGURE THESE TWO NAMES ======
# Set these to the exact function names defined in notebook_code.py
RAG_FN_NAME = "rag_answer"        # e.g., def rag_answer(query): -> (answer, confidence) or (answer, confidence, method)
FT_FN_NAME  = "ft_answer"         # e.g., def ft_answer(query):  -> (answer, confidence) or (answer, confidence, method)
# =======================================

st.set_page_config(page_title="RAG vs Fine-Tuned — UI", layout="wide")
st.title("🔎 QA Interface — RAG vs Fine-Tuned")

def _call_func(func_name, query, mode):
    f = getattr(notebook_code, func_name, None)
    if not callable(f):
        return f"Function '{func_name}' not found in notebook_code.py", 0.0, mode
    try:
        # Try (query, mode) first
        out = f(query, mode)
    except TypeError:
        # Fallback to (query)
        out = f(query)
    except Exception as e:
        return f"Error calling {func_name}: {e}", 0.0, mode

    # Normalize outputs
    method = mode
    conf = 0.0
    if out is None:
        return "(No answer returned)", 0.0, method
    if isinstance(out, tuple):
        if len(out) == 3:
            ans, conf, m = out
            return str(ans), float(conf), str(m)
        if len(out) == 2:
            ans, b = out
            if isinstance(b, (int, float)):
                return str(ans), float(b), method
            else:
                return str(ans), 0.0, str(b)
        return " ".join(map(str, out)), 0.0, method
    if isinstance(out, dict):
        ans = str(out.get("answer") or out.get("output") or out.get("result") or "(No 'answer' field)")
        c = out.get("confidence") or out.get("score") or out.get("prob") or 0.0
        m = out.get("method") or out.get("mode") or method
        try: c = float(c)
        except Exception: c = 0.0
        return ans, c, str(m)
    return str(out), conf, method

def pipeline_run(query: str, mode: str):
    if mode == "RAG":
        return _call_func(RAG_FN_NAME, query, mode)
    else:
        return _call_func(FT_FN_NAME, query, mode)

# ------------ UI ------------
with st.sidebar:
    st.header("Controls")
    query = st.text_input("Enter your query")
    mode = st.radio("Select Mode", ["RAG", "Fine-Tuned"], horizontal=True)
    run = st.button("Run", type="primary")

if run:
    start = time.time()
    if not query:
        st.warning("Please enter a query in the sidebar.")
    else:
        answer, confidence, used_method = pipeline_run(query, mode)
        elapsed = time.time() - start

        st.subheader("Answer")
        st.write(answer)

        st.subheader("Details")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Retrieval Confidence Score", f"{confidence:.2f}")
        with c2: st.metric("Method Used", used_method)
        with c3: st.metric("Response Time (s)", f"{elapsed:.2f}")

with st.expander("ℹ️ How to hook your functions"):
    st.markdown(
        f"""
- Edit **RAG_FN_NAME** and **FT_FN_NAME** at the top of this file to match your function names in `notebook_code.py`.
- Supported return formats from your functions:
  - `str`
  - `(answer: str, confidence: float)`
  - `(answer: str, confidence: float, method: str)`
  - `dict` with keys like `answer`, `confidence`, `method`
- If your functions need `(query, mode)`, that's supported. If they only take `(query)`, that's also supported.
"""
    )
