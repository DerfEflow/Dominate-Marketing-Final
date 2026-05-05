# test_ingest.py
from services.ingest import fetch_site_profile

if __name__ == "__main__":
    url = input("Paste a product/services page URL and press Enter:\n> ").strip()
    profile = fetch_site_profile(url)

    print("\n=== BASIC INFO ===")
    print("Title:", profile.title)
    print("Description:", profile.description)
    print("Keywords:", profile.keywords[:10])

    print("\n=== FIRST 3 PARAGRAPHS ===")
    for i, p in enumerate(profile.paragraphs[:3], start=1):
        print(f"{i}. {p}\n")

    print("=== Offers (guesses) ===")
    for o in profile.offers:
        print("-", o)