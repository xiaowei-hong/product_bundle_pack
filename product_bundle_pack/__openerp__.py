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
{
    "name": "Product Bundle Pack",
    "category": 'Sales',
    "summary": """
       Combine two or more products together in order to create a bundle product.""",
    "description": """
	BrowseInfo developed a new odoo/OpenERP module apps.
	This module is use to create Product Bundle,Product Pack, Bundle Pack of Product, Combined Product pack.
    -Product Pack, Custom Combo Product, Bundle Product. Customized product, Group product.Custom product bundle. Custom Product Pack.
    -Pack Price, Bundle price, Bundle Discount, Bundle Offer.
	
    """,
    "sequence": 1,
    "author": "Browseinfo",
    "website": "http://www.browseinfo.in",
    "version": '1.0',
    "depends": ['sale','product','stock','sale_stock'],
    "data": [
        'views/product_view.xml',
        'security/ir.model.access.csv'
    ],
    "price": 19,
    "currency": 'EUR',
    "installable": True,
    "application": True,
    "auto_install": False,
    "images":['static/description/Banner.png'],

}
