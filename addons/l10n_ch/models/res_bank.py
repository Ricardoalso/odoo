# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.tools.misc import mod10r
from odoo.exceptions import ValidationError

import werkzeug.urls

CH_POSTFINANCE_CLEARING = "09000"


def validate_l10n_ch_postal(postal_acc_number):
    """Check if the string postal_acc_number is a valid postal account number,
    i.e. it only contains ciphers and is last cipher is the result of a recursive
    modulo 10 operation ran over the rest of it. Shorten form with - is also accepted.
    Raise a ValidationError if check fails
    """
    if not postal_acc_number:
        raise ValidationError(_("There is no postal account number."))
    if re.match('^[0-9]{2}-[0-9]{1,6}-[0-9]$', postal_acc_number or ''):
        ref_subparts = postal_acc_number.split('-')
        postal_acc_number = ref_subparts[0] + ref_subparts[1].rjust(6,'0') + ref_subparts[2]

    if not re.match('\d{9}$', postal_acc_number or ''):
        raise ValidationError(_("The postal does not match 9 digits position."))

    acc_number_without_check = postal_acc_number[:-1]
    if not mod10r(acc_number_without_check) == postal_acc_number:
        raise ValidationError(_("The postal account number is not valid."))

def pretty_l10n_ch_postal(number):
    """format a postal account number or an ISR subscription number
    as per specifications with '-' separators.
    eg. 010000628 -> 01-162-8
    """
    if re.match('^[0-9]{2}-[0-9]{1,6}-[0-9]$', number or ''):
        return number
    currency_code = number[:2]
    middle_part = number[2:-1]
    trailing_cipher = number[-1]
    middle_part = re.sub('^0*', '', middle_part)
    return currency_code + '-' + middle_part + '-' + trailing_cipher

