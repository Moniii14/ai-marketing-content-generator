#pip install langchain==1.1.3 langchain-openai langchain-community openai chromadb python-dotenv streamlit
# marketing_agents.py
import json
import csv
import datetime
import os
from dotenv import load_dotenv
load_dotenv()  # loads .env file for api key

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_LIVE_LLM = OPENAI_API_KEY is not None

#Conditional LLM initialization(if no api key, use mock mode)
if USE_LIVE_LLM:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
else:
    llm = None  # mock mode

#  LangChain imports
try:
    from langchain_openai import ChatOpenAI
except Exception as e:
    raise ImportError("Please install langchain-openai (pip install langchain-openai). Error: " + str(e))

# community toolkits for React-style agent
try:
    from langchain_community.agent_toolkits import create_react_agent, AgentExecutor
except Exception:
    create_react_agent = None
    AgentExecutor = None

# Tool wrapper (some LangChain installs expose Tool in different places)
try:
    from langchain.tools import Tool
except Exception:
    Tool = None
## NOTE:
# ChromaDB-based vector memory was explored for semantic retrieval (RAG), but due to dependency and portability constraints,,
# replaced with JSONL persistence for portability and ease of demo.

#LLM initialization block
from langchain_openai import ChatOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
else:
    llm = None # llm mock mode to guard dependency from error bcos of no api key

USE_LIVE_LLM = llm is not None

# ---- Utilities ----
def safe_json_load(text: str):
    """Try to parse JSON robustly (fallback to extracting substring)."""
    try:
        return json.loads(text) #if strucutred json parsing return it
    except Exception:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        # final fallback: try to return raw text in a dict
        return {"_raw": text}
    
#Live mode i.e real LLM via OpenAI (LangChain)
def run_prompt_live(prompt: str) -> str:
    """Call the LLM and return plain text (LangChain 1.x compatible)."""

    response = llm.invoke(prompt)

    # langchain response is an AIMessage
    if hasattr(response, "content"):
        return response.content
    # if it fails, return str
    return str(response)

#Mock mode i.e simulated responses (no API, no cost)
def _run_prompt_mock(prompt: str) -> str:
    """Mock LLM responses when OpenAI quota is unavailable."""

    if "persona builder" in prompt:
        return json.dumps({
            "persona": {
                "age_range": "25-35",
                "interests": ["technology", "marketing"],
                "pain_points": ["time constraints", "low engagement"]
            },
            "voice": "clear, friendly, professional",
            "top_ctas": ["Try now", "Learn more", "Get started"]
        })

    if "email copywriter" in prompt.lower():
        return json.dumps({
            "subject_lines": [
                "New Launch - 20% Off Inside",
                "Dont Miss Our Limited-Time Offer",
                "Introducing Our Latest Product"
            ],
            "preheader": "Exclusive launch offer just for you",
            "email_body": "This is a mock email body generated for demonstration. It simulates how the system works end-to-end when a live LLM is connected."
        })
#Ensures nothing crashes, even if prompt doesn’t match
    return json.dumps({
        "approved": True,
        "issues": [],
        "fix_suggestions": []
    })

def run_prompt(prompt: str) -> str:
    if USE_LIVE_LLM:
        return run_prompt_live(prompt)
    return _run_prompt_mock(prompt)




# ---- AGENTS (functions) ----
# Audience Agent -Persona & tone generator
def audience_agent(brief: dict) -> dict:
    prompt = f"""
You are a persona builder. Input brief: {json.dumps(brief, ensure_ascii=False)}
Return strictly valid JSON with keys: persona, voice, top_ctas.
persona: object with age_range, interests, pain_points.
voice: three short adjectives.
top_ctas: array of 3 short CTAs.
"""
    text = run_prompt(prompt)
    return safe_json_load(text) #ensures agent never crashes ,output is always a dictionary

# Content Agent - Email copy generator
def content_agent_email(payload: dict) -> dict:
    """
    payload keys: brand_name, voice, persona, goal, required_phrases
    Returns JSON with: subject_lines (3), preheader, email_body
    """
    prompt = f"""
You are an expert email copywriter for brand {payload.get('brand_name')}.
Voice: {payload.get('voice')}
Persona: {json.dumps(payload.get('persona', {}), ensure_ascii=False)}
Goal: {payload.get('goal')}
Required phrases: {payload.get('required_phrases','')}
Return valid JSON: {{ "subject_lines": ["","",""], "preheader": "", "email_body": "" }}
Email body length: 150-180 words.
"""
    text = run_prompt(prompt)
    return safe_json_load(text)

