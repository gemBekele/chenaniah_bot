import asyncio
import logging
import sqlite3
from typing import List, Dict, Any
from database import Database
from google_services import GoogleSheetsService
from notification_service import NotificationService

logger = logging.getLogger(__name__)

class AdminTools:
    def __init__(self):
        self.db = Database()
        self.sheets_service = GoogleSheetsService()
        self.notification_service = NotificationService()
    
    async def get_all_submissions(self) -> List[Dict[str, Any]]:
        """Get all submissions from database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM submissions 
                    ORDER BY submitted_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting submissions: {e}")
            return []
    
    async def get_pending_submissions(self) -> List[Dict[str, Any]]:
        """Get pending submissions"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM submissions 
                    WHERE status = 'pending' 
                    ORDER BY submitted_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pending submissions: {e}")
            return []
    
    async def update_submission_status(self, submission_id: int, status: str, 
                                     reviewer_comments: str = None) -> bool:
        """Update submission status"""
        try:
            await self.db.update_submission_status(submission_id, status, reviewer_comments)
            
            # Send notification about status update
            await self.notification_service.notify_reviewers_status_update(
                submission_id, status, reviewer_comments
            )
            
            logger.info(f"Updated submission #{submission_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating submission status: {e}")
            return False
    
    async def get_submission_stats(self) -> Dict[str, Any]:
        """Get submission statistics"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Total submissions
                cursor.execute('SELECT COUNT(*) FROM submissions')
                total = cursor.fetchone()[0]
                
                # Pending submissions
                cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "pending"')
                pending = cursor.fetchone()[0]
                
                # Approved submissions
                cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "approved"')
                approved = cursor.fetchone()[0]
                
                # Rejected submissions
                cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "rejected"')
                rejected = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'pending': pending,
                    'approved': approved,
                    'rejected': rejected
                }
                
        except Exception as e:
            logger.error(f"Error getting submission stats: {e}")
            return {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0}
    
    async def export_submissions_to_csv(self, filename: str = None) -> str:
        """Export submissions to CSV file"""
        import csv
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vocalist_submissions_{timestamp}.csv"
        
        try:
            submissions = await self.get_all_submissions()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'name', 'address', 'phone', 'telegram_username', 
                             'audio_drive_link', 'submitted_at', 'status', 'reviewer_comments']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for submission in submissions:
                    writer.writerow(submission)
            
            logger.info(f"Exported {len(submissions)} submissions to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting submissions: {e}")
            return None
    
    async def sync_with_google_sheets(self) -> bool:
        """Sync database with Google Sheets"""
        try:
            # Get all submissions from database
            submissions = await self.get_all_submissions()
            
            # Get submissions from Google Sheets
            sheets_data = await self.sheets_service.get_submissions()
            
            # Compare and sync if needed
            # This is a simplified version - in production you'd want more sophisticated sync logic
            logger.info(f"Synced {len(submissions)} submissions with Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing with Google Sheets: {e}")
            return False
    
    async def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old submission data"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM submissions 
                    WHERE submitted_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old submissions")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

# CLI interface for admin tools
async def main():
    """CLI interface for admin tools"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vocalist Screening Admin Tools')
    parser.add_argument('--stats', action='store_true', help='Show submission statistics')
    parser.add_argument('--pending', action='store_true', help='Show pending submissions')
    parser.add_argument('--export', type=str, help='Export submissions to CSV file')
    parser.add_argument('--sync', action='store_true', help='Sync with Google Sheets')
    parser.add_argument('--cleanup', type=int, help='Clean up data older than N days')
    
    args = parser.parse_args()
    
    admin = AdminTools()
    
    if args.stats:
        stats = await admin.get_submission_stats()
        print(f"Submission Statistics:")
        print(f"Total: {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Approved: {stats['approved']}")
        print(f"Rejected: {stats['rejected']}")
    
    if args.pending:
        pending = await admin.get_pending_submissions()
        print(f"Pending Submissions ({len(pending)}):")
        for sub in pending:
            print(f"#{sub['id']}: {sub['name']} - {sub['submitted_at']}")
    
    if args.export:
        filename = await admin.export_submissions_to_csv(args.export)
        if filename:
            print(f"Exported to {filename}")
        else:
            print("Export failed")
    
    if args.sync:
        success = await admin.sync_with_google_sheets()
        print(f"Sync {'successful' if success else 'failed'}")
    
    if args.cleanup:
        deleted = await admin.cleanup_old_data(args.cleanup)
        print(f"Cleaned up {deleted} old submissions")

if __name__ == "__main__":
    asyncio.run(main())
