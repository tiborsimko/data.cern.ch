# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2018 CERN.
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


"""CAP CDS service views."""

import requests
from flask import jsonify, abort, make_response

from . import blueprint
from ..serializers.cds import CDSRecordSchema
from cap.modules.access.utils import login_required
from cap.modules.experiments.errors import ExternalAPIException

from dojson.contrib.marc21.utils import create_record
import xml.dom.minidom as md

CDS_URL = 'https://cds.cern.ch/record/{}/export/xm?ln=en'


def check_if_deleted(resp):
    """Checks if a record is deleted, by using the appropriate MARC key."""
    try:
        # if the 980$c exists, the record is ALWAYS DELETED
        types = resp['980__']

        if isinstance(types, tuple):
            if any('c' in _dict for _dict in types) and len(types) == 1:
                abort(400, 'The record was deleted from CDS.')
        else:
            if types['c']:
                abort(400, 'The record was deleted from CDS.')
    except KeyError:
        pass


def check_if_authorized(resp):
    """Checks the CDS authorization."""
    if resp.headers.get('Expires'):
        abort(
            make_response(
                jsonify({'message': 'You are unauthorized to view this CDS record.'}),
                401,
            )
        )


def check_if_404(resp):
    """Checks and abort in case of missing page."""
    if resp.status_code == 404:
        abort(404, 'CDS record does not exist.')


def _cds(record_id):
    """Get Indico event by id."""
    url = CDS_URL.format(record_id)
    resp = requests.get(url)

    check_if_authorized(resp)
    check_if_404(resp)

    dom = md.parseString(resp.text.encode('utf-8'))
    rec = dom.getElementsByTagName('record')[0]
    rec_json = create_record(rec.toxml())

    return rec_json, resp.status_code


@blueprint.route('/cds/<record_id>')
@login_required
def get_cds_record(record_id):
    """Get Indico event by id and serialize the response."""
    try:
        resp, status = _cds(record_id)
        check_if_deleted(resp)

        serialized = CDSRecordSchema().dump(resp).data
        return jsonify(serialized), status
    except IndexError:
        return abort(400, "Error on CDS serialization. "
                          "Make sure that the record exists.")
    except ExternalAPIException:
        raise abort(503, 'Error on the response of CDS API.')
