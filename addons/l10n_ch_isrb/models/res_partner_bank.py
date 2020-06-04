# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class ResPartnerBank(models.Model):
    """Inherit res.partner.bank class in order to add:

    - ISR-B customer ID field

    """

    _inherit = "res.partner.bank"

    l10n_ch_isrb_id_number = fields.Char(string='ISR-B Custmer ID', help='ISR-B Customer ID number for ISR. Used only when generating ISR reference through a bank. This will prefix your references. It is not necessary for standard ISR from Postfinance. e.g. 999999')
