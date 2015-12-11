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
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round

class wave_report(models.Model):

    _inherit ='wave.report'

    @api.one
    #@api.depends('operation_ids')
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
    #@api.depends('operation_ids')
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
        #se usa cuando ca,biamos el paquete de una operación dentro de un wave_report
        id = my_args.get('id', False)
        user_id = my_args.get('user_id', False)
        vals = my_args.get('values', False)
        wave_obj = self.browse(id)
        ctx = {'no_recompute': True}
        env2 = wave_obj.env(self._cr, user_id, ctx)
        wave = wave_obj.with_env(env2)
        res = False
        product_id = vals.get('product_id', False)
        if vals:
            package_id = vals['package_id']
            op_package_id = vals['op_package_id']
        product = self.env['product.product'].browse(product_id)
        new_package_id = self.env['stock.quant.package'].browse(package_id)
        domain = [('package_id', '=', package_id), ('reservation_id.id', '=', False)]
        quant_ids = self.env['stock.quant'].search(domain)
        new_quant_objs = quant_ids
        old_package_id = self.env['stock.quant.package'].browse(op_package_id)
        old_quant_ids = [x.id for x in old_package_id.quant_ids]
        #domain =
        #1º ir desde op al movimiento
        #linked_move_operation_ids

        #2ª
        force_quants =[]
        qty_to_reassign = 0.0
        #quants_reserved = self.env['stock.quant'].search()
        if wave:
            for op in wave.operation_ids:
                if op.package_id.id != old_package_id.id:
                    continue

                moves2recalc = list(set([x.move_id for x in op.linked_move_operation_ids]))
                for move in moves2recalc:
                    force_quants =[]
                    for quant_id in move.reserved_quant_ids:

                        quant = self.env['stock.quant'].sudo().browse(quant_id.id)#quant.sudo(user_id=1)
                        if quant.id in old_quant_ids:
                            quant.reservation_id = False
                            qty_to_reassign += quant.qty
                        else:
                            if quant.qty>0:
                                force_quants.append((quant, quant.qty))

                    for quant in new_quant_objs:
                        if qty_to_reassign >= quant.qty:
                            force_quants.append((quant, quant.qty))
                            qty_to_reassign -= quant.qty
                        else:
                            if qty_to_reassign>0:
                                force_quants.append((quant, qty_to_reassign))
                            break
                    #Anulamos la reserva
                    move.do_unreserve()

                    ctx = self._context.copy()
                    ctx.update({'force_quants_location': force_quants})
                    move = self.env['stock.move'].with_context(ctx).browse(move.id)
                    move.action_assign()

                #trato todos las operaciones como productos:
                #escribo producto y product_qty en todas las ops de esta ola
                #si el paquete queda vacío mala suerte...
                if op.product_id:
                    qty = op.product_qty
                else:
                    qty = op.packed_qty
                    vals['product_qty'] = qty
                    vals['uos_qty'] = product.uom_qty_to_uos_qty(qty, op.uos_id.id)
                #op.write(vals)
                #no sobreescribe la uos_id
                #entonces:

                res = op.write(vals)

        return res or False

    @api.multi
    def change_wave_op_values(self, my_args):
        id = my_args.get('id', 0)
        user_id = my_args.get('user_id', False)
        values = my_args.get('values', {})
        wave_obj = self.browse(id)
        ctx = {'no_recompute': True}
        env2 = wave_obj.env(self._cr, user_id, ctx)
        #env2 = wave_obj.env(self._cr, user_id, self._context)
        wave = wave_obj.with_env(env2)
        res = False
        if wave:
            for op in wave.operation_ids:
                op.write (values)
                #Calculate the operations for the next chained picking
                related_pick = op.picking_id.move_lines and\
                               op.picking_id.move_lines[0].move_dest_id and\
                               op.picking_id.move_lines[0].move_dest_id.picking_id
                if related_pick:
                    #### CMNT REVISAR QUITAR  DE AQUI PARA AGILIZAR PISTOLA
                    related_pick.do_prepare_partial()
                    related_pick.write({'midban_operations': True})


            #res = wave.operation_ids.write(values)
        return res

    @api.multi
    def get_wave_report_values(self):
        #sacamos los valores necesarios ddel wave_report para la lpistola
        values = {}
        if not self:
            return values
        self.ensure_one()
        wh = self.env['stock.warehouse'].search([])[0]
        lot_id = self.lot_id
        product_id = self.product_id
        if self.is_package:
            qty = self.pack_id.packed_qty
        packed_qty = float_round(self.pack_id.packed_qty, precision_rounding = self.pack_id.uom_id.rounding)
        uos_id = self.uos_id or self.uom_id
        values = {
            'id': self.id,
            'wave_report_id':self.id,
            'wave_id': self.wave_id.id,
            'name':self.wave_id.name or '',
            'product_id': product_id.id or False,
            'product': product_id.short_name or '',
            'default_code': self.product_id.default_code or '',
            'qty': float_round(self.product_qty, precision_rounding = self.uom_id.rounding) or 0.00,
            'is_package': self.is_package,
            'package': self.pack_id.id and self.pack_id.name or "",
            'package_id': self.pack_id.id or 0,
            'packed_qty': packed_qty or 0,
            'lot_id': self.lot_id.id or False,
            'lot': self.lot_id.name or '',
            'origen_id': self.location_id.id or 0,
            'origen_bcd' : self.location_id.bcd_name or self.location_id.name or '',
            'result_package_id' : False,
            'result_package' : '',
            'destino_id': wh.wh_output_stock_loc_id.id or False,
            'destino_bcd' : wh.wh_output_stock_loc_id.name or '',
            'to_process': self.to_process,
            'uom': self.uom_id.name or False,
            'uom_id': self.uom_id.id or False,
            'uom_qty' : float_round(self.product_qty, precision_rounding = self.uom_id.rounding) or 0.00,
            'uos_qty': float_round(self.uos_qty, precision_rounding = uos_id.rounding) or 0.00,
            'uos' :uos_id.name,
            'uos_id':uos_id.id,
            'to_revised':self.to_revised,
            'is_var_coeff': self.product_id.is_var_coeff or False,
            'var_coeff_ca':self.product_id.var_coeff_ca or False,
            'var_coeff_un':self.product_id.var_coeff_un or False,
            'num_ops':len(self.operation_ids),
            'customer': self.customer_id.ref or '',
            'customer_id': self.customer_id.comercial or self.customer_id.name,
            'qty_available': packed_qty or 0.00
        }
        product = self.product_id
        values ['units'] = {}
        if product:
            if product.is_var_coeff:
                qty = self.uos_qty
            else:
                qty = self.product_qty
            values['units'] = product.get_uom_conversions(qty, uom_id = self.uos_id.id)
        # uom_destino = product.log_box_id.id or product.log_unit_id.id or product.log_base_id.id
        # uom_origen = op.uos_id.id or op.uom_id.id
        # values['big_unit'] = product._get_unit_ratios(uom_destino, False) / \
        #     product._get_unit_ratios(uom_origen, False)

        return values

