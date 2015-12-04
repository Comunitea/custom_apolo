# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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
from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class WizardOrderLocations(models.TransientModel):

    _name = 'wizard.order.locations'

    camera_order_ids = fields.One2many('stock.camera.order', 'wzd_order_id',
                                       "Cameras Order")

    @api.model
    def default_get(self, fields):
        res = super(WizardOrderLocations, self).default_get(fields)
        t_sl = self.env['stock.location']
        camera_codes = t_sl.read_group([], ['xy_camera'], groupby='xy_camera')
        if not camera_codes:
            raise except_orm(_('Error'),
                             _('Not locations codes founded'))
        # import ipdb; ipdb.set_trace()

        list_camera_vals = []
        for d in camera_codes:
            seq_cam = 0
            list_aisle_vals = []
            cam_code = d['xy_camera']
            if cam_code:
                domain = d['__domain']
                aisle_codes = t_sl.read_group(domain, ['xy_aisle'],
                                              groupby='xy_aisle')
                for d2 in aisle_codes:
                    seq_aisle = 0
                    aisle_code = d2['xy_aisle']
                    if aisle_code:
                        loc = t_sl.search([('xy_camera', '=', cam_code),
                                           ('xy_aisle', '=', aisle_code)],
                                          limit=1)
                        if loc:
                            seq_cam = loc.posc
                            seq_aisle = loc.posx
                        vals = {
                            'xy_aisle': aisle_code,
                            'orientation': loc.orientation,
                            'sequence': seq_aisle
                        }
                        list_aisle_vals.append((0, 0, vals))
                # Creating order cameras model
                list_aisle_vals.sort(key=lambda x: x[2]['sequence'])
                vals = {
                    'xy_camera': cam_code,
                    'aisle_order_ids': list_aisle_vals,
                    'sequence': seq_cam,

                }
                list_camera_vals.append((0, 0, vals))
        list_camera_vals.sort(key=lambda x: x[2]['sequence'])
        res.update({'camera_order_ids': list_camera_vals})
        return res

    @api.multi
    def set_defined_order(self):
        print u"Entro al set_defined_order"
        t_sl = self.env['stock.location']
        for cam in self.camera_order_ids:
            posc = cam.sequence
            my_sequence = ""
            for aisle in cam.aisle_order_ids:
                posx = aisle.sequence
                my_sequence = str(posc).zfill(3) + str(posx).zfill(3)
                domain = [('xy_camera', '=', cam.xy_camera),
                          ('xy_aisle', '=', aisle.xy_aisle)]
                domain_pick = domain + [('zone', '=', 'picking')]
                domain_sto = domain + [('zone', '=', 'storage')]
                order = 'xy_column asc, xy_height asc'
                if aisle.orientation == 'neg':
                    order = 'xy_column desc, xy_height asc'
                locs_picks = t_sl.search(domain_pick, order=order)
                locs_sto = t_sl.search(domain_sto, order=order)
                posy = 0
                posz = 0
                xy_column = ""
                for l in locs_picks + locs_sto:
                    if xy_column != l.xy_column:
                        xy_column = l.xy_column
                        posy += 1
                        posz = 0
                    posz += 1

                    my_sequence = str(posc).zfill(3) + str(posx).zfill(3) + \
                        str(posy).zfill(3) + str(posz).zfill(3)
                    vals = {
                        'posc': posc,
                        'posx': posx,
                        'posy': posy,
                        'posz': posz,
                        'order_seq': my_sequence,
                        'orientation': aisle.orientation
                    }
                    l.write(vals)


class StockCameraOrder(models.TransientModel):

    _name = "stock.camera.order"
    _description = "Sets order of Cameras"
    _rec_name = 'xy_camera'

    wzd_order_id = fields.Many2one('wizard.order.locations', 'Wzd Order')
    xy_camera = fields.Char("Camera code", readonly=True)
    aisle_order_ids = fields.One2many('stock.aisle.order', 'ord_cam_id',
                                      "Aisle Order")
    sequence = fields.Integer("Order")


class StockAisleOrder(models.TransientModel):

    _name = "stock.aisle.order"
    _description = "Sets order of Cameras"
    _rec_name = 'xy_aisle'

    ord_cam_id = fields.Many2one('stock.camera.order', 'Order Camera')
    xy_aisle = fields.Char("Aisle code", readonly=True)
    orientation = fields.Selection([('pos', 'Positive'), ('neg', 'Negative')],
                                   'Orentation', default='pos')
    sequence = fields.Integer("Order")
