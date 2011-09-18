# Create your views here.

import re
import textwrap

from django.contrib.auth.views import password_change, password_change_done,\
     password_reset, password_reset_done

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.template.loader import get_template

#def logout(request):
#    from django.contrib.auth import logout
#    logout(request)
#    return redirect('cal.views.redirect_to_now')
from django.contrib.auth.views import logout

def userpage(request):
    """User's home page."""
    can_change_username = request.user.username[:10] == 'openiduser'
    
    return render_to_response("userpage.html",
                              RequestContext(request, locals()))



class UserNameField(forms.CharField):
    """Like a CharField but validates """
    username_re = re.compile(r'^[a-zA-Z0-9_@+.-]{5,30}$')
    def clean(self, value):
        if len(value) < 5:
            raise forms.ValidationError("Username must be at least "\
                                        "five characters")
        if not self.username_re.match(value):
            raise forms.ValidationError("Username must be contain only "
                                        "letters, numbers, _, @, +, . and -.")
        return super(UserNameField, self).clean(value)
class ChangeUsernameForm(forms.Form):
    new_username = UserNameField(max_length=30)
#    next = forms.CharField(widget=forms.HiddenInput())

def change_username(request):
    """Allow a user to change their username if it is openiduser*
    """
    # Deny anonymous users.
    if isinstance(request.user, AnonymousUser):
        error = "You are not logged in"
        return render_to_response("change_username.html",
                                  RequestContext(request, locals()))
    # Deny users who don't have a username of openiduser*
    if request.user.username[:10] != "openiduser":
        error = "You do not currently have an openid username, "\
                "thus you can't change your username right now."
        return render_to_response("change_username.html",
                                  RequestContext(request, locals()))

    if request.method == "POST":
        form = ChangeUsernameForm(request.POST)
        if form.is_valid():
            newname = form.cleaned_data['new_username']
            request.user.username = newname
            request.user.save()
            del form
            successful = True
#            if 'next' in request.REQUEST:
#                return HttpRedirect(request.REQUEST['next'])
    else:
        form = ChangeUsernameForm()
    return render_to_response("change_username.html",
                              RequestContext(request, locals()))

@user_passes_test(lambda u: u.is_staff)
def list_groups(request):
    all_users = User.objects.all().order_by("username")
    rows = [ ]
    for user in all_users:
        groups = Group.objects.filter(user__id=user.id).order_by("name")
        groups = [str(x) for x in groups]
        perms_ = user.user_permissions.values()
        perms_ = [x['name'] for x in perms_]
        rows.append((user, groups, perms_))
        

    tmpl = Template("""
    <table border=1>
    <tr><td>User</td><td>Groups</td><td>Non-group permissions</td></tr>
    {% for user, groups, perms_ in rows %}
    <tr><td>{{user}}</td><td>{{groups}}</td><td>{{perms_}}</td></tr>
    {% endfor %}
    </table><p>
    Go to the <a href="/admin/">admin area</a> to adjust permissions.
    """)
    return HttpResponse(tmpl.render(RequestContext(request, locals())))


def restructured_text_template(request, template):
    if extra_context is None: extra_context = {}
    dictionary = {'params': kwargs}
    for key, value in extra_context.items():
        if callable(value):
            dictionary[key] = value()
        else:
            dictionary[key] = value

    from docutils.core import publish_parts
    docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS",{})
    t = loader.get_template(template)

    parts = publish_parts(source=smart_str(t),
                          writer_name="html4css1",
                          settings_overrides=docutils_settings)
    return mark_safe(force_unicode(parts["fragment"]))

    c = RequestContext(request, dictionary)
    return HttpResponse(t.render(c), mimetype=mimetype)
