"""Rename app_label from 'core' to 'yeoman_core' for suite shared DB."""

from django.db import migrations

OLD_LABEL = 'core'
NEW_LABEL = 'yeoman_core'

TABLE_RENAMES = [
    ('core_auditlog', 'yeoman_core_auditlog'),
    ('core_notification', 'yeoman_core_notification'),
    ('core_notificationpreference', 'yeoman_core_notificationpreference'),
    ('core_notificationlog', 'yeoman_core_notificationlog'),
    ('core_calendarevent', 'yeoman_core_calendarevent'),
    ('core_calendarsynclog', 'yeoman_core_calendarsynclog'),
]


def _table_exists(connection, table_name):
    return table_name in connection.introspection.table_names()


def forwards(apps, schema_editor):
    for old_name, new_name in TABLE_RENAMES:
        if _table_exists(schema_editor.connection, old_name):
            schema_editor.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')
    schema_editor.execute(
        "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
        [NEW_LABEL, OLD_LABEL],
    )
    schema_editor.execute(
        "UPDATE django_migrations SET app = %s WHERE app = %s",
        [NEW_LABEL, OLD_LABEL],
    )


def backwards(apps, schema_editor):
    for old_name, new_name in TABLE_RENAMES:
        if _table_exists(schema_editor.connection, new_name):
            schema_editor.execute(f'ALTER TABLE "{new_name}" RENAME TO "{old_name}"')
    schema_editor.execute(
        "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
        [OLD_LABEL, NEW_LABEL],
    )
    schema_editor.execute(
        "UPDATE django_migrations SET app = %s WHERE app = %s",
        [OLD_LABEL, NEW_LABEL],
    )


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('yeoman_core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
