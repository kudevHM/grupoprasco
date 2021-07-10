# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

class JobCosting(models.Model):
    _name = 'job.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin'] #odoo11
#    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Job Costing"
    _rec_name = 'number'
    
    @api.model
    def create(self,vals):
        number = self.env['ir.sequence'].next_by_code('job.costing')
        vals.update({
            'number': number,
        })
        return super(JobCosting, self).create(vals) 
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise Warning(_('You can not delete Job Cost Sheet which is not draft or cancelled.'))
        return super(JobCosting, self).unlink()
    
    @api.depends(
        'job_cost_line_ids',
        'job_cost_line_ids.product_qty',
        'job_cost_line_ids.cost_price',
    )
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum([(p.product_qty * p.cost_price) for p in rec.job_cost_line_ids])
                
    @api.depends(
        'job_labour_line_ids',
        'job_labour_line_ids.hours',
        'job_labour_line_ids.cost_price'
    )
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.hours * p.cost_price) for p in rec.job_labour_line_ids])

    @api.depends(
        'job_overhead_line_ids',
        'job_overhead_line_ids.product_qty',
        'job_overhead_line_ids.cost_price'
    )
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([(p.product_qty * p.cost_price) for p in rec.job_overhead_line_ids])

    @api.depends(
        'material_total',
        'labor_total',
        'overhead_total'
    )
    def _compute_jobcost_total(self):
        for rec in self:
            rec.jobcost_total = rec.material_total + rec.labor_total + rec.overhead_total
                
    @api.multi
    def _purchase_order_line_count(self):
        purchase_order_lines_obj = self.env['purchase.order.line']
        for order_line in self:
            order_line.purchase_order_line_count = purchase_order_lines_obj.search_count([('job_cost_id','=',order_line.id)])
            
    @api.multi
    def _timesheet_line_count(self):
        hr_timesheet_obj = self.env['account.analytic.line']
        for timesheet_line in self:
            timesheet_line.timesheet_line_count = hr_timesheet_obj.search_count([('job_cost_id', '=', timesheet_line.id)])
    
    @api.multi
    def _account_invoice_line_count(self):
        account_invoice_lines_obj = self.env['account.invoice.line']
        for invoice_line in self:
            invoice_line.account_invoice_line_count = account_invoice_lines_obj.search_count([('job_cost_id', '=', invoice_line.id)])
            
    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id
                
    number = fields.Char(
        readonly=True,
        default='New',
        copy=False,
    )
    name = fields.Char(
        required=True,
        copy=True,
        default='New',
        string='Name',
    )
    notes_job = fields.Text(
        required=False,
        copy=True,
        string='Job Cost Details'
    )
    user_id = fields.Many2one(
        'res.users', 
        default=lambda self: self.env.user, 
        string='Created By', 
        readonly=True
    )
    description = fields.Char(
        string='Description',
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id,
    )
    #readonly=True
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company', 
        readonly=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    contract_date = fields.Date(
        string='Contract Date',
    )
    start_date = fields.Date(
        string='Create Date',
        readonly=True,
        default=fields.Date.today(),
    )
    complete_date = fields.Date(
        string='Closed Date',
        readonly=True,
    )
    material_total = fields.Float(
        string='Total Material Cost',
        compute='_compute_material_total',
        store=True,
    )
    labor_total = fields.Float(
        string='Total Labour Cost',
        compute='_compute_labor_total',
        store=True,
    )
    overhead_total = fields.Float(
        string='Total Overhead Cost',
        compute='_compute_overhead_total',
        store=True,
    )
    jobcost_total = fields.Float(
        string='Total Cost',
        compute='_compute_jobcost_total',
        store=True,
    )
    job_cost_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','material')],
    )
    job_labour_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','labour')],
    )
    job_overhead_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type','=','overhead')],
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('customer','=', True)],
    )
    state = fields.Selection(
        selection=[
                    ('draft','Draft'),
                    ('confirm','Confirmed'),
                    ('approve','Approved'),
                    ('done','Done'),
                    ('cancel','Canceled'),
                  ],
        string='State',
        track_visibility='onchange',
        #default=lambda self: _('draft'),
        default='draft',
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
    )
    so_number = fields.Char(
        string='Sale Reference'
    )
