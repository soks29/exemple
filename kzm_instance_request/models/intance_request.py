from odoo import fields, models, api, _
from datetime import timedelta, date, datetime
from odoo.exceptions import ValidationError


class Instance_Request(models.Model):
    _name = "kzm.instance.request"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "creation d'instance"

    name = fields.Char(string="Designation", tracking=True)
    reference = fields.Char(string="Order Reference",
                            required=True, copy=False,
                            default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    adress_ip = fields.Char(string="Adresse IP")
    cpu = fields.Char(string="CPU")
    ram = fields.Char(string="RAM")
    disk = fields.Char(string="DISK")
    url = fields.Char(string="URL")
    state = fields.Selection(
        selection=[('brouillon', 'Brouillon'), ('soumise', 'Soumise'), ('entraitement', 'En traitement'),
                   ('traite', 'Traitée')],
        default='brouillon', tracking=True)
    limit_date = fields.Date(tracking=True)
    treat_date = fields.Datetime()
    treat_duration = fields.Float()

    _sql_constraints = [
        ('adresse_ip_unique',
         'unique (adress_ip)',
         "Please enter a unique ip address, the given address already exists !")
    ]

    def action_draft(self):
        for x in self:
            x.state = 'brouillon'

    def action_submissive(self):
        for x in self:
            x.state = 'soumise'

    def action_processing(self):
        for x in self:
            x.state = 'entraitement'

    def action_treated(self):
        for x in self:
            x.state = 'traite'
            x.treat_date = datetime.now()

    def action_scheduled(self):
        day = self.env['kzm.instance.request'].search([('limit_date', '<=', date.today() + timedelta(days=5))])
        for x in day:
            x.action_submissive()

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('instance.reconcile') or _('New')
        res = super(Instance_Request, self).create(vals)
        return res

    # def unlink(self):
    #     for state in self:
    #         if state.name != 'brouillon':
    #             raise exceptions.UserError(_("Cannot delete an instance which is in a state different to draft"))
    #         return super().unlink()

    def unlink(self):
        for x in self:
            if x.state != 'brouillon':
                raise ValidationError(_("You can only delete instance requests in Draft status!"))
            return super(Instance_Request, x).unlink()

    def write(self, vals):
        if vals.get('limit_date'):

            users = self.env.ref('kzm_instance_request.group_kzm_instance_request_responsible').users
            for user in users:
                self.activity_schedule('kzm_instance_request.activity_mail_a_traite', user_id=user.id,
                                       note=f' please approve the {self.reference} instance')

            date_time_obj = datetime.strptime(vals['limit_date'], '%Y-%m-%d')
            d = date_time_obj.date()
            if d < date.today():
                raise ValidationError(_("You cannot set a deadline later than today!!"))
        return super(Instance_Request, self).write(vals)

