import os
from subprocess import check_output

from charms import apt
from charms.reactive import when_not, when, set_state
from charmhelpers.core.hookenv import (
    log,
    open_port, status_set)
import jinja2

TEMPLATES_DIR = 'templates'


def render_template(template_name, context, template_dir=TEMPLATES_DIR):
    templates = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir))
    template = templates.get_template(template_name)
    return template.render(context)


@when('ceph-admin.available')
def connect_to_ceph(ceph_client):
    charm_ceph_conf = os.path.join(os.sep,
                                   'etc',
                                   'ceph',
                                   'ceph.conf')
    cephx_key = os.path.join(os.sep,
                             'etc',
                             'ceph',
                             'ceph.client.admin.keyring')

    ceph_context = {
        'auth_supported': ceph_client.auth(),
        'mon_hosts': ceph_client.mon_hosts(),
        'fsid': ceph_client.fsid(),
        'use_syslog': 'true',
        'loglevel': '0',
    }

    try:
        with open(charm_ceph_conf, 'w') as ceph_conf:
            ceph_conf.write(render_template('ceph.conf', ceph_context))
    except IOError as err:
        log("IOError writing ceph.conf: {}".format(err.message))

    try:
        with open(cephx_key, 'w') as key_file:
            key_file.write("[client.admin]\n\tkey = {}\n".format(
                ceph_client.key()
            ))
    except IOError as err:
        log("IOError writing ceph.client.admin.keyring: {}".format(err.message))
    set_state('ceph.configured')


@when_not('apt.installed.openattic')
def setup_debconf():
    # Tell debconf where to find answers fo the openattic questions
    charm_debconf = os.path.join(os.getenv('CHARM_DIR'),
                                 'files',
                                 'openattic-answers')
    check_output(['debconf-set-selections', charm_debconf])
    # Install openattic in noninteractive mode
    apt.queue_install(
        [
            "openattic",
            "openattic-module-ceph",
            "linux-image-extra-{}".format(os.uname()[2])
        ])


@when_not('ceph.configured')
@when('apt.installed.openattic')
def waiting_for_relations():
    status_set('waiting', 'waiting for relations to join')


@when('ceph.configured')
@when('apt.installed.openattic')
def configure_openattic():
    status_set('maintenance', 'configuring openattic')
    try:
        # Setup openattic post apt-get install and start the service
        check_output(['oaconfig', 'install', '--allow-broken-hostname'])
    except OSError as e:
        log("oaconfig install failed with {}".format(e))
        raise e
    open_port(port=80)
    status_set('active', '')
