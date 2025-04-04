from ebaysdk import UserAgent
from s3transfer import queue
from botasaurus_driver import driver
from utils import settings
from utils.log_manager import console

pool = queue.Queue()


def _initialize_drivers():
    num_drivers = getattr(settings, "SCRAPER_NUM_DRIVERS", 3)
    console.info(f"Spawning {num_drivers} persistent drivers...")
    for _ in range(num_drivers):
        try:
            user_agent = UserAgent().random if hasattr(UserAgent(), 'random') else 'Mozilla/5.0'
            bot = driver.Driver(user_agent=user_agent, headless=True)
            pool.put(bot)
        except Exception as e:
            console.error(f"Error initializing driver: {e}")

_initialize_drivers()
