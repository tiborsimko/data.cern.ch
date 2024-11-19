# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016, 2017 CERN.
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
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Tests for experiments module utils."""

import subprocess

from unittest.mock import patch
from pytest import raises

from cap.modules.experiments.utils.common import kinit


@patch('cap.modules.experiments.utils.common.check_output')
def test_kinit_decorator(subprocess_mock, app):
    @kinit('user@CERN.CH', 'user.keytab')
    def function(x):
        subprocess_mock.assert_called_with(
            'kinit -kt /etc/keytabs/user.keytab user@CERN.CH', shell=True)
        return x

    function('return_value')

    subprocess_mock.assert_called_with('kdestroy', shell=True)


def test_kinit_decorator_when_non_existing_keytab_file(app):
    @kinit('user@CERN.CH', 'non-existing.keytab')
    def function(x):
        return x

    with raises(subprocess.CalledProcessError):
        function('return_value')
