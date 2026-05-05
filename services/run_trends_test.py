from services.trends import get_trends

if __name__ == "__main__":
    trends = get_trends(limit=5)
    print("\n=== FAKE TRENDS ===")
    for t in trends:
        print(f"{t.platform} | {t.kind} | {t.title} | score: {t.popularity_score}")