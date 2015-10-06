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
    @api.depends('wave_report_revised_id')
    def _get_wrtrevised(self):

        wave_to_revised_pool = self.env["wave.report.revised"]
        wave_to_revised = wave_to_revised_pool.search ([('wave_report_id', '=', self.id)])
        if wave_to_revised:
            res = wave_to_revised[0].to_revised
        else:
            res = False
        self.to_revised = res
        return res

    to_revised = fields.Boolean(string = 'To Revised', compute='_get_wrtrevised')
    wave_report_revised_id = fields.Many2one("wave.report.revised", string = 'Wave Report', compute='_get_revised_id')

    @api.multi
    def set_waves_op_processed(self, my_args):
        id = my_args.get('id', 0)
        user_id = my_args.get('user_id', False)
        wave_obj = self.browse(id)
        env2 = wave_obj.env(self._cr, user_id, self._context)
        wave = wave_obj.with_env(env2)
        if wave:
            for op in self.operation.ids:
                vals = {'to_process': True,
                        'visited': True}
                op.write(vals)

class wave_report_revised(models.Model):

    _name = 'wave.report.revised'
    _rec_name='wave_report_id'

    to_revised = fields.Boolean('To Revised')
    new_uos_qty = fields.Float('Qty effective (uos)')
    new_uom_qty = fields.Float('Qty effective (uom)')
    pack_id = fields.Many2one(related = 'wave_report_id.pack_id')
    product_id = fields.Many2one(related = 'wave_report_id.product_id')
    lot_id = fields.Many2one(related = 'wave_report_id.lot_id')
    product_qty= fields.Float(related='wave_report_id.product_qty', readonly=True)
    uos_qty= fields.Float(related='wave_report_id.uos_qty', readonly=True)
    uom_id= fields.Many2one(related='wave_report_id.uom_id', readonly=True)
    uos_id= fields.Many2one(related='wave_report_id.uos_id', readonly=True)

    wave_report_id = fields.Many2one('wave.report', 'Wave', readonly = True)
    operation_ids = fields.One2many (related='wave_report_id.operation_ids')
    #wave_id = fields.Many2one('wave.report', 'Wave Report', readonly = True)

    @api.one
    def _get_operation_ids(self):
        wave_id = self.wave_report_id
        wave_repor = self.env['wave.report'].search([('id','=', wave_id)])
        res = []
        if wave_repor:
            res = wave_repor.operation_ids
        return res

    @api.multi
    def new_wave_to_revised(self, my_args):

        new_uos_qty = my_args.get('new_uos_qty', 0)
        new_uom_qty = my_args.get('new_uom_qty', 0)
        wave_report_id = my_args.get('id', 0)
        vals ={}
        wave_to_revised = self.env['wave.report.revised']
        vals = {
            'to_revised' : True,
            'new_uos_qty' : new_uos_qty,
            'new_uom_qty' : new_uom_qty,
            'wave_report_id': wave_report_id
        }
        wave_ = wave_to_revised.search([('wave_repoort_id','=',wave_report_id)])
        if wave_:
            wave = wave_.write(vals)
        else:
            wave = wave_to_revised.create(vals)
        #actualizamos wave_report
        wave_report = self.env["wave.report"].search([('id', '=', wave_report_id)])
        wave_report.write({'to_revised' : True,'wave_report_revised_id' : wave.id})
        #ponemos en pausa la tarea correspondiente
        #wave_id = wave_report.wave_id.id
        #stock_task_pool = self.env["stock.task"].search([('wave_id', '=', wave_id)])
        #stock_task_pool.write ({'paused' : True})
        return wave_report_id