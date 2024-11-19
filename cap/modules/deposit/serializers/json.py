# -*- coding: utf-8 -*-
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
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""CAP Basic Serializers."""

from flask import jsonify, make_response

from invenio_deposit.serializers import json_file_serializer, file_serializer

from cap.modules.deposit.api import CAPDeposit
from cap.modules.deposit.links import links_factory as deposit_links_factory
from cap.modules.records.serializers.json import CAPJSONSerializer


class DepositSerializer(CAPJSONSerializer):
    """Serializer for records v1 in JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Preprocess record serializing for record retrievals from the db.

        Call base serializer with deposit_links_factory explicitly.
        (bug in invenio doesn't pass correct one on deposit actions
        (e.g. /actions/publish)
        """
        result = super().preprocess_record(
            pid, record, links_factory=deposit_links_factory
        )

        deposit = CAPDeposit.get_record(pid.object_uuid)
        result['deposit'] = deposit

        # add bucket id for fetching files later
        if deposit.files:
            result['bucket'] = deposit.files.bucket
        return result


def json_files_serializer(objs, status=None):
    """JSON Files Serializer.

    :parma objs: A list of:class:`invenio_files_rest.models.ObjectVersion`
        instances.
    :param status: A HTTP Status. (Default: ``None``)
    :returns: A Flask response with JSON data.
    :rtype: :py:class:`flask.Response`.
    """
    files = [file_serializer(obj) for obj in objs]
    response = make_response(jsonify(files), status)
    return response


def json_file_response(obj=None, pid=None, record=None, status=None):
    """JSON Files/File serializer.

    :param obj: A :class:`invenio_files_rest.models.ObjectVersion` instance or
        a :class:`invenio_records_files.api.FilesIterator` if it's a list of
        files.
    :param pid: PID value. (not used)
    :param record: The record metadata. (not used)
    :param status: The HTTP status code.
    :returns: A Flask response with JSON data.
    :rtype: :py:class:`flask.Response`.
    """
    from invenio_records_files.api import FilesIterator
    if isinstance(obj, FilesIterator):
        return json_files_serializer(obj, status=status)
    else:
        return json_file_serializer(obj, status=status)
