import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from pathlib import Path
import sys
import os
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logger import JobLogger, setup_logging, get_directory_size

class TestLogger(unittest.TestCase):

    @patch('core.logger.LOG_DIR', Path('/fake/log/dir'))
    @patch('core.logger.Path.mkdir')
    @patch('core.logger.logging.FileHandler')
    @patch('core.logger.logging.StreamHandler')
    def test_setup_logging(self, mock_stream_handler, mock_file_handler, mock_mkdir):
        logger = JobLogger('FULL', 'Monthly')
        
        # Check if LOG_DIR was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Check if handlers were created
        mock_file_handler.assert_called_once()
        mock_stream_handler.assert_called_once()

        # Check if logger methods work
        with self.assertLogs(level='INFO') as cm:
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
        
        self.assertEqual(cm.output, [
            'INFO:core.logger:Test info message',
            'WARNING:core.logger:Test warning message',
            'ERROR:core.logger:Test error message'
        ])

    @patch('core.logger.os.chdir')
    @patch('core.logger.subprocess.check_output')
    @patch('core.logger.subprocess.run')
    def test_log_git_status(self, mock_run, mock_check_output, mock_chdir):
        logger = JobLogger('FULL', 'Monthly')
        mock_check_output.return_value = b'M modified_file.txt\n?? new_file.txt'
        mock_run.return_value.returncode = 0
        
        with self.assertLogs(level='INFO') as cm:
            logger.log_git_status('/test/repo')
        
        self.assertIn('INFO:core.logger:Changes detected in /test/repo:', cm.output)
        self.assertIn('INFO:core.logger:  Modified: modified_file.txt', cm.output)
        self.assertIn('INFO:core.logger:  New file: new_file.txt', cm.output)
        self.assertIn('INFO:core.logger:Changes committed in /test/repo', cm.output)

    @patch('core.logger.get_directory_size')
    @patch('core.logger.logging.Logger.info')
    @patch('core.logger.logging.Logger.warning')
    def test_close(self, mock_warning, mock_info, mock_get_size):
        logger = JobLogger('FULL', 'Monthly')
        mock_get_size.return_value = 950 * 1024 * 1024 * 1024  # 950 GB

        logger.close()

        # Check if all expected log messages were called
        mock_info.assert_any_call(f"========================== Job End: {logger.start_time:%Y%m%d-%w}. Monthly - FULL ===========================")
        mock_info.assert_any_call(f"Backup size (/mnt/e/mnt/aws.local): 950.00 GB")
        
        # Check if warning was logged
        mock_warning.assert_any_call("Consider purging files")

    @patch('os.walk')
    @patch('os.path.getsize')
    def test_get_directory_size(self, mock_getsize, mock_walk):
        mock_walk.return_value = [
            ('/fake/path', ('dir1', 'dir2'), ('file1', 'file2')),
            ('/fake/path/dir1', (), ('file3',)),
            ('/fake/path/dir2', (), ('file4', 'file5'))
        ]
        mock_getsize.side_effect = [100, 200, 300, 400, 500]

        size = get_directory_size('/fake/path')
        self.assertEqual(size, 1500)

    def test_log_backup_operations(self):
        logger = JobLogger('FULL', 'Monthly')
        
        with self.assertLogs(level='INFO') as cm:
            logger.log_backup_start("test_folder")
            logger.log_backup_success("test_archive")
            logger.log_backup_test("test_archive")
            logger.log_backup_failure("failed_archive", "Test error")
            logger.log_backup_stats("stats_archive", 1.5, "00:10:00")

        self.assertIn('INFO:core.logger:Backing up test_folder...', cm.output)
        self.assertIn('INFO:core.logger:Backup successful: test_archive', cm.output)
        self.assertIn('INFO:core.logger:Backup test successful: test_archive', cm.output)
        self.assertIn('ERROR:core.logger:Backup failed: failed_archive', cm.output)
        self.assertIn('ERROR:core.logger:Error: Test error', cm.output)
        self.assertIn('INFO:core.logger:Backup stats for stats_archive:', cm.output)
        self.assertIn('INFO:core.logger:  Size: 1.50 GB', cm.output)
        self.assertIn('INFO:core.logger:  Duration: 00:10:00', cm.output)

    def test_generate_archive_name(self):
        logger = JobLogger('FULL', 'Monthly')
        archive_name = logger.generate_archive_name("TestArchive")
        self.assertRegex(archive_name, r'\d{6} FULL TestArchive\.7z')

if __name__ == '__main__':
    unittest.main()