from django.conf.urls import url

from .views import (
    CreatePlanEditorInvitationView,
    ListPlanEditorInvitationView,
    AcceptPlanEditorInvitationView,
    ResendPlanEditorInvitationView,
    RevokePlanEditorInvitationView,
    CreatePlanViewerInvitationView,
    ListPlanViewerInvitationView,
    AcceptPlanViewerInvitationView,
    ResendPlanViewerInvitationView,
    RevokePlanViewerInvitationView,
)


PLAN_RE = r'(?P<plan>\d+)'
UUID_RE = r'(?P<uuid>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})'

urlpatterns = [
    url(r'plan/' + PLAN_RE + r'/editor/$', ListPlanEditorInvitationView.as_view(), name='invitation_plan_editor_list'),
    url(r'plan/' + PLAN_RE + r'/editor/new/$', CreatePlanEditorInvitationView.as_view(), name='invitation_plan_editor_create'),
    url(UUID_RE + r'/plan/editor/resend/$', ResendPlanEditorInvitationView.as_view(), name='invitation_plan_editor_resend'),
    url(UUID_RE + r'/plan/editor/accept/$', AcceptPlanEditorInvitationView.as_view(), name='invitation_plan_editor_accept'),
    url(UUID_RE + r'/plan/editor/revoke/$', RevokePlanEditorInvitationView.as_view(), name='invitation_plan_editor_revoke'),

    url(r'plan/' + PLAN_RE + r'/viewer/$', ListPlanViewerInvitationView.as_view(), name='invitation_plan_viewer_list'),
    url(r'plan/' + PLAN_RE + r'/viewer/new/$', CreatePlanViewerInvitationView.as_view(), name='invitation_plan_viewer_create'),
    url(UUID_RE + r'/plan/viewer/resend/$', ResendPlanViewerInvitationView.as_view(), name='invitation_plan_viewer_resend'),
    url(UUID_RE + r'/plan/viewer/accept/$', AcceptPlanViewerInvitationView.as_view(), name='invitation_plan_viewer_accept'),
    url(UUID_RE + r'/plan/viewer/revoke/$', RevokePlanViewerInvitationView.as_view(), name='invitation_plan_viewer_revoke'),
]
