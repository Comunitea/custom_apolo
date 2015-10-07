# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Informáticos All Rights Reserved
#    $Carlos Lombardía Rodríguez$ <carlos@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _
import time


class custom_picking_parser(models.AbstractModel):
    """
    """

    _name = 'report.custom_documents.report_custom_picking'

    @api.multi
    def render_html(self, data=None):
        # import ipdb; ipdb.set_trace()

        report_obj = self.env['report']
        report_name = 'custom_documents.report_custom_picking'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        for pick in self.env[report.model].browse(self._ids):
            docs.append(pick)

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
        }
        return report_obj.render(report_name, docargs)
