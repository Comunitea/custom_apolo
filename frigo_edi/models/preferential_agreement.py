# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _


class PreferentialAgreement(models.Model):

    _name = 'preferential.agreement'

    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    date = fields.Date('Agreement date', required=True)
    amount = fields.Float('Amount', required=True)
    joint_percentage = fields.Float('Joint percentage', required=True)
    init_date = fields.Date('Init date', required=True)
    end_date = fields.Date('End date', required=True)
    type = fields.Many2one('agreement.type', 'Type', required=True)
    note = fields.Text('Notes', size=100)
    state = fields.Selection((('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancelled')), 'state',
                             default='draft')
    rappel_group_id = fields.Many2one('product.rappel.group', 'Rappel group',
                                      required=True)
    rappel_subgroup_id = fields.Many2one('product.rappel.subgroup',
                                         'Rappel subgroup', required=True)
    cons_est = fields.Float('Estimated consumptions', required=True)

    @api.multi
    def confirm(self):
        """Se exporta el fichero COL con tipo A"""
        edi_obj = self.env["edi"]
        edis = edi_obj.search([])
        for service in edis:
            wzd = False
            for dtype in service.doc_type_ids:
                if dtype.code == "col":
                    wzd = self.env['edi.export.wizard'].create({'service_id':
                                                                service.id})
                    wzd.export_file_col('preferential.agreement', self, 'A')
                    break
        self.write({'state': 'confirmed'})

    @api.multi
    def cancel(self):
        """Se exporta el fichero COL con tipo B"""
        edi_obj = self.env["edi"]
        edis = edi_obj.search([])
        for service in edis:
            wzd = False
            for dtype in service.doc_type_ids:
                if dtype.code == "col":
                    wzd = self.env['edi.export.wizard'].create({'service_id':
                                                                service.id})
                    wzd.export_file_col('preferential.agreement', self, 'B')
                    break
        self.write({'state': 'cancel'})

    @api.multi
    def write(self, vals):
        """ Se exporta el fichero COL con las modificaciones(M)"""
        res = super(PreferentialAgreement, self).write(vals)
        if not (len(vals.keys()) == 1 and vals.get('state', False)):
            edi_obj = self.env["edi"]
            edis = edi_obj.search([])
            for service in edis:
                wzd = False
                for dtype in service.doc_type_ids:
                    if dtype.code == "col":
                        wzd = self.env['edi.export.wizard'].create(
                            {'service_id': service.id})
                        wzd.export_file_col('preferential.agreement', self,
                                            'M')
                        break
        return res


class AgreementType(models.Model):

    _name = 'agreement.type'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=1, required=True)
