import os
import re

import fabric
import fabtools
from fabtools import require

from fabric_helpers import fabtools as fabtech

from ..utils import RequiredDictKeysMixin
from .server import prep_server

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')


def get_virtualenv_dir(project_root):
    with fabric.context_managers.cd(project_root):
        output = fabric.operations.run('poetry env info --path')
    return ansi_escape.sub('', output.strip().replace('\r', '').replace('\n', ''))


def chown(path, user, group=None, recursive=False, use_sudo=False):
    cmd = 'chown {user}'.format(user)
    options = []

    if group:
        cmd += ':{group}'.format(**locals())

    if recursive:
        options.append('-R')

    cmd = cmd + ' '.join(options) + path

    run_fn = use_sudo and fabtools.utils.run_as_root or fabric.api.run
    return run_fn(cmd)


class DjangoApplicationTask(fabric.tasks.Task, RequiredDictKeysMixin):

    server_debs = [
        'nginx-extras',
        'supervisor',
        'redis-server',
        'build-essential',
        'python3.7',
        'python3-distutils',
        'libpython3.7-dev',
        'libpython2.7-dev',
        'python3-venv',  # ensurepip for poetry
        'python3.7-venv',  # same
    ]

    server_fabtools_reqs = [
        fabtech.require.postgres.server,
        fabtools.require.python.pip,
        fabtech.require.python.poetry,
    ]

    option_keys = [  # required option keys, if you subclass, update this!
        'project_name',
        'project_root',
        'wsgi_module',
        'nginx_server_name',
        'nginx_server_alias',
        'nginx_template_source',
        'pg_user',
        'pg_password',
        'pg_db_name',
        'DJANGO_SETTINGS_MODULE',
        'SECRET_KEY',
        'gunicorn_port',
        'local_cert_pattern',
        'remote_cert_dir',
        'app_user',
        'app_group',
    ]

    option_optional_keys = ['nginx_extra_server_conf']  # custom stuff for the template

    def __init__(self, options={}, *args, **kwargs):
        RequiredDictKeysMixin.__init__(self, options)

        self.options = options
        super().__init__(*args, **kwargs)

    def run(self):
        opt = self.options  # keep things more consise

        # pre-installation preparation
        fabric.tasks.execute(prep_server)
        require.deb.update_index()

        debs = self.server_debs
        if 'server_debs_extra' in opt and opt['server_debs_extra']:
            debs += opt['server_debs_extra']
        require.deb.packages(debs)

        # installation
        for req in self.server_fabtools_reqs:
            req()

        # configuration
        fabric.contrib.files.append(
            '/etc/environment', 'SECRET_KEY={SECRET_KEY}'.format(**opt)
        )

        # config db
        """Configure postgres database."""
        fabtech.require.postgres.user(
            opt['pg_user'], opt['pg_password'], superuser=True, encrypted_password=True
        )
        if not fabtech.postgres.database_exists(opt['pg_db_name']):
            fabtech.postgres.create_database(
                name=opt['pg_db_name'], owner=opt['pg_user']
            )

        # clone app
        fabtech.require.git.working_copy(
            remote_url=opt['project_vcs'], path=opt['project_root'], recursive=True
        )

        # configure application virtualenv and packages
        with fabric.context_managers.cd(opt['project_root']):
            fabric.api.run('poetry install')

        # now we can initialize some variables that depend on poetry
        venv_dir = get_virtualenv_dir(opt['project_root'])
        gunicorn_bin = os.path.join(venv_dir, 'bin', 'gunicorn')
        print('venv_dir: ', venv_dir)
        print('gunicorn_dir: ', gunicorn_bin)

        # put ssl certs
        require.files.directory(
            path=opt['remote_cert_dir'], owner=opt['app_user'], group=opt['app_group']
        )
        fabric.operations.put(opt['local_cert_pattern'], opt['remote_cert_dir'])

        require.nginx.site(
            server_name=opt['nginx_server_name'],
            template_source=opt['nginx_template_source'],
            server_alias=opt['nginx_server_alias'],
            server_port=80,
            app_port=opt['gunicorn_port'],
            ssl_cert=os.path.join(
                opt['remote_cert_dir'], '{project_name}.pem'.format(**opt)
            ),
            ssl_key=os.path.join(
                opt['remote_cert_dir'], '{project_name}.key'.format(**opt)
            ),
            project_name=opt['project_name'],
            extra_server_conf=opt.get('nginx_extra_server_conf', ''),
        )

        require.files.directory(
            path='/var/log/gunicorn', owner=opt['app_user'], group=opt['app_group']
        )
        require.supervisor.process(
            opt['project_name'],
            command=' '.join(
                [
                    gunicorn_bin,
                    '--workers=5',
                    '--max-requests=5',  # prevent memleaks, autorestart workers
                    '--max-requests-jitter=2',  # prevent workers restart same time
                    '--bind 127.0.0.1:{gunicorn_port}',
                    '--chdir {project_root}',
                    '--error-logfile /var/log/gunicorn/{project_name}-error.log',
                    '--access-logfile /var/log/gunicorn/{project_name}-access.log',
                    '--user {app_user} --group {app_group}',
                    opt['wsgi_module'],
                ]
            ).format(**opt),
            environment=','.join(
                [
                    'DJANGO_SETTINGS_MODULE={DJANGO_SETTINGS_MODULE}',
                    'SECRET_KEY={SECRET_KEY}',
                ]
            ).format(**opt),
            stdout_logfile='/var/log/supervisor/{project_name}.log'.format(**opt),
            stderr_logfile='/var/log/supervisor/{project_name}.log'.format(**opt),
            autostart=True,
            autorestart=True,
        )
        fabtools.supervisor.restart_process(opt['project_name'])


