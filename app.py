# app.py
import time
import inspect
import importlib
import streamlit as st

st.set_page_config(page_title="Notebook → Streamlit", layout="wide")
st.title("Group no - 59")

st.sidebar.header("Controls")
query = st.sidebar.text_input("Enter your query")
mode = st.sidebar.radio("Select Mode", ["RAG", "Fine-Tuned"], horizontal=True)

st.sidebar.caption("This app auto-loads functions from utils_extracted.py")

# Lazy import utils_extracted
utils = None
try:
    utils = importlib.import_module("utils_extracted")
except Exception as e:
    st.error(f"Failed to import utils_extracted.py: {e}")

# Heuristic: pick a function we can call
def pick_candidate_function(module):
    if module is None:
        return None, None
    candidates = []
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        try:
            sig = inspect.signature(obj)
            params = list(sig.parameters.values())
            # Prefer functions (query, mode) or (query)
            score = 0
            if len(params) == 2:
                score += 2
            if any(p.name.lower() in {"query", "question", "text", "prompt"} for p in params):
                score += 2
            if any(p.name.lower() in {"mode", "method"} for p in params):
                score += 1
            if len(params) == 1:
                score += 1
            if score > 0:
                candidates.append((score, name, obj, sig))
        except Exception:
            continue
    if not candidates:
        return None, None
    candidates.sort(reverse=True)
    return candidates[0][1], candidates[0][2]

picked_name, picked_fn = pick_candidate_function(utils)
if picked_name:
    st.sidebar.success(f"Auto-selected function: `{picked_name}()`")
else:
    st.sidebar.warning(
        "No suitable function found. Using a dummy response. "
        "Add a function in utils_extracted.py that accepts (query) or (query, mode)."
    )

def normalize_output(raw, mode_label):
    """Normalize output into (answer:str, confidence:float|None, method:str)."""
    method = mode_label
    confidence = None

    if raw is None:
        return "(No answer returned)", confidence, method

    # Tuple patterns
    if isinstance(raw, tuple):
        if len(raw) == 3:
            answer, confidence, method = raw
            return str(answer), confidence, str(method)
        if len(raw) == 2:
            answer, maybe = raw
            if isinstance(maybe, (int, float)):
                confidence = float(maybe)
            else:
                method = str(maybe)
            return str(answer), confidence, method
        # Fallback: join tuple
        return " ".join(map(str, raw)), confidence, method

    # Dict patterns
    if isinstance(raw, dict):
        answer = str(raw.get("answer") or raw.get("output") or raw.get("result") or "(No 'answer' field)")
        confidence = raw.get("confidence") or raw.get("score") or raw.get("prob") or None
        method = str(raw.get("method") or raw.get("mode") or method)
        return answer, confidence, method

    # Plain text
    return str(raw), confidence, method

# UI button
if st.sidebar.button("Run", type="primary"):
    start = time.time()
    if picked_fn and query:
        try:
            sig = inspect.signature(picked_fn)
            if len(sig.parameters) >= 2:
                raw = picked_fn(query, mode)
            else:
                raw = picked_fn(query)
        except Exception as e:
            raw = f"Error calling {picked_name}(): {e}"
    else:
        # Dummy
        raw = f"Demo answer for: '{query}'" if query else "Please enter a query."

    answer, confidence, used_method = normalize_output(raw, mode)
    elapsed = time.time() - start

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "—")
    with col2:
        st.metric("Method Used", used_method if used_method else "—")
    with col3:
        st.metric("Response Time (s)", f"{elapsed:.2f}")

st.divider()
with st.expander("Answer", expanded=False):
    st.markdown(
        """
        Place your core logic in `utils_extracted.py` as a function with one of these signatures:

        - `def my_answer_function(query: str) -> ...`
        - `def my_answer_function(query: str, mode: str) -> ...`

        Return formats the app understands:
        - `str` → treated as the answer
        - `(answer: str, confidence: float, method: str)`
        - `(answer: str, confidence: float)`
        - `(answer: str, method: str)`
        - `dict` with keys like `answer`, `confidence`, `method`
        """
    )
