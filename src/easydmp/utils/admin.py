from django.contrib import admin

from guardian.admin import GuardedModelAdminMixin
from guardian.shortcuts import assign_perm
from guardian.shortcuts import get_objects_for_user

from easydmp.utils import get_model_name
from easydmp.utils import generate_default_permission_strings


class SetPermissionsMixin:

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if request.user.is_superuser:
            return
        if not change:
            default_permissions = generate_default_permission_strings(
                get_model_name(self.model)
            )
            permissions = default_permissions + getattr(self, 'set_permissions', [])
            for perm in permissions:
                assign_perm(perm, request.user, obj)


class ObjectPermissionModelAdmin(GuardedModelAdminMixin, admin.ModelAdmin):

    def get_queryset(self, request):
        """Limit queryset only to objects with change permission.

        If the optional method ``get_limited_queryset()`` is defined, return
        the set of this and the previous queryset.
        """
        qs = admin.ModelAdmin.get_queryset(self, request)
        if request.user.is_superuser:
            return qs

        # Run an explicit filter for the queryset, if any
        limit_qs = qs.none()
        if hasattr(self, 'get_limited_queryset'):
            limit_qs = self.get_limited_queryset(request) & qs

        # Get objects with 'change_<model_name>' object permission
        perm_qs = qs.none()
        if getattr(self, 'has_object_permissions', False):  # Avoid a db call
            model_name = get_model_name(self.model)
            app_label = self.model._meta.app_label
            permission_name = 'change_{}'.format(model_name)
            perm_qs = get_objects_for_user(
                request.user,
                '{}.{}'.format(app_label, permission_name),
                klass=qs,
                accept_global_perms=False,
            )

        qs = perm_qs | limit_qs

        return qs.distinct()
