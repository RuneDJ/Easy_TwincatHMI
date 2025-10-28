"""
Alarm Logger for TwinCAT HMI
Logs alarms to CSV files with daily rotation
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmLogger:
    """Logger for alarm events to CSV files"""
    
    CSV_HEADERS = [
        'Timestamp',
        'Symbol',
        'Value',
        'AlarmType',
        'Priority',
        'State',
        'Message',
        'AcknowledgedBy',
        'AcknowledgedTime'
    ]
    
    def __init__(self, log_directory: str = 'alarm_logs'):
        """
        Initialize alarm logger
        
        Args:
            log_directory: Directory for log files
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        self.current_log_file = None
        self.current_date = None
        
        logger.info(f"AlarmLogger initialized (directory={self.log_directory})")
    
    def log_alarm(self, alarm):
        """
        Log alarm event to CSV
        
        Args:
            alarm: Alarm object
        """
        try:
            # Get log file for today
            log_file = self._get_log_file()
            
            # Check if file needs headers
            file_exists = log_file.exists()
            
            # Open file and write
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers if new file
                if not file_exists:
                    writer.writerow(self.CSV_HEADERS)
                
                # Write alarm data
                row = [
                    alarm.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    alarm.symbol_name,
                    f"{alarm.value:.2f}",
                    alarm.alarm_type.value,
                    alarm.priority.value,
                    alarm.state.value,
                    alarm.message,
                    alarm.acknowledged_by if alarm.acknowledged_by else '',
                    alarm.acknowledged_time.strftime('%Y-%m-%d %H:%M:%S') if alarm.acknowledged_time else ''
                ]
                
                writer.writerow(row)
            
            logger.debug(f"Logged alarm: {alarm.message}")
            
        except Exception as e:
            logger.error(f"Failed to log alarm: {e}")
    
    def log_alarm_state_change(self, alarm):
        """
        Log alarm state change (acknowledged or cleared)
        
        Args:
            alarm: Alarm object
        """
        self.log_alarm(alarm)
    
    def _get_log_file(self) -> Path:
        """
        Get log file path for current date
        
        Returns:
            Path to log file
        """
        today = datetime.now().date()
        
        # Check if we need a new file (date changed)
        if self.current_date != today:
            self.current_date = today
            filename = f"alarm_log_{today.strftime('%Y-%m-%d')}.csv"
            self.current_log_file = self.log_directory / filename
        
        return self.current_log_file
    
    def read_logs(self, date: datetime.date = None, limit: int = 1000) -> List[dict]:
        """
        Read alarm logs from CSV
        
        Args:
            date: Date to read logs for (None = today)
            limit: Maximum number of records to return
            
        Returns:
            List of alarm dictionaries
        """
        if date is None:
            date = datetime.now().date()
        
        filename = f"alarm_log_{date.strftime('%Y-%m-%d')}.csv"
        log_file = self.log_directory / filename
        
        if not log_file.exists():
            logger.warning(f"Log file not found: {log_file}")
            return []
        
        alarms = []
        
        try:
            with open(log_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    alarms.append(row)
                    if len(alarms) >= limit:
                        break
            
            logger.info(f"Read {len(alarms)} alarms from {log_file}")
            return alarms
            
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            return []
    
    def get_log_files(self) -> List[Path]:
        """
        Get list of all log files
        
        Returns:
            List of log file paths
        """
        log_files = sorted(self.log_directory.glob('alarm_log_*.csv'), reverse=True)
        return log_files
    
    def export_to_csv(self, output_file: str, start_date: datetime.date = None, 
                     end_date: datetime.date = None):
        """
        Export alarms to a single CSV file
        
        Args:
            output_file: Output file path
            start_date: Start date for export (None = all)
            end_date: End date for export (None = today)
        """
        try:
            log_files = self.get_log_files()
            
            if end_date is None:
                end_date = datetime.now().date()
            
            # Filter files by date range
            if start_date:
                log_files = [
                    f for f in log_files 
                    if self._extract_date_from_filename(f) >= start_date
                ]
            
            if end_date:
                log_files = [
                    f for f in log_files 
                    if self._extract_date_from_filename(f) <= end_date
                ]
            
            # Combine all logs
            all_alarms = []
            for log_file in log_files:
                with open(log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    all_alarms.extend(list(reader))
            
            # Write to output file
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                writer.writerows(all_alarms)
            
            logger.info(f"Exported {len(all_alarms)} alarms to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export alarms: {e}")
    
    def _extract_date_from_filename(self, filepath: Path) -> datetime.date:
        """
        Extract date from log filename
        
        Args:
            filepath: Path to log file
            
        Returns:
            Date object
        """
        # Format: alarm_log_YYYY-MM-DD.csv
        filename = filepath.stem  # Remove extension
        date_str = filename.replace('alarm_log_', '')
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Delete log files older than specified days
        
        Args:
            days_to_keep: Number of days to keep
        """
        try:
            cutoff_date = datetime.now().date()
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            
            log_files = self.get_log_files()
            deleted_count = 0
            
            for log_file in log_files:
                file_date = self._extract_date_from_filename(log_file)
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old log files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
