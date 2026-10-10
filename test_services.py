
from citypulse import tools

tests = [
    ("Weather", lambda: tools.fetch_weather("Lucknow")),
    ("News", lambda: tools.fetch_news("Lucknow", 3)),
]

for name, test in tests:
    try:
        result = test()
        print(f"\n{name}: SUCCESS")

        if name == "Weather":
            print(result)
        else:
            print("Articles returned:", len(result))

    except Exception as exc:
        print(f"\n{name}: FAILED")
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))
