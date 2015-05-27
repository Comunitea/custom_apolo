# -*- coding: utf-8 -*-
##############################################################################
#
#    Omar Castiñeira Saavedra Copyright Comunitea SL 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, fields, api


class EdiDoc(models.Model):

    _inherit = "edi.doc"

    count = fields.Integer("Seq. count", readonly=True)


class Edi(models.Model):

    _inherit = "edi"

    related_partner_id = fields.Many2one("res.partner", "Related partner",
                                         domain=[('is_company', '=', True)])


    @api.model
    def _get_file_type(self, filename):
        ftype = super(Edi, self)._get_file_type(filename)
        if not ftype:
            doc_type_obj = self.env['edi.doc.type']
            if 'PRO' in filename:
                ftype = doc_type_obj.search([('code', '=', 'pro')])[0]
            elif 'ABO' in filename:
                ftype = doc_type_obj.search([('code', '=', 'abo')])[0]
            elif 'TUR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'tur')])[0]
            elif 'ALC' in filename:
                ftype = doc_type_obj.search([('code', '=', 'alc')])[0]
            elif 'CLP' in filename:
                ftype = doc_type_obj.search([('code', '=', 'clp')])[0]
            elif 'LPR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'lpr')])[0]
            elif 'TOR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'tor')])[0]
        return ftype

    @api.model
    def _get_file_name(self, filename, type):
        if type.code in ('PRO', 'ABO', 'TUR', 'ALC', 'CLP', 'LPR', 'TOR'):
            return filename
        else:
            return super(Edi, self)._get_file_name(filename, type)