def content_agent_sms(payload: dict) -> list:
    """
    Create SMS messages. payload keys: persona, goal, required_phrases
    returns list of SMS strings (<=160 chars)
    """
    prompt = f"""
Write 3 SMS messages (each <=160 chars) for persona {json.dumps(payload.get('persona',{}), ensure_ascii=False)}.
Goal: {payload.get('goal')}. Required phrases: {payload.get('required_phrases','')}
Return a JSON array of strings.
"""
    text = run_prompt(prompt)
    return safe_json_load(text)

def content_agent_social(payload: dict) -> list:
    """
    Create social posts. payload: platform, persona, voice, goal
    returns list of short post strings.
    """
    prompt = f"""
Write 6 social posts for platform {payload.get('platform')} using voice {payload.get('voice')}.
Persona: {json.dumps(payload.get('persona',{}), ensure_ascii=False)}.
Goal: {payload.get('goal')}
Each post <=280 chars. Include 1 CTA and 1-2 hashtags.
Return as JSON array.
"""
    text = run_prompt(prompt)
    return safe_json_load(text)


# Compliance Agent - Content compliance checker
def compliance_agent(payload: dict) -> dict:
    """
    payload: content (string), rules (list)
    returns JSON: { approved: bool, issues: [...], fix_suggestions: [...] }
    """
    prompt = f"""
Check the following content for compliance with these rules: {payload.get('rules',[])}
Content: {payload.get('content','')}
Return JSON: {{ "approved": true/false, "issues": ["..."], "fix_suggestions": ["..."] }}
"""
    text = run_prompt(prompt)
    return safe_json_load(text)

# Variation Agent - generates multiple alternative versions
def variation_agent(payload: dict) -> list:
    """
    payload: content, n
    returns list
    """
    prompt = f"Create {payload.get('n',5)} concise variants of the following content. Return a JSON array.\n\n{payload.get('content','')}"
    text = run_prompt(prompt)
    return safe_json_load(text)

# Quality Scorer - evaluates content quality
def quality_scorer(payload: dict) -> dict:
    """
    payload: content
    returns JSON: readability, spamminess, cta_strength, pass (bool)
    """
    prompt = f"""
Score the content from 1-10 for readability, spamminess, and cta_strength.
Return JSON: {{ 'readability': int, 'spamminess': int, 'cta_strength': int, 'pass': bool }}
Content: {payload.get('content','')}
"""
    text = run_prompt(prompt)
    return safe_json_load(text)


## Optional: tool wrappers for future LangChain agent integration
#convert a Python function into a LangChain Tool.If not, it falls back to a simple dictionary representatio
def _wrap_tool(fn, name, description):
    if Tool is not None:
        try:
            #You could use a ReAct-style agent
            return Tool.from_function(func=fn, name=name, description=description)
        except Exception:
            # Some installs require a different signature; fall through to dict
            return {"name": name, "fn": fn, "description": description}
    else:
        return {"name": name, "fn": fn, "description": description}
#Wrapping each agent function as a tool
audience_tool = _wrap_tool(lambda brief_json: audience_agent(json.loads(brief_json)), "audience_agent", "Create persona & voice from brief")
content_email_tool = _wrap_tool(lambda payload_json: content_agent_email(json.loads(payload_json)), "content_agent_email", "Generate email JSON")
content_sms_tool = _wrap_tool(lambda payload_json: content_agent_sms(json.loads(payload_json)), "content_agent_sms", "Generate SMS array")
content_social_tool = _wrap_tool(lambda payload_json: content_agent_social(json.loads(payload_json)), "content_agent_social", "Generate social posts")
compliance_tool = _wrap_tool(lambda payload_json: compliance_agent(json.loads(payload_json)), "compliance_agent", "Check content for compliance")
variation_tool = _wrap_tool(lambda payload_json: variation_agent(json.loads(payload_json)), "variation_agent", "Create variants")
quality_tool = _wrap_tool(lambda payload_json: quality_scorer(json.loads(payload_json)), "quality_scorer", "Score content")
#python_tool = _wrap_tool(PythonREPLTool().run, "python_repl", "Run python code")

TOOLS = [audience_tool, content_email_tool, content_sms_tool, content_social_tool, compliance_tool, variation_tool, quality_tool]