#    issue_id = fields.Many2one(
#        'project.issue',
#        string='Job Issue',
#    ) #odoo11
    
    purchase_order_line_count = fields.Integer(
        compute='_purchase_order_line_count'
    )
    
    purchase_order_line_ids = fields.One2many(
        "purchase.order.line",
        'job_cost_id',
    )
    
    timesheet_line_count = fields.Integer(
        compute='_timesheet_line_count'
    )
    
    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'job_cost_id',
    )
    
    account_invoice_line_count = fields.Integer(
        compute='_account_invoice_line_count'
    )
    
    account_invoice_line_ids = fields.One2many(
        "account.invoice.line",
        'job_cost_id',
    )

    order_id = fields.Many2one('sale.order', string='order')
    

    _sql_constraints = [('uni_project_id', 'unique(project_id)', 'El Codigo del Proyecto se repite')]
        
    

    @api.multi
    def action_draft(self):
        for rec in self:
            rec.write({
                'state' : 'draft',
            })
    
    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.write({
                'state' : 'confirm',
            })
            rec.create_sale_order()
            rec.add_items_project_task()
        
    @api.multi
    def action_approve(self):
        for rec in self:
            rec.write({
                'state' : 'approve',
            })
    
    @api.multi
    def action_done(self):
        for rec in self:
            rec.write({
                'state' : 'done',
                'complete_date':date.today(),
            })
        
    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.write({
                'state' : 'cancel',
            })

    @api.multi
    def action_view_purchase_order_line(self):
        self.ensure_one()
        purchase_order_lines_obj = self.env['purchase.order.line']
        cost_ids = purchase_order_lines_obj.search([('job_cost_id','=',self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order Line',
            'res_model': 'purchase.order.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
        }
        return action
        
    @api.multi
    def action_view_hr_timesheet_line(self):
        hr_timesheet = self.env['account.analytic.line']
        cost_ids = hr_timesheet.search([('job_cost_id','=',self.id)]).ids
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line').read()[0]
        action['domain'] = [('id', 'in', cost_ids)]
        return action
        
    @api.multi
    def action_view_vendor_bill_line(self):
        account_invoice_lines_obj = self.env['account.invoice.line']
        cost_ids = account_invoice_lines_obj.search([('job_cost_id','=',self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Account Invoice Line',
            'res_model': 'account.invoice.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
        }
        action['context'] = {
           'create':False,
           'edit': False,
       }
        return action

    @api.multi
    def add_items_project_task(self):
        task_id = self.task_id
        if not self.task_id:
            user_id = self.env['res.users'].browse(self._uid)
            task_id = self.env['project.task'].create({
                'user_id': user_id.id,
                'project_id': self.project_id.id,
                'name': 'HT '+ self.name,
                'date_start': fields.Datetime.now(),
                'date_end': fields.Datetime.now()
            })
            for rec in self:
                rec.write({
                    'task_id': task_id.id,
                })

        for line in self.job_cost_line_ids:
            self.env['material.plan'].create({
                'material_task_id': task_id.id,
                'product_id': line.product_id.id,
                'description': line.product_id.name,
                'product_uom_qty': line.product_qty,
                'product_uom': line.uom_id.id
            })

    @api.multi
    def create_sale_order(self):

        for sale_id in self.order_id:
            sale_id.unlink()

        price_lists = self.env['product.pricelist'].search([('currency_id', '=', self.currency_id.id)])
        if len(price_lists) == 0:
            raise ValidationError(_('No existe lista de precio para generar la orden de compra'))

        so = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'pricelist_id': price_lists[0].id,
        })

        for line in self.job_cost_line_ids:
            tax_id = False
            if line.product_id.taxes_id:
                tax_id = line.product_id.taxes_id[0]

            self.env['sale.order.line'].create({
                'order_id': so.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.uom_id.id,
                'price_unit': line.list_price,
                'tax_id': [0],
                'price_subtotal': line.total_cost
            })

        for line in self.job_labour_line_ids:
            tax_id = False
            if line.product_id.taxes_id:
                tax_id = line.product_id.taxes_id[0]

            self.env['sale.order.line'].create({
                'order_id': so.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.hours,
                'product_uom': line.uom_id.id or line.product_id.uom_id.id or False,
                'price_unit': line.list_price,
                'tax_id': [0],
                'price_subtotal': line.total_cost
            })

        for line in self.job_overhead_line_ids:
            tax_id = False
            if line.product_id.taxes_id:
                tax_id = line.product_id.taxes_id[0]

            self.env['sale.order.line'].create({
                'order_id': so.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.uom_id.id or line.product_id.uom_id.id or False,
                'price_unit': line.list_price,
                'tax_id': [0],
                'price_subtotal': line.total_cost
            })

        for rec in self:
            rec.write({
                'order_id' : so.id,
            })