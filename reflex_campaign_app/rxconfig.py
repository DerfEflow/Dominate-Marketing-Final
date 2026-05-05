import reflex as rx

config = rx.Config(
    app_name="visual_tester",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"]
)