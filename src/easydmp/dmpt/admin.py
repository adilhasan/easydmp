# -*- coding: utf-8 -*-
from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from easydmp.eestore.models import EEStoreMount

from .models import Template
from .models import Section
from .models import Question
from .models import CannedAnswer


@admin.register(Template)
class TemplateAdmin(GuardedModelAdmin):
    list_display = ('id', 'title')
    list_display_links = ('title', 'id')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'position',
        'section_depth',
        'id',
        'label',
        'title',
    )
    list_display_links = ('template', 'section_depth', 'id', 'position')
    list_filter = ('template',)
    actions = [
        'increment_position',
        'decrement_position',
    ]

    def increment_position(self, request, queryset):
        for q in queryset.order_by('-position'):
            q.position += 1
            q.save()
    increment_position.short_description = 'Increment position by 1'

    def decrement_position(self, request, queryset):
        for q in queryset.order_by('position'):
            q.position -= 1
            q.save()
    decrement_position.short_description = 'Decrement position by 1'


@admin.register(CannedAnswer)
class CannedAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'question',
        'choice',
        'position',
        'id',
        'has_edge',
    )
    list_display_links = ('id', 'question')
    actions = [
        'create_edge',
        'update_edge',
    ]
    list_filter = ('question',)

    def create_edge(self, request, queryset):
        for q in queryset.all():
            if not q.edge:
                q.create_edge()
    create_edge.short_description = 'Create edge'

    def update_edge(self, request, queryset):
        for q in queryset.all():
            if q.edge:
                q.update_edge()
            else:
                q.create_edge()
    update_edge.short_description = 'Update edge'

    def has_edge(self, obj):
        return True if obj.edge else False
    has_edge.short_description = 'Edge'
    has_edge.boolean = True


class CannedAnswerInline(admin.StackedInline):
    model = CannedAnswer


class EEStoreMountInline(admin.StackedInline):
    model = EEStoreMount


class EEStoreTypeFilter(admin.SimpleListFilter):
    title = 'EEStore type'
    parameter_name = 'eestore'

    def lookups(self, request, model_admin):
        types = EEStoreMount.objects.values_list('eestore_type__name', flat=True).distinct()
        return tuple(zip(*(types, types)))

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(eestore__eestore_type__name=self.value())
        return queryset


class SectionFilter(admin.SimpleListFilter):
    title = 'Section'
    parameter_name = 'section'

    def lookups(self, request, model_admin):
        sections = Section.objects.all()
        template_id = request.GET.get('section__template__id__exact', None)
        if template_id:
            sections = sections.filter(template_id=template_id)
        lookups = []
        for section in sections:
            lookups.append((section.pk, str(section)))
        return lookups

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(section__id=self.value())
        return queryset


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'position',
        'id',
        'label',
        'question',
        'section',
        'input_type',
        'obligatory',
        'has_node',
        'get_mount',
    )
    list_display_links = ('position', 'id', 'question')
    actions = [
        'create_node',
        'toggle_obligatory',
        'increment_position',
        'decrement_position',
    ]
    list_filter = [
        'obligatory',
        'section__template',
        SectionFilter,
        EEStoreTypeFilter,
    ]
    inlines = [
        CannedAnswerInline,
        EEStoreMountInline,
    ]
    save_on_top = True

    def has_node(self, obj):
        return True if obj.node else False
    has_node.short_description = 'Node'
    has_node.boolean = True

    def get_mount(self, obj):
        return obj.eestore.eestore_type if obj.eestore else ''
    get_mount.short_description = 'EEStore'
    get_mount.admin_order_field = 'eestore'

    def create_node(self, request, queryset):
        for q in queryset.all():
            if not q.node:
                q.create_node()
    create_node.short_description = 'Create node'

    def toggle_obligatory(self, request, queryset):
        for q in queryset.all():
            q.obligatory = not q.obligatory
            q.save()
    toggle_obligatory.short_description = 'Toggle obligatoriness'

    def increment_position(self, request, queryset):
        for q in queryset.order_by('-position'):
            q.position += 1
            q.save()
    increment_position.short_description = 'Increment position by 1'

    def decrement_position(self, request, queryset):
        for q in queryset.order_by('position'):
            q.position -= 1
            q.save()
    decrement_position.short_description = 'Decrement position by 1'
