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

from __future__ import absolute_import, print_function

from marshmallow import Schema, fields
from flask import jsonify


class CERNProfileSchema(Schema):
    display_name = fields.Str(dump_only=True)
    common_name = fields.Str(dump_only=True)
    department = fields.Str(dump_only=True)
    home_institute = fields.Str(dump_only=True)


class CERNRemoteSchema(Schema):
    email = fields.Str(dump_only=True)
    profile = fields.Method('get_profile', dump_only=True)

    def get_profile(self, obj):
        return CERNProfileSchema().dump(obj.get('profile', {})).data


def get_user_data(user):
    """Retrieve user data from RemoteAccount."""
    from cap.modules.user.utils import get_remote_account_by_id
    return get_remote_account_by_id(user.id)


def user_serializer(user_data):
    """User profile serializer."""
    def serializer(user, code=200, headers=None):
        data = user_data(user)
        response = jsonify(data)
        response.status_code = code

        if headers:
            response.headers.extend(headers)
        return response
    return serializer


def user_list_serializer(user_data):
    """User profile list serializer."""
    def serializer(users, code=200, headers=None, links=None, total=None):
        if users is None:
            users = []

        response = jsonify({
            'hits': {
                'hits': [user_data(user) for user in users],
                'total': total,
            },
            'links': links
        })
        response.status_code = code

        if headers is not None:
            response.headers.extend(headers)
        return response
    return serializer


user_account_serializer = user_serializer(get_user_data)
user_account_list_serializer = user_list_serializer(get_user_data)
