"""
Custom exception classes.
"""


class TaskCanceledException(RuntimeError):
    """
    Raised to stop task execution when a cancellation command is noticed.
    """
