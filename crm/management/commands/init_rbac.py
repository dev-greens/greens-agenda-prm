from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.apps import apps

APP = "crm"
MODELS = ["doctor", "appointment", "visitreport", "organization", "deal"]

GROUPS = {
    "Admin": {"all_perms": True},
    "Gestor": {"perms": ["view", "add", "change"]},
    "Representante": {"perms": ["view", "add", "change"]},
    "Marketing": {"perms": ["view"]},
}

class Command(BaseCommand):
    help = "Cria grupos/permissões e usuários de exemplo (RBAC)."

    def handle(self, *args, **kwargs):
        # 1) Grupos e permissões
        for gname, rule in GROUPS.items():
            g, _ = Group.objects.get_or_create(name=gname)
            if rule.get("all_perms"):
                perms = Permission.objects.all()
            else:
                perms = []
                for mn in MODELS:
                    try:
                        model = apps.get_model(APP, mn.capitalize())
                    except LookupError:
                        model = apps.get_model(APP, mn)
                    for cod in rule["perms"]:
                        codename = f"{cod}_{model._meta.model_name}"
                        try:
                            p = Permission.objects.get(codename=codename)
                            perms.append(p)
                        except Permission.DoesNotExist:
                            pass
            g.permissions.set(perms)

        # 2) Usuários de exemplo (senha: 123456)
        seed_users = [
            ("admin", "Admin", True),
            ("gestor", "Gestor", False),
            ("rep", "Representante", False),
            ("mkt", "Marketing", False),
        ]
        for uname, gname, is_super in seed_users:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={"is_staff": True, "is_superuser": is_super, "email": f"{uname}@example.com"},
            )
            u.set_password("123456")
            u.is_staff = True
            u.is_superuser = is_super
            u.save()
            u.groups.set([Group.objects.get(name=gname)])

        self.stdout.write(self.style.SUCCESS("RBAC pronto. Usuários: admin/gestor/rep/mkt (senha 123456)."))
