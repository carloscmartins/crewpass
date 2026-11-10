# CrewPass

Plataforma web para credenciamento e controle de entrada/saída de equipes operacionais de eventos. Leia `PRD.md` antes de alterar o escopo do produto. As referências de interface estão em `Design-Reference/lamborghini/`.

## Requisitos

- Python 3.12+ (o projeto segue Django 6.0).
- Node.js e npm para compilar Tailwind CSS.

## Desenvolvimento local (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:DJANGO_DEBUG = 'true'
python -m pip install -r requirements.txt
npm install
npm run build:css
npm run build:js
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Em outro terminal, `npm run watch:css` recompila o CSS durante o desenvolvimento. Testes: `python manage.py test`.

Configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e `DJANGO_ALLOWED_HOSTS` como variáveis de ambiente. `DJANGO_DEBUG` fica desativado por padrão; em desenvolvimento, habilite-o como acima para usar a chave local insegura. Com debug desativado, a chave é obrigatória, HTTPS é forçado e os cookies de sessão/CSRF ficam marcados como seguros. Crie organizações e associações de usuários pelo `/admin/`; o dashboard só mostra organizações com associação ativa.

Em desenvolvimento (`DJANGO_DEBUG=true`), `Origin: null` é aceito por padrão somente para hosts locais, para compatibilidade com pré-visualizações incorporadas; o token CSRF continua obrigatório. Desative essa exceção com `DJANGO_ALLOW_NULL_ORIGIN=false`. Configure origens adicionais confiáveis em `DJANGO_CSRF_TRUSTED_ORIGINS`, separadas por vírgula, somente quando necessário.