class wave_report_revised(models.Model):

    _name = 'wave.report.revised'
    _rec_name='wave_report_id'


    @api.depends('operation_ids')
    @api.one
    def _get_to_revised(self):
        to_revised= False
        for op in self.operation_ids:
            if op.to_revised:
                to_revised=True
        self.to_revised = to_revised

    @api.depends('operation_ids')
    @api.one
    def _get_assigned_qtys(self):
        res = 0.0
        for l in self.operation_ids:
            res += l.product_qty
        self.picked_qty = res


    @api.multi
    def set_to_revised(self, value = False):
        ops = self.operation_ids
        if ops:
            ops.write({'to_revised': value})
        return value

    # @api.one
    # @api.depends('product_id')
    # def _get_operation_ids(self, cr, uid):
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



    to_revised = fields.Boolean(string = 'To Revised', compute=_get_to_revised)
    new_uos_qty = fields.Float('Picked Qty (uos)',compute=_get_assigned_qtys,
                               digits_compute=
                               dp.get_precision('Product Unit of Measure'))
    new_uom_qty = fields.Float('Picked Qty (uom)',
                               digits_compute=
                               dp.get_precision('Product Unit of Measure'))
    pack_id = fields.Many2one(related = 'wave_report_id.pack_id', string ='Pack')
    packed_qty = fields.Float(related = 'wave_report_id.pack_id.unreserved_qty', string = 'Unreserved Qty in pack')
    #product_id = fields.Many2one('product.product', 'Product')
    product_id = fields.Many2one(related = 'wave_report_id.product_id')
    lot_id = fields.Many2one(related = 'wave_report_id.lot_id')
    product_qty= fields.Float(related='wave_report_id.product_qty', readonly=True)
    uos_qty= fields.Float(related='wave_report_id.uos_qty', readonly=True, string = 'Qty (uos)')
    uom_qty= fields.Float(readonly=True, string = 'Qty (uom)')
    uom_id= fields.Many2one(related='wave_report_id.uom_id', readonly=True, string = 'Stock Unit')
    uos_id= fields.Many2one(related='wave_report_id.uos_id', readonly=True, string = "UoS")
    wave = fields.Many2one(related = 'wave_report_id.wave_id', readonly = True, string = 'Wave')
    wave_report_id = fields.Many2one('wave.report', 'Ref', readonly = True)
    operation_ids = fields.One2many ('stock.pack.operation', 'wave_revised_id', string = "Operation")
    stock = fields.Float(related = 'wave_report_id.product_id.qty_available', string = "Stock QTY")
    picked_qty = fields.Float('Picked Qty', readonly = True)
    #state = fields.Selection(related = 'wave_report_id.wave_id.state', string ="Wave Asociated State", readonly = True)
    task_id = fields.Many2one('stock.task', readonly = True)
    state = fields.Selection (related = 'task_id.state')

    @api.multi
    def new_wave_to_revised(self, my_args):
        new_uos_qty = my_args.get('new_uos_qty', 0)
        new_uom_qty = my_args.get('new_uom_qty', 0)
        # qty = my_args.get('qty', 0)
        uom_qty = my_args.get('uom_qty', 0)
        wave_report_id = my_args.get('wave_id', False)
        task_id = my_args.get('task_id', False)
        wave_report = self.env['wave.report'].browse(wave_report_id)
        product_id = wave_report.product_id
        wave_to_revised = self.env['wave.report.revised']
        wave_report = self.env['wave.report'].browse(wave_report_id)
        vals = {
            'wave_report_id': wave_report_id,
            'to_revised' : True,
            'new_uos_qty' : new_uos_qty,
            'new_uom_qty' : new_uom_qty,
            'wave_report_id': wave_report_id,
            'product_id': product_id.id,
            'picked_qty': new_uom_qty,
            'pack_id': wave_report.pack_id.id,
            'uom_qty': uom_qty,
            'task_id' : task_id
        }
        wave_ = wave_to_revised.search([('wave_report_id','=',wave_report_id)])
        if wave_:
            wave_.write(vals)
        else:
            wave_ = wave_to_revised.create(vals)

        wave_report.operation_ids.write({'to_process': True, 'to_revised' : True, 'wave_revised_id' : wave_.id})
        wave_report.write({'wave_report_revised_id' : wave_.id})

        #Marcamos como procesados, a revisar y le damos un wave_id las operaciones del wave_report
        # picking_wave = self.env['stock.picking.wave'].browse(wave_report.wave_id.id)
        # for wave_report in picking_wave.wave_report_ids:
        #     if wave_report.product_id.id == product_id.id:
        #         wave_report.operation_ids.write({'to_revised' : True, 'wave_revised_id' : wave_.id})
        #         wave_report.write({'wave_report_revised_id' : wave_.id})
        #wave_.refresh_qtys()
        return wave_to_revised.id

    @api.one
    def refresh_qtys(self):
        picked_qty = 0
        new_uom_qty = 0
        for op in self.operation_ids:
            op_qty= 0.0
            if op.product_id:
                op_qty = op.product_qty
            else:
                op_qty = op.package_id.packed_qty
            #NO VALIDO
            if op.to_process:
                picked_qty +=  op_qty

            new_uom_qty += op_qty

        vals = {
            'new_uos_qty' : 0.0,
            'new_uom_qty' : new_uom_qty,
            'picked_qty': picked_qty
        }
        self.write(vals)

    @api.multi
    def set_wave_to_revised(self, ctx, to_revised = True):
        self.set_wave_revised(ctx, to_revised)

    @api.multi
    def set_wave_revised(self, ctx, to_revised = False):
        if self.picked_qty > self.uom_qty:
            raise except_orm(_('Error'),
                             _('Picked Qty > UoS Qty'))
        for wave in self:
            revised = to_revised
            values = ({'to_revised': revised})
            wave.operation_ids.write(values)
        #self.refresh_qtys()

    @api.multi
    def finish_revised_task(self):


        wave_report = self.wave_report_id
        task = self.env['stock.task'].search([('wave_id', '=', wave_report.wave_id.id)])

        if task:
            if task.state == "to_revised" or task.state == "assigned":
                task.finish_partial_task()
            else:
                 return {
                    'warning': {'title': _("Error"),
                                'message': _("This wave is not marked as to_revised")},
                    }
