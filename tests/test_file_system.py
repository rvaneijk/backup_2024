import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.file_system import check_mount, unmount, ensure_dir_exists

class TestFileSystem(unittest.TestCase):

    @patch('core.file_system.Path.is_mount')
    @patch('core.file_system.subprocess.run')
    @patch('core.file_system.logger.info')
    @patch('core.file_system.logger.error')
    @patch('core.file_system.sys.exit')
    @patch('core.file_system.AWS_DIR')
    @patch('core.file_system.BASE_DIR')
    def test_check_mount(self, mock_base_dir, mock_aws_dir, mock_exit, mock_error, mock_info, mock_run, mock_is_mount):
        # Setup
        mock_base_dir.is_mount = mock_is_mount
        mock_aws_dir.exists.return_value = True

        # Test when already mounted
        mock_is_mount.return_value = True
        check_mount()
        mock_info.assert_any_call("Backup disk is already mounted.")
        mock_info.assert_any_call(f"Backup directory {mock_aws_dir} is accessible.")
        mock_run.assert_not_called()

        # Reset mocks
        mock_info.reset_mock()
        mock_error.reset_mock()
        mock_exit.reset_mock()
        mock_run.reset_mock()

        # Test when not mounted and mount succeeds
        mock_is_mount.return_value = False
        mock_run.return_value.returncode = 0
        check_mount()
        mock_info.assert_any_call("Backup disk is not mounted. Attempting to mount...")
        mock_info.assert_any_call("Backup disk mounted successfully.")
        mock_info.assert_any_call(f"Backup directory {mock_aws_dir} is accessible.")
        mock_run.assert_called_once()

        # Reset mocks
        mock_info.reset_mock()
        mock_error.reset_mock()
        mock_exit.reset_mock()
        mock_run.reset_mock()

        # Test when not mounted and mount fails
        mock_is_mount.return_value = False
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Mount failed"
        check_mount()
        mock_error.assert_called_with("Failed to mount the backup disk: Mount failed")
        mock_exit.assert_called_with(1)

        # Test when AWS_DIR doesn't exist
        mock_is_mount.return_value = True
        mock_aws_dir.exists.return_value = False
        check_mount()
        mock_error.assert_called_with(f"Backup directory {mock_aws_dir} does not exist. Please check your USB drive.")
        mock_exit.assert_called_with(1)

    @patch('core.file_system.Path.is_mount')
    @patch('core.file_system.subprocess.run')
    @patch('core.file_system.logger.info')
    @patch('core.file_system.logger.error')
    def test_unmount(self, mock_error, mock_info, mock_run, mock_is_mount):
        # Test when mounted and unmount succeeds
        mock_is_mount.return_value = True
        mock_run.return_value.returncode = 0
        unmount()
        mock_run.assert_called_once()
        mock_info.assert_any_call("Unmounting backup disk...")
        mock_info.assert_any_call("Backup disk unmounted successfully.")
        mock_error.assert_not_called()

        # Reset mocks
        mock_run.reset_mock()
        mock_info.reset_mock()
        mock_error.reset_mock()

        # Test when mounted and unmount fails
        mock_is_mount.return_value = True
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Unmount failed"
        unmount()
        mock_run.assert_called_once()
        mock_error.assert_called_once_with("Failed to unmount the backup disk: Unmount failed")

        # Reset mocks
        mock_run.reset_mock()
        mock_info.reset_mock()
        mock_error.reset_mock()

        # Test when not mounted
        mock_is_mount.return_value = False
        unmount()
        mock_run.assert_not_called()
        mock_info.assert_called_with("Backup disk is not mounted. No need to unmount.")

    @patch('core.file_system.Path')
    @patch('core.file_system.logger.info')
    @patch('core.file_system.logger.error')
    @patch('core.file_system.sys.exit')
    def test_ensure_dir_exists(self, mock_exit, mock_error, mock_info, mock_path):
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        # Test when directory doesn't exist
        mock_path_instance.exists.return_value = False
        ensure_dir_exists('/test/dir')
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_info.assert_called_once()
        self.assertIn("Created directory", mock_info.call_args[0][0])

        # Reset mocks
        mock_path_instance.mkdir.reset_mock()
        mock_info.reset_mock()

        # Test when directory already exists
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        ensure_dir_exists('/test/dir')
        mock_path_instance.mkdir.assert_not_called()

        # Test when path exists but is not a directory
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = False
        ensure_dir_exists('/test/file')
        mock_error.assert_called_once()
        self.assertIn("Path exists but is not a directory", mock_error.call_args[0][0])
        mock_exit.assert_called_with(1)

        # Reset mocks
        mock_error.reset_mock()
        mock_exit.reset_mock()

        # Test permission error
        mock_path_instance.exists.return_value = False
        mock_path_instance.mkdir.side_effect = PermissionError("Permission denied")
        ensure_dir_exists('/test/no_permission')
        mock_error.assert_called_once()
        self.assertIn("Permission denied when trying to create directory", mock_error.call_args[0][0])
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()