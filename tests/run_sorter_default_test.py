from src.inbox_sorter.main import main
from pathlib import Path

if __name__ == "__main__":
    """
    This script serves as the entry point for running the default sorting test.
    """
    # Define default paths for inbox and output
    base_dir = Path(__file__).resolve().parent.parent
    default_inbox_path = base_dir / "dataset" / "inbox"
    default_output_path = base_dir / "test_output"
    # Call the main function with the default paths
    main(default_inbox_path, default_output_path)

def run_sorter_default_test():
    """
    This function runs the default sorting test by calling the main function with default paths.
    """
    # Define default paths for inbox and output
    base_dir = Path(__file__).resolve().parent.parent
    default_inbox_path = base_dir / "dataset" / "inbox"
    default_output_path = base_dir / "test_output"
    # Call the main function with the default paths
    main(default_inbox_path, default_output_path)