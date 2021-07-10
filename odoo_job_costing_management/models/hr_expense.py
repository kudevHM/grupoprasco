# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "payment_requested":
                expense.state = "payment_requested"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('payment_requested', 'Payment Requested'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the expense.")

    doc_number = fields.Char(string='number ruc')
    partner_id = fields.Many2one('res.partner')

    #@api.one
    #@api.depends('partner_id')
    #def _get_doc_partner(self):
        #if self.partner_id and self.partner_id.doc_type:
            #tipo_doc = self.env['pe.datas'].get_name_item_by_table_pe_doc_type(self.partner_id.doc_type)
            #self.doc_number = '%s %s'%(tipo_doc or '', self.partner_id.doc_number or '')

    #@api.onchange('partner_id')
    #def onchange_product_id(self):
    #    self._get_doc_partner()

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'payment_requested':
            return 'odoo_job_costing_management.mt_expense_payment_requested'
        return super(HrExpenseSheet, self)._track_subtype(init_values)

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'payment_requested'):
            self.activity_schedule('odoo_job_costing_management.mail_act_expense_payment_requested', user_id=expense_report.sudo()._get_responsible_for_payment_requested().id)
        self.filtered(lambda hol: hol.state == 'payment_requested').activity_feedback(['odoo_job_costing_management.mail_act_expense_payment_requested'])
        return super(HrExpenseSheet, self).activity_update()

    def _get_responsible_for_payment_requested(self):
        if self.user_id:
            return self.user_id
        else:
            raise UserError(_("please, enter the payment user"))

    def _get_responsible_for_approval(self):
        if self.approver_user_id:
            return self.approver_user_id
        else:
            raise UserError(_("please, enter the approver user"))

    @api.constrains('expense_line_ids', 'employee_id')
    def _check_employee(self):
        pass
        #for sheet in self:
        #    employee_ids = sheet.expense_line_ids.mapped('employee_id')
        #    if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != sheet.employee_id):
        #        raise ValidationError(_('You cannot add expenses of another employee.'))

    @api.multi
    def action_sheet_payment_requested(self):
        if self.state == 'post':
            self.write({'state': 'payment_requested'})
            self.activity_update()
        else:
            raise UserError(_("status does not apply."))

    user_id = fields.Many2one('res.users', 'Manager', readonly=True, copy=False,
                              states={'draft': [('readonly', False)], 'submit': [('readonly', False)]}, track_visibility='onchange',
                              oldname='responsible_id')

    approver_user_id = fields.Many2one('hr.employee', string="Approver User", readonly=True, copy=False, track_visibility='onchange',
                              states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('payment_requested', 'Payment Requested'),
        ('done', 'Paid'),
        ('cancel', 'Refused')

    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft',
        required=True, help='Expense Report State')


