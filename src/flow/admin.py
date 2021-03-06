from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from .models import Node
from .models import Edge
from .models import FSA


def has_payload(obj):
    try:
        obj.payload
        return True
    except ObjectDoesNotExist:
        return False
has_payload.short_description = 'Has Payload'
has_payload.boolean = True


class PayloadListFilter(admin.SimpleListFilter):
    title = 'Payload'
    parameter_name = 'payload'

    def lookups(self, request, _model_admin):
        return (
            ('True', 'Yes'),
            ('False', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(payload__isnull=False)
        if self.value() == 'False':
            return queryset.filter(payload__isnull=True)
        return queryset


class EmptyEdgeFilter(admin.SimpleListFilter):
    title = 'Empty'
    parameter_name = 'empty'

    def lookups(self, request, _model_admin):
        return (
            ('both', 'Both'),
            ('none', 'None'),
            ('prev', 'Previous'),
            ('next', 'Next'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'both':
            return queryset.filter(prev_node__isnull=True, next_node__isnull=True)
        if self.value() == 'none':
            return queryset.filter(prev_node__isnull=False, next_node__isnull=False)
        if self.value() == 'prev':
            return queryset.filter(prev_node__isnull=True, next_node__isnull=False)
        if self.value() == 'next':
            return queryset.filter(prev_node__isnull=False, next_node__isnull=True)
        return queryset


class PrevEdgeInline(admin.StackedInline):
    model = Edge
    fk_name = 'prev_node'
    exclude = ('cloned_from', 'cloned_when')


class EdgeAdmin(admin.ModelAdmin):
    list_display = ['id', 'condition', 'prev_node', 'next_node', has_payload]
    list_display_links = ['id', 'condition', 'prev_node']
    list_filter = [PayloadListFilter, EmptyEdgeFilter]
    readonly_fields = ('cloned_from', 'cloned_when')
admin.site.register(Edge, EdgeAdmin)


class NodeInline(admin.StackedInline):
    model = Node
    exclude = ('cloned_from', 'cloned_when')


class NodeAdmin(admin.ModelAdmin):
    list_display = ['id', '__str__', 'depends', 'fsa', has_payload]
    list_display_links = ['id']
    list_filter = [PayloadListFilter, 'fsa']
    readonly_fields = ('cloned_from', 'cloned_when')
    inlines = [PrevEdgeInline]

admin.site.register(Node, NodeAdmin)


class FSAAdmin(admin.ModelAdmin):
    list_display = ['slug', 'id']
    readonly_fields = ('cloned_from', 'cloned_when')
    inlines = [NodeInline]
admin.site.register(FSA, FSAAdmin)
