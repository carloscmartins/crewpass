from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField('nome', max_length=180)
    slug = models.SlugField('identificador', max_length=200, unique=True, blank=True)
    legal_name = models.CharField('razão social', max_length=200, blank=True)
    is_active = models.BooleanField('ativa', default=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'organização'
        verbose_name_plural = 'organizações'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'organizacao'
            candidate = base_slug
            suffix = 2
            while Organization.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base_slug}-{suffix}'
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        OPERATOR = 'OPERATOR', 'Operador'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='organização',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        verbose_name='usuário',
    )
    role = models.CharField('perfil', max_length=16, choices=Role.choices, default=Role.OPERATOR)
    is_active = models.BooleanField('ativo', default=True)
    created_at = models.DateTimeField('adicionado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['organization__name', 'user__email']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user'],
                name='unique_user_per_organization',
            ),
        ]
        verbose_name = 'associação de usuário'
        verbose_name_plural = 'associações de usuários'

    def __str__(self):
        return f'{self.user} — {self.organization} ({self.get_role_display()})'
