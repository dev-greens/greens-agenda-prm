# Greens Agenda (v8)

### Rodar
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations crm
python manage.py migrate
python manage.py runserver
```
### Novidades
- Toggle de tema **chip** no rodapé (sem ícones internos), com label **CLARO/ESCURO**.
- Agenda corrigida: eventos exibidos com datas locais (sem timezone) e refetch após salvar.
- Relatório com **Tipo de visita (Presencial/Remoto)** e PDF atualizado.
- WhatsApp na página de Visitas com mensagem pronta; Dashboard com KPIs e gráficos.


## Passo 1 (Segurança, Donos e Auditoria)
- Login obrigatório (middleware + @login_required)
- Campos `owner` em Doctor/Appointment/Deal
- `UF` no médico e unicidade `CRM+UF` (condicional quando CRM preenchido)
- Relação Médicos ↔ Organizações (afiliações)
- Auditoria com `django-simple-history`
- Variáveis de ambiente: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`

**Como rodar:**
```bash
pip install -r requirements.txt
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```


### Rodar Docker

# 1) build + start
```bash
docker compose up -d --build
```

# 2) (primeira vez) criar superusuário
```bash
docker compose exec web python manage.py createsuperuser
```