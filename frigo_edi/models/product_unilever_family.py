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


class ProductUnileverFamily(models.Model):

    _name = "product.unilever.family"

    name = fields.Char("Name", size=30, required=True)
    code = fields.Char("Code", size=6, required=True)


class ProductRappelGroup(models.Model):

    _name = 'product.rappel.group'

    name = fields.Char("Name", size=30, required=True)
    code = fields.Char("Code", size=2, required=True)
    subgroup_ids = fields.One2many('product.rappel.subgroup', 'group_id',
                                   'Subgroups')


class ProductRappelSubgroup(models.Model):

    _name = 'product.rappel.subgroup'

    name = fields.Char('name', required=True)
    code = fields.Char('Code', size=2, required=True)
    group_id = fields.Many2one('product.rappel.group', 'Group')
    estimation_ids = fields.One2many('product.rappel.subgroup.estimation', 'subgroup_id', 'Estimations')


class ProductRappelSubgroupEstimation(models.Model):

    _name = 'product.rappel.subgroup.estimation'

    subgroup_id = fields.Many2one('product.rappel.subgroup', 'Subgroup')
    partner_id = fields.Many2one('res.partner', 'Customer')
    estimation = fields.Float('Estimations')

class ProductTemplate(models.Model):

    _inherit = "product.template"

    unilever_family_id = fields.Many2one("product.unilever.family",
                                         "Unilever family")
    rappel_group_id = fields.Many2one('product.rappel.group', 'Rappel group')
    rappel_subgroup_id = fields.Many2one('product.rappel.subgroup',
                                         'Rappel subgroup')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def get_supplier_product_code(self, supplier_id):
        self.ensure_one()

        suppinfo = self.env['product.supplierinfo'].search(
            [('product_tmpl_id', '=', self.product_tmpl_id.id),
             ('name', '=', supplier_id)])

        if suppinfo.product_code:
            res_code = suppinfo.product_code or ''
        else:
            res_code = self.default_code or ''
        return res_code
