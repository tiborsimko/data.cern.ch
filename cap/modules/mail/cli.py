# * coding: utf8 *
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016 CERN.
#
# CERN Analysis Preservation Framework is free software; you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Analysis Preservation Framework is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Analysis Preservation Framework; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 021111307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Mail Cli."""

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_mail import Message

from cap.cli import MutuallyExclusiveOption
from cap.modules.mail.users import (
    get_all_users,
    get_users_by_experiment,
    get_users_by_record,
)


@click.group()
def mail():
    """Mail commands."""
    pass


@mail.command('send')
@click.option(
    '--sender',
    '-s',
    default=None,
    help='Mail sender',
)
@click.option(
    '--subject',
    prompt=True,
    help='Mail subject',
)
@click.option(
    '--body',
    prompt=True,
    help='Mail Body',
)
# recipient options
@click.option(
    '--all-users',
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["experiment", "depid"],
    help='Recipients are all users of CAP',
)
@click.option(
    '--users-from-experiment',
    'experiment',
    type=click.Choice(['cms', 'atlas', 'alice', 'lhcb', 'faser']),
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_users", "depid"],
    help='Recipients are the users of a specific experiment',
)
@click.option(
    '--users-from-record',
    'depid',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_users", "experiment"],
    help='Recipients are the users of a specific record',
)
@click.option(
    '--with-role',
    'role',
    default='admin',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_users", "experiment"],
    help='Define the role that the users need to have to receive the mail',
)
@click.option(
    '--test',
    help='A test recipient that the mail will be sent to',
)
@with_appcontext
def send(sender, subject, body, all_users, depid, experiment, role, test):
    """Create and send mails.

    The `subject` and `body` options are prompts, so they should not be
    provided in the command. If `test` exists, it will be used to send the mail
    to it. The 3 recipient options are mutually exclusive, and can't be used
    together. The `--with-role` option can only be used in the context of
    record users.

    Examples:
        cap mail send --all-users
        cap mail send --users-from-experiment cms
        cap mail send --users-from-record DEPID
        cap mail send --users-from-record DEPID --with-role read

    And with `--test`:
        cap mail send --test testmail@cern.ch --all-users
    """
    if not sender:
        sender = current_app.config['MAIL_DEFAULT_SENDER']

    if all_users:
        recipients = get_all_users()
    elif experiment:
        recipients = get_users_by_experiment(experiment)
    else:
        recipients = get_users_by_record(depid, role=role)

    # if test is provided, the mail will not be sent to the actual recipients
    recipient_list = [test] if test else recipients

    # TODO: Support templates/context and find the
    #       different ways to provide the data

    msg = Message(sender=sender, bcc=recipient_list, subject=subject, body=body)

    current_app.extensions['mail'].send(msg)
    click.secho(
        f"From {sender}\n"
        f"To {recipients}\n"
        f"Subject: {subject}\n"
        f"Body: {body}",
        fg='green',
    )
