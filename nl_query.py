import os
import time
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def answer_query(question: str, df: pd.DataFrame) -> tuple[str, str]:
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    schema_info = f"""
DataFrame name: df
Columns: {list(df.columns)}
Sample data:
{df.head(3).to_string()}

Column descriptions:
- state              : Indian state name (string)
- nh_length_km       : Total National Highway length in km (int)
- km_completed_fy25  : NH km completed in FY2024-25 (int)
- completion_pct     : Project completion percentage (float)
- budget_crore       : Budget allocated in Rs Crore (int)
- spend_crore        : Budget actually spent in Rs Crore (int)
- pmgsy_km           : PMGSY rural road length completed in km (int)
- active_projects    : Number of active infrastructure projects (int)
"""

    prompt = f"""
You are a Python data analyst. You have a pandas DataFrame called `df` with India infrastructure data.

{schema_info}

User question: "{question}"

STRICT RULES:
1. Write pandas Python code to answer the question
2. The LAST LINE must assign a human-readable string to `result`
3. `result` must DIRECTLY answer the question with real numbers and units
4. For rankings show top 3-5 with values
5. Keep `result` concise — 1 to 6 lines max
6. Do NOT use print()
7. Return ONLY raw Python code — no markdown, no ``` fences, no explanation

EXAMPLE for "which state has highest completion rate":
top = df.loc[df['completion_pct'].idxmax()]
result = f"{{top['state']}} has the highest completion rate at {{top['completion_pct']:.1f}}%"

EXAMPLE for "top 3 states by budget":
top3 = df.nlargest(3, 'budget_crore')[['state', 'budget_crore']]
result = "Top 3 states by budget:\\n" + "\\n".join(
    f"{{i+1}}. {{row['state']}}: Rs {{row['budget_crore']:,}} Crore"
    for i, (_, row) in enumerate(top3.iterrows())
)
"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(45 * (attempt + 1))
            else:
                return f"⚠️ API Error: {str(e)}", ""

    # Clean the response — strip markdown fences if Gemini adds them
    code = response.text.strip()
    code = code.replace("```python", "").replace("```", "").strip()

    # Execute the code
    exec_globals = {"df": df.copy(), "pd": pd}
    try:
        exec(code, exec_globals)
        answer = exec_globals.get("result", None)

        if answer is None:
            return "⚠️ Gemini did not return a clear answer. Try rephrasing your question.", code

        return str(answer), code

    except Exception as e:
        return f"⚠️ Code execution error: {str(e)}\n\nTry rephrasing your question.", code