

import streamlit as st
from marketing_agents import orchestrate_campaign

st.set_page_config(page_title="AI Marketing Agent", layout="centered")

st.title("AI Marketing Content Generator")

# ---- Inputs ----
brand = st.text_input("Brand name", "ExampleCo")
goal = st.text_area("Campaign goal", "Announce new product launch with 20% off")

channels = st.multiselect(
    "Channels",
    ["email", "sms", "twitter", "linkedin"],
    default=["email", "twitter"]
)

required_phrases = st.text_input("Required phrases", "20% off, limited-time")

rules = st.text_area(
    "Compliance rules (one per line)",
    "include unsubscribe link\nno unverified medical claims"
)

# ---- Run pipeline ----
if st.button("Generate Campaign"):
    brief = {
        "brand_name": brand,
        "goal": goal,
        "channels": channels,
        "required_phrases": required_phrases,
        "rules": [r.strip() for r in rules.splitlines() if r.strip()]
    }

    with st.spinner("Running AI agents..."):
        result = orchestrate_campaign(brief)

    st.success("Campaign generated successfully!")

    # ---- Outputs ----
    st.subheader("Final Selected Content")
    st.write(result["final_choice"])

    st.subheader("Compliance Check")
    st.json(result["compliance"])

    st.subheader("All Variants & Scores")
    for i, v in enumerate(result["variants_scored"]):
        st.markdown(f"### Variant {i+1}")
        st.write(v["variant"])
        st.json(v["score"])