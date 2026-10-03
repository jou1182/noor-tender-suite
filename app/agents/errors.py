"""Swarm-level errors.

A swarm run must never fabricate results: when an agent lacks the real input it
needs, it raises ``InsufficientInputError`` and the audit is marked ``failed``
with this message (shown to the user) instead of completing with demo data.
"""


class InsufficientInputError(RuntimeError):
    """The audit cannot produce trustworthy output from the supplied inputs."""
