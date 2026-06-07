import os
import time
import threading
import logging
from main_app import app


def _start_in_process_scheduler():
    """Run the automation scheduler in a background thread (local/dev convenience).

    In production the dedicated `worker` process (see Procfile) does this. Locally
    there's no separate worker, so — unless disabled with RUN_SCHEDULER=false — we
    tick the engine in-process every minute so the post→publish and research-refresh
    loops are visible during review. Each tick runs inside an app context.
    """
    def _loop():
        from services.social_scheduler import SocialScheduler
        scheduler = SocialScheduler()
        while True:
            try:
                with app.app_context():
                    scheduler.process_due_posts()
                    scheduler.process_research_refresh()
            except Exception as e:
                logging.error(f"In-process scheduler error: {e}")
            time.sleep(60)
    threading.Thread(target=_loop, daemon=True).start()
    logging.info("In-process automation scheduler started")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    if os.environ.get('RUN_SCHEDULER', 'true').lower() in ('1', 'true', 'yes', 'on'):
        _start_in_process_scheduler()
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
