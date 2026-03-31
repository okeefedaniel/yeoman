"""
Simple workflow registry. In production keel.workflow, this is more
sophisticated with database-backed workflow definitions, versioning, etc.
"""

_WORKFLOWS = {}


def register_workflow(config):
    """Register a workflow configuration dict."""
    _WORKFLOWS[config['name']] = config


def get_workflow(name):
    """Get a registered workflow by name."""
    return _WORKFLOWS.get(name)


def list_workflows():
    """List all registered workflow names."""
    return list(_WORKFLOWS.keys())