# ---- Memory ----
#memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ---- Agent / Executor creation (attempt) ----
AGENT = None
EXECUTOR = None
if create_react_agent is not None:
    try:
        AGENT = create_react_agent(llm=llm, tools=TOOLS)
        if AgentExecutor is not None:
            EXECUTOR = AgentExecutor(agent=AGENT, tools=TOOLS, verbose=True)
    except Exception as e:
        AGENT = None
        EXECUTOR = None

# ---- Orchestrator (end-to-end) ----
def orchestrate_campaign(brief: dict, require_human_approval: bool = False) -> dict:
    """
    brief keys: brand_name, goal, channels(list), required_phrases, rules(list)
    returns dict with drafts, variants, final_choice
    """
    # 1: Audience
    aud = audience_agent(brief)

    # 2: Content generation per channel (example: email, sms, social)
    content_results = {}
    # EMAIL
    email_payload = {
        "brand_name": brief.get("brand_name"),
        "voice": aud.get("voice"),
        "persona": aud.get("persona"),
        "goal": brief.get("goal"),
        "required_phrases": brief.get("required_phrases", "")
    }
    email_drafts = content_agent_email(email_payload)
    content_results["email"] = email_drafts

    # SMS
    sms_payload = {"persona": aud.get("persona"), "goal": brief.get("goal"), "required_phrases": brief.get("required_phrases","")}
    sms_drafts = content_agent_sms(sms_payload)
    content_results["sms"] = sms_drafts

    # Social (for each platform requested)
    social_results = {}
    for p in brief.get("channels", ["twitter"]):
        plat_payload = {"platform": p, "persona": aud.get("persona"), "voice": aud.get("voice"), "goal": brief.get("goal")}
        social_results[p] = content_agent_social(plat_payload)
    content_results["social"] = social_results

    # 3: Compliance check on email body (example)
    compliance_payload = {"content": email_drafts.get("email_body",""), "rules": brief.get("rules",[])}
    compliance_res = compliance_agent(compliance_payload)

    # If not approved, attempt a single rewrite pass
    if not compliance_res.get("approved", False):
        issues = compliance_res.get("issues", [])
        rewrite_req = email_payload.copy()
        rewrite_req["required_phrases"] = rewrite_req.get("required_phrases", "") + " FIX_ISSUES: " + ", ".join(issues)
        email_drafts = content_agent_email(rewrite_req)
        content_results["email_rewrite"] = email_drafts
        compliance_res = compliance_agent({"content": email_drafts.get("email_body",""), "rules": brief.get("rules",[])})

    # 4: Generate variations for email body
    var_list = variation_agent({"content": email_drafts.get("email_body",""), "n": 5})

    # 5: Score variations and pick best
    scored = []
    for v in var_list:
        sc = quality_scorer({"content": v})
        scored.append({"variant": v, "score": sc})
    # simple selection metric
    def metric(s):
        return s["score"].get("readability",0) - s["score"].get("spamminess",0) + s["score"].get("cta_strength",0)
    scored_sorted = sorted(scored, key=metric, reverse=True)
    final_choice = scored_sorted[0] if scored_sorted else {"variant": email_drafts.get("email_body",""), "score": {}}

    # Optional HITL
    human_ok = True
    if require_human_approval:
        # stub: in prod, show UI and wait; here we auto-approve
        human_ok = True

    # 6: Persist final choice to Chromadb
    try:
        collection.add(documents=[final_choice["variant"]], metadatas=[{"brand": brief.get("brand_name"), "goal": brief.get("goal")}], ids=[os.urandom(8).hex()])
    except Exception as e:
        print("Warning: chroma store failed:", e)

    result = {
        "audience": aud,
        "content": content_results,
        "compliance": compliance_res,
        "variants_scored": scored_sorted,
        "final_choice": final_choice,
        "human_approved": human_ok
    }
    # ✅ Save approved campaign to memory
    if human_ok:
       save_memory(result)
    return result

# ---- Simple publisher stubs ----
def publish_to_csv(text: str, filename: str = "./outgoing_campaign.csv"):
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.utcnow().isoformat(), text])

def save_memory(data, path="memory_store.jsonl"):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def load_memory(path="memory_store.jsonl"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# ---- Example run guard ----
if __name__ == "__main__":
    brief = {
        "brand_name": "ExampleCo",
        "goal": "Announce new product launch with 20% off",
        "channels": ["twitter","linkedin"],
        "required_phrases": "20% off, limited-time",
        "rules": ["include unsubscribe link", "no unverified medical claims"]
    }
    res = orchestrate_campaign(brief)
    print(json.dumps(res["final_choice"], indent=2))

