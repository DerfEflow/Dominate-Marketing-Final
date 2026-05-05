from openai import OpenAI
import json, os

def _get_client():
    """Lazy OpenAI client — avoids import-time credential errors."""
    from openai import OpenAI
    import os
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

client = None  # use _get_client() to get the real client
def build_ad_script(business_url, region, goal, brand_voice, cta, length_sec):
    prompt = f"""
Return JSON ONLY with keys:
voiceover_lines (array of short lines),
on_screen_text (array of objects {{t:int,text:string}}),
visuals (array of short phrases).

Rules:
- Total runtime ~{length_sec}s. Assume ~2.5 words/sec.
- Each voiceover line ≤ 12 words.
- On-screen text ≤ 6 words per item.
- Keep visuals as short phrases.
URL: {business_url}
Region: {region}
Goal: {goal}
Voice: {brand_voice}
CTA: {cta}
"""
    resp = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.6,
        max_tokens=700,
        messages=[{"role":"user","content":prompt}]
    )
    content = resp.choices[0].message.content
    if not content:
        return {"error": "Empty response from OpenAI API"}
    data = json.loads(content)

    # Hard guardrails so we never pass an empty script:
    lines = data.get("voiceover_lines") or []
    if not lines:
        # fallback from on_screen_text, last resort
        ost = [x.get("text","") for x in (data.get("on_screen_text") or [])]
        lines = [t for t in ost if t]
        data["voiceover_lines"] = lines

    return data