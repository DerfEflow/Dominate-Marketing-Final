def build_veo3_request(script_json: dict, brand_voice: str, cta: str, length_sec: int, logo_url: str | None):
    lines = script_json.get("voiceover_lines") or []
    script_text = " ".join([ln.strip() for ln in lines if ln.strip()])  # ← never empty if step 1 worked
    visuals = script_json.get("visuals") or []
    visuals = visuals + [f"End card with logo and CTA: {cta}"]

    return {
        "script": script_text,
        "length_sec": length_sec,
        "style": f"{brand_voice} documentary realism",
        "voice": "confident American male",
        "music": "cinematic, modern",
        "sfx": ["subtle whooshes", "light ambience"],
        "visuals": visuals,
        "brand_assets": {"logo_url": logo_url or "", "color_hint": "steel gray"},
        "output": {"format": "mp4", "aspect": "9:16"},
    }