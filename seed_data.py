#!/usr/bin/env python
"""
Convenience wrapper for: python manage.py seed_data
"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yeoman_project.settings')
    import django
    django.setup()
    from django.core.management import call_command
    call_command('seed_data')