class UpdateApplicationTask(fabric.tasks.Task, RequiredDictKeysMixin):

    option_keys = ['project_name', 'project_vcs', 'project_root']

    def __init__(self, options={}, *args, **kwargs):
        # verify all required settings are exist
        RequiredDictKeysMixin.__init__(self, options)

        self.options = options
        super().__init__(*args, **kwargs)

    def run(self):
        opt = self.options

        # clone app
        fabtech.require.git.working_copy(
            remote_url=opt['project_vcs'],
            path=opt['project_root'],
            recursive=True,
            user=opt['app_user'],
        )

        fabtools.supervisor.restart_process(opt['project_name'])


class FlushRedisNamespaceTask(fabric.tasks.Task, RequiredDictKeysMixin):
    option_keys = ['redis_db', 'redis_namespace']

    def __init__(self, options={}, *args, **kwargs):
        # verify all required settings are exist
        RequiredDictKeysMixin.__init__(self, options)

        self.options = options
        super().__init__(*args, **kwargs)

    def run(self):
        opt = self.options
        fabric.api.run(
            "redis-cli -n {redis_db} keys '{redis_namespace}:*' "
            '| xargs redis-cli -n {redis_db} DEL'.format(**opt),
            shell=True,
        )


class RunDjangoCommandTask(fabric.tasks.Task, RequiredDictKeysMixin):

    """Run with virtualenv + django settings + cd'd in django environment."""

    option_keys = ['project_root', 'DJANGO_SETTINGS_MODULE']

    def __init__(self, cmd, options={}, *args, **kwargs):
        # verify all required settings are exist
        RequiredDictKeysMixin.__init__(self, options)

        self.options = options
        self.cmd = cmd

        super().__init__(*args, **kwargs)

    def run(self):
        options = self.options

        venv_dir = get_virtualenv_dir(options['project_root'])
        with fabtools.python.virtualenv(venv_dir), fabric.context_managers.cd(
            options['project_root']
        ), fabric.context_managers.shell_env(
            DJANGO_SETTINGS_MODULE=options['DJANGO_SETTINGS_MODULE']
        ):
            fabric.api.run(self.cmd)
