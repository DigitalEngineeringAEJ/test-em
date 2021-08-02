from odoo import _, fields, models


class MailActivityEditWizard(models.TransientModel):
    _name = "mail.activity.edit.wizard"
    _description = "Mail Activity Edit Wizard"

    schedule_date = fields.Datetime(string="Scheduled Date")
    duration = fields.Float(string="Duration")
    user_id = fields.Many2one('res.users', string='Assigned To')

    def save(self):
        activities = self.env['mail.activity'].browse(self._context['activity_ids'])
        for activity in activities:
            if activity.planning != 'detail_plan':
                activity.planning = 'detail_plan'
            activity.schedule_date = self.schedule_date
            activity.duration = self.duration
            activity.date_deadline = self.schedule_date.date()
            activity.user_id = self.user_id.id if self.user_id else False