def _is_l10n_ch_postfinance_iban(iban):
    """Postfinance IBAN have format
    CHXX 0900 0XXX XXXX XXXX K
    Where 09000 is the clearing number
    """
    return (iban.startswith('CH')
            and iban[4:9] == CH_POSTFINANCE_CLEARING)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_ch_postal = fields.Char(string='Swiss Postal Account', help='This field is used for the Swiss postal account number '
                                                                     'on a vendor account and for the client number on your '
                                                                     'own account.  The client number is mostly 6 numbers without '
                                                                     '-, while the postal account number can be e.g. 01-162-8')
    # fields to configure ISR payment slip generation
    l10n_ch_isr_subscription_chf = fields.Char(string='CHF ISR Subscription Number', help='The subscription number provided by the bank or Postfinance to identify the bank, used to generate ISR in CHF. eg. 01-162-8')
    l10n_ch_isr_subscription_eur = fields.Char(string='EUR ISR Subscription Number', help='The subscription number provided by the bank or Postfinance to identify the bank, used to generate ISR in EUR. eg. 03-162-5')
    l10n_ch_show_subscription = fields.Boolean(compute='_compute_l10n_ch_show_subscription', default=lambda self: self.env.company.country_id.code == 'CH')

    @api.depends('partner_id', 'company_id')
    def _compute_l10n_ch_show_subscription(self):
        for bank in self:
            if bank.partner_id:
                bank.l10n_ch_show_subscription = bool(bank.partner_id.ref_company_ids)
            elif bank.company_id:
                bank.l10n_ch_show_subscription = bank.company_id.country_id.code == 'CH'
            else:
                bank.l10n_ch_show_subscription = self.env.company.country_id.code == 'CH'

    @api.depends('acc_number', 'acc_type')
    def _compute_sanitized_acc_number(self):
        #Only remove spaces in case it is not postal
        postal_banks = self.filtered(lambda b: b.acc_type == "postal")
        for bank in postal_banks:
            bank.sanitized_acc_number = bank.acc_number
        super(ResPartnerBank, self - postal_banks)._compute_sanitized_acc_number()

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(('postal', _('Postal')))
        return rslt

    @api.model
    def retrieve_acc_type(self, acc_number):
        """ Overridden method enabling the recognition of swiss postal bank
        account numbers.
        """
        acc_number_split = ""
        # acc_number_split is needed to continue to recognize the account
        # as a postal account even if the difference
        if acc_number and " " in acc_number:
            acc_number_split = acc_number.split(" ")[0]
        if _is_l10n_ch_postal(acc_number) or (acc_number_split and _is_l10n_ch_postal(acc_number_split)):
            return 'postal'
        try:
            validate_l10n_ch_postal(acc_number)
        except ValidationError:
            return super(ResPartnerBank, self).retrieve_acc_type(acc_number)

    @api.onchange('acc_number', 'partner_id', 'acc_type')
    def _onchange_set_l10n_ch_postal(self):
        if self.acc_type == 'iban':
            self.l10n_ch_postal = self._retrieve_l10n_ch_postal(self.sanitized_acc_number)
        elif self.acc_type == 'postal':
            if self.acc_number and " " in self.acc_number:
                self.l10n_ch_postal = self.acc_number.split(" ")[0]
            else:
                self.l10n_ch_postal = self.acc_number
                if self.partner_id:
                    self.acc_number = self.acc_number + '  ' + self.partner_id.name

    @api.model
    def _retrieve_l10n_ch_postal(self, iban):
        """Reads a swiss postal account number from a an IBAN and returns it as
        a string. Returns None if no valid postal account number was found, or
        the given iban was not from Swiss Postfinance.

        CH09 0900 0000 1000 8060 7 -> 10-8060-7
        """
        # We can deduce postal account number only if
        # the financial institution is PostFinance
        if _is_l10n_ch_postfinance_iban(iban):
            #the IBAN corresponds to a swiss account
            try:
                validate_l10n_ch_postal(iban[-9:])
                return pretty_l10n_ch_postal(iban[-9:])
            except ValidationError:
                pass
        return None

    @api.model
    def create(self, vals):
        if vals.get('l10n_ch_postal'):
            try:
                validate_l10n_ch_postal(vals['l10n_ch_postal'])
                vals['l10n_ch_postal'] = pretty_l10n_ch_postal(vals['l10n_ch_postal'])
            except ValidationError:
                pass
        return super(ResPartnerBank, self).create(vals)

    def write(self, vals):
        if vals.get('l10n_ch_postal'):
            try:
                validate_l10n_ch_postal(vals['l10n_ch_postal'])
                vals['l10n_ch_postal'] = pretty_l10n_ch_postal(vals['l10n_ch_postal'])
            except ValidationError:
                pass
        return super(ResPartnerBank, self).write(vals)

    def find_number(self, s):
        # this regex match numbers like 1bis 1a
        lmo = re.findall('([0-9]+[^ ]*)',s)
        # no number found
        if len(lmo) == 0:
            return ''
        # Only one number or starts with a number return the first one
        if len(lmo) == 1 or re.match(r'^\s*([0-9]+[^ ]*)',s):
            return lmo[0]
        # else return the last one
        if len(lmo) > 1:
            return lmo[-1]
        else:
            return ''

    @api.model
    def build_swiss_code_url(self, amount, currency_name, not_used_anymore_1, debtor_partner, not_used_anymore_2, structured_communication, free_communication):
        comment = ""
        if free_communication:
            comment = (free_communication[:137] + '...') if len(free_communication) > 140 else free_communication

        creditor_addr_1, creditor_addr_2 = self._get_partner_address_lines(self.partner_id)
        debtor_addr_1, debtor_addr_2 = self._get_partner_address_lines(debtor_partner)

        # Compute reference type (empty by default, only mandatory for QR-IBAN,
        # and must then be 27 characters-long, with mod10r check digit as the 27th one,
        # just like ISR number for invoices)
        reference_type = 'NON'
        reference = ''
        if self._is_qr_iban():
            # _check_for_qr_code_errors ensures we can't have a QR-IBAN without a QR-reference here
            reference_type = 'QRR'
            reference = structured_communication

        qr_code_vals =  [
            'SPC',                                                # QR Type
            '0200',                                               # Version
            '1',                                                  # Coding Type
            self.sanitized_acc_number,                            # IBAN
            'K',                                                  # Creditor Address Type
            (self.acc_holder_name or self.partner_id.name)[:71],  # Creditor Name
            creditor_addr_1,                                      # Creditor Address Line 1
            creditor_addr_2,                                      # Creditor Address Line 2
            '',                                                   # Creditor Postal Code (empty, since we're using combined addres elements)
            '',                                                   # Creditor Town (empty, since we're using combined addres elements)
            self.partner_id.country_id.code,                      # Creditor Country
            '',                                                   # Ultimate Creditor Address Type
            '',                                                   # Name
            '',                                                   # Ultimate Creditor Address Line 1
            '',                                                   # Ultimate Creditor Address Line 2
            '',                                                   # Ultimate Creditor Postal Code
            '',                                                   # Ultimate Creditor Town
            '',                                                   # Ultimate Creditor Country
            '{:.2f}'.format(amount),                              # Amount
            currency_name,                                        # Currency
            'K',                                                  # Ultimate Debtor Address Type
            debtor_partner.name[:71],                             # Ultimate Debtor Name
            debtor_addr_1,                                        # Ultimate Debtor Address Line 1
            debtor_addr_2,                                        # Ultimate Debtor Address Line 2
            '',                                                   # Ultimate Debtor Postal Code (not to be provided for address type K)
            '',                                                   # Ultimate Debtor Postal City (not to be provided for address type K)
            debtor_partner.country_id.code,                       # Ultimate Debtor Postal Country
            reference_type,                                       # Reference Type
            reference,                                            # Reference
            comment,                                              # Unstructured Message
            'EPD',                                                # Mandatory trailer part
        ]

        return '/report/barcode/?type=%s&value=%s&width=%s&height=%s&humanreadable=1' % ('QR', werkzeug.urls.url_quote_plus('\n'.join(qr_code_vals)), 256, 256)

    def _get_partner_address_lines(self, partner):
        """ Returns a tuple of two elements containing the address lines to use
        for this partner. Line 1 contains the street and number, line 2 contains
        zip and city. Those two lines are limited to 70 characters
        """
        line_1 = (partner and partner.street or '') + ' ' + (partner and partner.street2 or '')
        line_2 = partner.zip + ' ' + partner.city
        return line_1[:70], line_2[:70]

    def _is_qr_iban(self):
        """ Tells whether or not this bank account has a QR-IBAN account number.
        QR-IBANs are specific identifiers used in Switzerland as references in
        QR-codes. They are formed like regular IBANs, but are actually something
        different.
        """
        self.ensure_one()

        iid_start_index = 4
        iid_end_index = 8
        iid = self.sanitized_acc_number[iid_start_index : iid_end_index+1]
        return self.acc_type == 'iban' \
               and re.match('\d+', iid) \
               and 30000 <= int(iid) <= 31999 # Those values for iid are reserved for QR-IBANs only

    @api.model
    def _is_qr_reference(self, reference):
        """ Checks whether the given reference is a QR-reference, i.e. it is
        made of 27 digits, the 27th being a mod10r check on the 26 previous ones.
        """
        return reference \
               and len(reference) == 27 \
               and re.match('\d+$', reference) \
               and reference == mod10r(reference[:-1])

    def validate_swiss_code_arguments(self, currency, debtor_partner, reference_to_check=''):
        # reference_to_check added as an optional parameter in order not to break our stability policy.
        # For people having already installed the module, QRR won't be checked until
        # they update the module (as a change in the pdf report's xml sets a value in reference_to_check).
        # '' is used as default, as an empty field will pass None value,
        # and we want to be able to distinguish between those cases
        def _partner_fields_set(partner):
            return partner.zip and \
                   partner.city and \
                   partner.country_id.code and \
                   (self.partner_id.street or self.partner_id.street2)

        return _partner_fields_set(self.partner_id) and \
               _partner_fields_set(debtor_partner) and \
               (reference_to_check == '' or not self._is_qr_iban() or self._is_qr_reference(reference_to_check))
