

from django.contrib.auth.admin import User, UserAdmin
from django.contrib.auth.models import Group
import django.contrib.admin

def generate_adder(group, add=True):
    def function(modeladmin, request, queryset):
        staff_group = Group.objects.filter(name=group)
        assert len(staff_group) == 1, "Search for group %s len!=1."%group
        staff_group = staff_group[0]
        for obj in queryset:
            if add:
                staff_group.user_set.add(obj)
            else:
                staff_group.user_set.remove(obj)
    return function
    
add_to_group_cava_staff      = generate_adder("CAVA Staff")
add_to_group_cava_staff.short_description = "Add to group CAVA Staff"
add_to_group_cava            = generate_adder("CAVA Members")
add_to_group_cava_staff.short_description = "Add to group CAVA Staff"
remove_from_group_cava_staff = generate_adder("CAVA Staff", add=False)
remove_from_group_cava_staff.short_description = "Remove from group CAVA Staff"
remove_from_group_cava       = generate_adder("CAVA Members", add=False)
remove_from_group_cava.short_description = "Add to group CAVA Members"

def list_groups_of_user(user):
    groups = django.contrib.auth.admin.Group.objects.filter(user__id=user.id)
    return ", ".join(unicode(x) for x in groups)
def dummy(user):
    return "x"

UserAdmin.actions.append(add_to_group_cava_staff)
UserAdmin.list_display = UserAdmin.list_display + (list_groups_of_user, )
UserAdmin.list_display = UserAdmin.list_display + (dummy, )

class User2(User):
    class Meta:
        db_table = 'auth_user'

#django.contrib.admin.site.register(User2, UserAdmin)
