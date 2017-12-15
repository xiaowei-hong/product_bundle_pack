# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from openerp import api, models, _
from datetime import datetime, timedelta
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_check_availability(self):
        res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
        if self.product_id.is_pack:
            if self.product_id.type == 'product':
                warning_mess = {}
                for pack_product in self.product_id.pack_ids:
                    qty = self.product_uom_qty
                    if qty * pack_product.qty_uom > pack_product.product_id.virtual_available:
                        warning_mess = {
                                'title': _('Not enough inventory!'),
                                'message' : ('You plan to sell %s but you only have %s %s available, and the total quantity to sell is %s !' % (qty, pack_product.product_id.virtual_available, pack_product.product_id.name, qty * pack_product.qty_uom))
                                }
                        return {'warning': warning_mess}
        else:
            return res
    
    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        self.ensure_one()
        res = []
        if  self.product_id.pack_ids:
            for item in self.product_id.pack_ids:
                res.append({
                    'name': item.product_id.name,
                    'origin': self.order_id.name,
                    'date_planned': datetime.strptime(self.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=self.customer_lead),
                    'product_id': item.product_id.id,
                    'product_qty': item.qty_uom,
                    'product_uom': item.uom_id and item.uom_id.id,
                    'company_id': self.order_id.company_id.id,
                    'group_id': group_id,
                    'sale_line_id': self.id,
                    'warehouse_id' : self.order_id.warehouse_id and self.order_id.warehouse_id.id,
                    'location_id': self.order_id.partner_shipping_id.property_stock_customer.id,
                    'route_ids': self.route_id and [(4, self.route_id.id)] or [],
                    'partner_dest_id': self.order_id.partner_shipping_id.id,
                })
        else:
            res.append({
                'name': self.name,
                'origin': self.order_id.name,
                'date_planned': datetime.strptime(self.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=self.customer_lead),
                'product_id': self.product_id.id,
                'product_qty': self.product_uom_qty,
                'product_uom': self.product_uom.id,
                'company_id': self.order_id.company_id.id,
                'group_id': group_id,
                'sale_line_id': self.id,
                'warehouse_id' : self.order_id.warehouse_id and self.order_id.warehouse_id.id,
                'location_id': self.order_id.partner_shipping_id.property_stock_customer.id,
                'route_ids': self.route_id and [(4, self.route_id.id)] or [],
                'partner_dest_id': self.order_id.partner_shipping_id.id,
                
                })
        return res
            

    @api.multi
    def _action_procurement_create(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order']
        orders = list(set(x.order_id for x in self))
        for line in self:
            
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                return False
            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)
            vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
            for val in vals:
		if line.product_id.is_pack:
                    val['product_qty'] = line.product_uom_qty * val['product_qty']
                else:
                    val['product_qty'] = line.product_uom_qty
                new_proc = self.env["procurement.order"].create(val)
                new_procs += new_proc
            for order in orders:
                reassign = order.picking_ids.filtered(lambda x: x.state == 'confirmed' or ((x.state == 'partially_available') and not x.printed))
                if reassign:
                    reassign.do_unreserve()
                    reassign.action_assign()
        new_procs.run()
        return new_procs

    
class stock_quant(models.Model):
    _inherit = 'stock.quant'
    
    @api.model
    def quants_reserve(self, quants, move, link=False):
        ''' This function reserves quants for the given move and optionally
        given link. If the total of quantity reserved is enough, the move state
        is also set to 'assigned'

        :param quants: list of tuple(quant browse record or None, qty to reserve). If None is given as first tuple element, the item will be ignored. Negative quants should not be received as argument
        :param move: browse record
        :param link: browse record (stock.move.operation.link)
        '''
        # TDE CLEANME: use ids + quantities dict
        # TDE CLEANME: check use of sudo
        quants_to_reserve_sudo = self.env['stock.quant'].sudo()
        reserved_availability = move.reserved_availability
        # split quants if needed
        for quant, qty in quants:
            if qty <= 0.0 or (quant and quant.qty <= 0.0):
                raise UserError(_('You can not reserve a negative quantity or a negative quant.'))
            if not quant:
                continue
            quant._quant_split(qty)
            quants_to_reserve_sudo |= quant
            reserved_availability += quant.qty
        # reserve quants
        if quants_to_reserve_sudo:
            quants_to_reserve_sudo.write({'reservation_id': move.id})
        # check if move state needs to be set as 'assigned'
        # TDE CLEANME: should be moved as a move model method IMO
        rounding = move.product_id.uom_id.rounding
        if move.product_id.is_pack:
            quantity = []
            for pack_obj in move.product_id.product_tmpl_id.pack_ids:
                product_obj = self.env['product.product']
                product_search = product_obj.search([('id' , '=', pack_obj.product_id.id)])
                if product_search:
                    product_qty = product_obj.browse(product_search[0]).qty_available
                    if product_qty <= 0.0:
                        quantity.append(product_qty)
            if quantity:
                self.pool.get('stock.move').write([move.id], {'state': 'confirmed'})
            else:
                self.pool.get('stock.move').write([move.id], {'state': 'assigned'})
        if float_compare(reserved_availability, move.product_qty, precision_rounding=rounding) == 0 and move.state in ('confirmed', 'waiting'):
            move.write({'state': 'assigned'})
        elif float_compare(reserved_availability, 0, precision_rounding=rounding) > 0 and not move.partially_available:
            move.write({'partially_available': True})
