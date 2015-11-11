# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez$ <kiko@comunitea.com>
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

from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _

class wave_report(models.Model):

    _inherit ='wave.report'

    @api.one
    @api.depends('operation_ids')
    def _get_revised_id(self):
        wave_to_revised_pool = self.env["wave.report.revised"]
        wave_to_revised = wave_to_revised_pool.search ([('wave_report_id', '=', self.id)])
        if wave_to_revised:
            res = wave_to_revised[0].id
        else:
            res = False
        self.wave_report_revised_id = res
        return res

    @api.one
    @api.depends('operation_ids')
    def _get_wrtrevised(self):

        res = False
        for op in self.operation_ids:
            if op.to_revised:
                res=True

        self.to_revised = res
        return res

    to_revised = fields.Boolean(string = 'To Revised', compute='_get_wrtrevised')
    wave_report_revised_id = fields.Many2one("wave.report.revised", string = 'Wave Report', compute='_get_revised_id')


    @api.multi
    def change_wave_op_values_packed_change(self, my_args):

        id = my_args.get('id', False)
        user_id = my_args.get('user_id', False)
        vals = my_args.get('values', False)
        wave_obj = self.browse(id)
        env2 = wave_obj.env(self._cr, user_id, self._context)
        wave = wave_obj.with_env(env2)
        res = True
        if wave:
            for op in wave.operation_ids:
                #op.write(vals)
                res = op.write(vals) and res
        return res


    @api.multi
    def change_wave_op_values(self, my_args):
        id = my_args.get('id', 0)
        user_id = my_args.get('user_id', False)
        wave_obj = self.browse(id)
        env2 = wave_obj.env(self._cr, user_id, self._context)
        wave = wave_obj.with_env(env2)
        res = True
        if wave:
            for op in wave.operation_ids:
                vals = {'to_process': True,
                        'visited': True}
                res = op.write(vals) and res
        return res



class wave_report_revised(models.Model):

    _name = 'wave.report.revised'
    _rec_name='wave_report_id'

    @api.one
    @api.depends('operation_ids')
    def _get_to_revised(self):

        to_revised= False
        for op in self.operation_ids:
            if op.to_revised:
                to_revised=True

        self.to_revised = to_revised
        return to_revised

    @api.multi
    def set_to_revised(self, value = False):
        ops = self.operation_ids
        if ops:
            ops.write({'to_revised': value})
        return value

    # @api.one
    # @api.depends('product_id')
    # def _get_operation_ids(self, cr, uid):
    #     import ipdb; ipdb.set_trace()
    #     res = {}
    #     waves = self
    #
    #     #waves.write = {'operation_ids': [(5)]}
    #     wave_id = waves.wave
    #     item_res = []
    #     for wave_report in wave_id.wave_report_ids:
    #         for op in wave_report.operation_ids:
    #             if op.product_id.id == wave_id.product_id.id:
    #                 #waves.write = {'operation_ids': [(4, op.id)]}
    #                 item_res.append(op.id)
    #         res['operation_ids'] = list(set(item_res))
    #     return res['operation_ids']


    to_revised = fields.Boolean(string = 'To Revised', compute='_get_to_revised')
    new_uos_qty = fields.Float('Qty effective (uos)', compute='refresh_qtys')
    new_uom_qty = fields.Float('Qty effective (uom)')
    pack_id = fields.Many2one(related = 'wave_report_id.pack_id')
    #product_id = fields.Many2one('product.product', 'Product')
    product_id = fields.Many2one(related = 'wave_report_id.product_id')
    lot_id = fields.Many2one(related = 'wave_report_id.lot_id')
    product_qty= fields.Float(related='wave_report_id.product_qty', readonly=True)
    uos_qty= fields.Float(related='wave_report_id.uos_qty', readonly=True)
    uom_id= fields.Many2one(related='wave_report_id.uom_id', readonly=True)
    uos_id= fields.Many2one(related='wave_report_id.uos_id', readonly=True)
    wave = fields.Many2one(related = 'wave_report_id.wave_id', readonly = True)
    wave_report_id = fields.Many2one('wave.report', 'Ref', readonly = True)
    #operation_ids = fields.One2many(related='wave_report_id.operation_ids')
    #operation_ids = fields.One2many (string="Operation", compute = '_get_operation_ids')
    operation_ids = fields.One2many ('stock.pack.operation', 'wave_revised_id', string = "Operation")
    stock = fields.Float(related = 'wave_report_id.product_id.qty_available')
    #wave_id = fields.Many2one('wave.report', 'Wave Report', readonly = True)



    # @api.one
    # def _get_operation_ids(self):
    #     wave_id = self.wave_report_id
    #     wave_repor = self.env['wave.report'].search([('id','=', wave_id)])
    #     res = []
    #     if wave_repor:
    #         res = wave_repor.operation_ids
    #     return res

    @api.multi
    def new_wave_to_revised(self, my_args):

        new_uos_qty = my_args.get('new_uos_qty', 0)
        new_uom_qty = my_args.get('new_uom_qty', 0)
        wave_report_id = my_args.get('id', False)
        task_id = my_args.get('task_id', False)
        vals ={}
        wave_report = self.env['wave.report'].browse(wave_report_id)
        product_id = wave_report.product_id
        wave_to_revised = self.env['wave.report.revised']
        vals = {
            'to_revised' : True,
            'new_uos_qty' : new_uos_qty,
            'new_uom_qty' : new_uom_qty,
            'wave_report_id': wave_report_id,
            'product_id': product_id.id
        }
        wave_ = wave_to_revised.search([('wave_report_id','=',wave_report_id)])
        if wave_:
            wave_.write(vals)
        else:
            wave_ = wave_to_revised.create(vals)
        product_id = wave_.product_id

        new_uos_qty=0
        new_uom_qty=0

        wave_report = self.env['wave.report'].browse(wave_report_id)
        wave_report.operation_ids.write({'to_process': True})
        picking_wave = self.env['stock.picking.wave'].browse(wave_report.wave_id.id)
        for wave_report in picking_wave.wave_report_ids:
            for op in wave_report.operation_ids:
                if op.product_id.id == product_id.id:
                    op.write({'to_revised' : True, 'wave_revised_id' : wave_.id})
                new_uos_qty += op.uos_qty
                new_uom_qty += op.product_qty
            wave_report.write({'wave_report_revised_id' : wave_.id})

        vals = {
            'new_uos_qty' : new_uos_qty,
            'new_uom_qty' : new_uom_qty,
        }
        wave_.write(vals)

        return wave_report_id

    @api.one
    @api.depends('operation_ids')
    def refresh_qtys(self):

        new_uom_qty =0
        new_uos_qty =0
        for op in self.operation_ids:
            new_uom_qty += op.product_qty
            new_uos_qty += op.uos_qty

        vals = {
            'new_uom_qty': new_uom_qty,
            'new_uos_qty': new_uos_qty
        }
        self.write(vals)




    @api.multi
    def set_wave_to_revised(self, ctx, to_revised = True):
        self.set_wave_revised(ctx, to_revised)

    @api.multi
    def set_wave_revised(self, ctx, to_revised = False):
        for wave in self:
            revised = to_revised
            values = ({'to_revised': revised})
            wave.operation_ids.write(values)
        self.refresh_qtys()

    @api.multi
    def finish_revised_task(self):
        wave_id = self.wave_report_id
        task = self.env['stock.task'].search([('wave_id', '=', wave_id.id)])

        if task:
            if task.state == "to_revised":
                task.finish_partial_task()
            else:
                 return {
                    'warning': {'title': _("Error"),
                                'message': _("This wave is not marked as to_revised")},
                    }







