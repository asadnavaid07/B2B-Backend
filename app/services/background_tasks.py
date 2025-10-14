import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.retention_service import RetentionService
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

class BackgroundTaskService:
 
    def __init__(self):
        self._retention_update_task: Optional[asyncio.Task] = None
        self._payment_monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_retention_update_scheduler(self):
        """Start the monthly retention update scheduler"""
        if self._is_running:
            logger.warning("Retention update scheduler is already running")
            return
            
        self._is_running = True
        logger.info("Starting retention update scheduler")
        
        self._retention_update_task = asyncio.create_task(
            self._retention_update_loop()
        )
    
    async def stop_retention_update_scheduler(self):
        """Stop the monthly retention update scheduler"""
        if not self._is_running:
            logger.warning("Retention update scheduler is not running")
            return
            
        self._is_running = False
        
        if self._retention_update_task:
            self._retention_update_task.cancel()
            try:
                await self._retention_update_task
            except asyncio.CancelledError:
                pass
        
        if self._payment_monitoring_task:
            self._payment_monitoring_task.cancel()
            try:
                await self._payment_monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Background task scheduler stopped")
    
    async def start_payment_monitoring_scheduler(self):
        """Start the daily payment monitoring scheduler"""
        if self._payment_monitoring_task and not self._payment_monitoring_task.done():
            logger.warning("Payment monitoring scheduler is already running")
            return
            
        logger.info("Starting payment monitoring scheduler")
        
        self._payment_monitoring_task = asyncio.create_task(
            self._payment_monitoring_loop()
        )
    
    async def stop_payment_monitoring_scheduler(self):
        """Stop the payment monitoring scheduler"""
        if self._payment_monitoring_task:
            self._payment_monitoring_task.cancel()
            try:
                await self._payment_monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Payment monitoring scheduler stopped")
    
    async def _payment_monitoring_loop(self):
        """Main loop for payment monitoring"""
        while True:
            try:
                # Run payment monitoring every 24 hours
                await asyncio.sleep(24 * 3600)  # 24 hours
                
                await self._run_payment_monitoring()
                    
            except asyncio.CancelledError:
                logger.info("Payment monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in payment monitoring loop: {str(e)}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _run_payment_monitoring(self):
        """Run the actual payment monitoring process"""
        logger.info("Starting daily payment monitoring process")
        
        try:
            # Get database session
            async for db in get_db():
                try:
                    # Check for overdue payments and send notifications
                    summary = await PaymentService.check_overdue_payments(db)
                    
                    logger.info(f"Daily payment monitoring completed: {summary}")
                    
                except Exception as e:
                    logger.error(f"Error during payment monitoring: {str(e)}")
                finally:
                    await db.close()
                break
                
        except Exception as e:
            logger.error(f"Error getting database session for payment monitoring: {str(e)}")
    
    async def _retention_update_loop(self):
        """Main loop for retention updates"""
        while self._is_running:
            try:

                now = datetime.utcnow()
                if now.month == 12:
                    next_month = datetime(now.year + 1, 1, 1)
                else:
                    next_month = datetime(now.year, now.month + 1, 1)
                
                seconds_until_next_month = (next_month - now).total_seconds()
                
                logger.info(f"Next retention update scheduled for: {next_month}")
                logger.info(f"Waiting {seconds_until_next_month} seconds until next update")
                
                # Wait until next month
                await asyncio.sleep(seconds_until_next_month)
                
                if self._is_running:
                    await self._run_retention_update()
                    
            except asyncio.CancelledError:
                logger.info("Retention update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in retention update loop: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _run_retention_update(self):
        """Run the actual retention update process"""
        logger.info("Starting monthly retention update process")
        
        try:
            # Get database session
            async for db in get_db():
                try:
                    # Update all users' retention periods
                    summary = await RetentionService.update_all_users_retention_periods(db)
                    
                    logger.info(f"Monthly retention update completed: {summary}")
                    
                    # Get analytics for reporting
                    analytics = await RetentionService.get_retention_analytics(db)
                    logger.info(f"Retention analytics: {analytics}")
                    
                except Exception as e:
                    logger.error(f"Error during retention update: {str(e)}")
                finally:
                    await db.close()
                break
                
        except Exception as e:
            logger.error(f"Error getting database session for retention update: {str(e)}")
    
    async def run_immediate_retention_update(self) -> dict:
        """Run retention update immediately (for manual triggers)"""
        logger.info("Running immediate retention update")
        
        try:
            async for db in get_db():
                try:
                    summary = await RetentionService.update_all_users_retention_periods(db)
                    logger.info(f"Immediate retention update completed: {summary}")
                    return summary
                except Exception as e:
                    logger.error(f"Error during immediate retention update: {str(e)}")
                    raise
                finally:
                    await db.close()
                break
        except Exception as e:
            logger.error(f"Error getting database session for immediate retention update: {str(e)}")
            raise
    
    async def start_all_schedulers(self):
        """Start all background schedulers"""
        await self.start_retention_update_scheduler()
        await self.start_payment_monitoring_scheduler()
        logger.info("All background schedulers started")
    
    async def stop_all_schedulers(self):
        """Stop all background schedulers"""
        await self.stop_retention_update_scheduler()
        await self.stop_payment_monitoring_scheduler()
        logger.info("All background schedulers stopped")
    
    async def run_immediate_payment_monitoring(self) -> dict:
        """Run payment monitoring immediately (for manual triggers)"""
        logger.info("Running immediate payment monitoring")
        
        try:
            async for db in get_db():
                try:
                    summary = await PaymentService.check_overdue_payments(db)
                    logger.info(f"Immediate payment monitoring completed: {summary}")
                    return summary
                except Exception as e:
                    logger.error(f"Error during immediate payment monitoring: {str(e)}")
                    raise
                finally:
                    await db.close()
                break
        except Exception as e:
            logger.error(f"Error getting database session for immediate payment monitoring: {str(e)}")
            raise

# Global instance
background_task_service = BackgroundTaskService()
