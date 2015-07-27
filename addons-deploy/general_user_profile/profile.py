# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _

class profile(osv.osv):
    _name = "profile"
    _description = "Profile"
    _columns = {
#         'users_ids': fields.one2many('res.users', 'profile_id', string='Users', required=False, readonly=True),
        'users_ids': fields.many2many('res.users', 'res_users_profiles_rel', 'profile', 'user_id', string='Profiles', 
                                        required=False, readonly=False, help='The profile of the user. The admin should have no profile.'),
                
        'name': fields.char('Profile Name', size=64, required=True),
        'groups_ids': fields.many2many('res.groups', 'profiles_groups_rel', 'profile_id', 'group_id', string='Groups', required=False, readonly=False),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'The name of the profile must be unique!'),
    ]
    _order = "name"
    
    def copy(self, cr, uid, id, default=None, context=None):
        name = ''
        sql = '''
            SELECT name
            FROM profile
            WHERE id = %s
        '''
        cr.execute(sql, (id,))
        if cr.rowcount > 0:
            name = cr.fetchone()[0]
        default.update({'name': _('%s (copy)') % name, 'users_ids': []})        
        return super(profile, self).copy(cr, uid, id, default, context)
    
    def unlink(self, cr, uid, ids, context=None):
        user_ids = []
        for line in self.browse(cr, uid, ids):
            if line.users_ids:
                for user in line.users_ids:
                    user_ids.append(user.id)
        super(profile, self).unlink(cr, uid, ids, context)
        return self.update_groups(cr, uid, user_ids)
    
    def write(self, cr, uid, ids, vals, context=None):
        super(profile, self).write(cr, uid, ids, vals, context)
        for line in self.browse(cr, uid, ids):
            if line.users_ids:
                user_ids = [x.id for x in line.users_ids]
                self.update_groups(cr, uid, user_ids)
        return True
    
    def update_groups(self, cr, uid, uids):
        users_pool = self.pool.get('res.users')
        if uids:
            for user in users_pool.browse(cr, uid, uids):
                if not user.profile_ids and user.id != 1:
                    users_pool.write(cr, uid, [user.id], {'groups_id': [[6,0,[]]]})
                if user.profile_ids:
                    sql = '''
                        DELETE
                        FROM res_groups_users_rel
                        WHERE uid = %s
                    '''%(user.id)
                    cr.execute(sql)
                    groups_ids = []
                    for profile in user.profile_ids:
                        groups_ids += [x.id for x in profile.groups_ids if x.id not in groups_ids]
                    users_pool.write(cr, uid, [user.id], {'groups_id': [[6,0,groups_ids]]})
#                 if user.id == 1:
#                     sql = '''
#                         DELETE
#                         FROM res_groups_users_rel
#                         WHERE uid = 1
#                     '''
#                     cr.execute(sql)
#                     sql = '''
#                         INSERT INTO res_groups_users_rel(uid, gid)
#                         SELECT DISTINCT ru.id, rg.id
#                         FROM res_users ru, res_groups rg
#                         WHERE (ru.id = 1) 
#                     '''
#                     cr.execute(sql) 
        return True
    
profile()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
