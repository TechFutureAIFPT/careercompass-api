import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.crawler.tuyensinh247 import TuyenSinh247Crawler
from app.crawler.vietnamnet import VietnamNetExamCrawler

logger = logging.getLogger("tasks.scheduler")

scheduler = AsyncIOScheduler()

async def scheduled_tuyensinh247_job():
    """Weekly crawler for university admission scores on Tuyensinh247."""
    logger.info("Executing scheduled job: Weekly Tuyensinh247 admission scores crawler...")
    try:
        crawler = TuyenSinh247Crawler()
        result = await crawler.run()
        logger.info(f"Weekly Tuyensinh247 crawler finished: {result}")
    except Exception as e:
        logger.error(f"Weekly Tuyensinh247 crawler failed: {e}", exc_info=True)

async def scheduled_vietnamnet_job():
    """Daily graduation exam score crawler during examination season (June - August)."""
    logger.info("Executing scheduled job: Daily VietnamNet graduation exam score crawler...")
    try:
        # Crawl top 1000 records daily for major provinces
        crawler = VietnamNetExamCrawler(year=2024)
        result = await crawler.run(start_idx=1, end_idx=500, province_code="01")
        logger.info(f"Daily VietnamNet exam crawler finished: {result}")
    except Exception as e:
        logger.error(f"Daily VietnamNet exam crawler failed: {e}", exc_info=True)

def start_scheduler():
    """Initializes and registers offline periodic crawler tasks."""
    if scheduler.running:
        return

    # 1. Tuyensinh247: Run every Sunday at 02:00 AM
    scheduler.add_job(
        scheduled_tuyensinh247_job,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_tuyensinh247_crawl",
        name="Crawl Tuyensinh247 định kỳ hàng tuần",
        replace_existing=True
    )

    # 2. VietnamNet: Run daily at 03:00 AM during June, July, August (Months 6-8)
    scheduler.add_job(
        scheduled_vietnamnet_job,
        trigger=CronTrigger(month="6-8", hour=3, minute=0),
        id="daily_vietnamnet_exam_crawl",
        name="Crawl Điểm thi THPT VietnamNet mùa thi (Tháng 6 - 8)",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Admission data crawler scheduler started successfully (Weekly Tuyensinh247, Daily VietnamNet)")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Crawler scheduler stopped.")
