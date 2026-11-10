# CrewPass — instruções para agentes

- Antes de iniciar qualquer Sprint X, leia `PRD.md` e pergunte ao usuário qual sprint e escopo foram autorizados. O plano do PRD é uma proposta; confirme também decisões pendentes, sem inventá-las.
- `PRD.md` é a referência de produto. O CrewPass credencia equipes operacionais de eventos; não é venda de ingressos nem controle de acesso do público.
- Preserve a separação entre `StaffMember` (cadastro reutilizável), `EventAssignment` (vínculo pessoa/evento) e `Credential` (credencial daquela participação). Isole consultas e ações por organização.
- As telas de eventos/cadastros e os relatórios exigem associação ativa de administrador/supervisor. A operação permite administrador/supervisor ativos ou operador com `EventOperatorGrant` ativo para o evento, associação ativa na mesma organização e evento ativo; não exponha dashboards, histórico ou relatórios a operadores.
- Emita/cancele/substitua credenciais pelos serviços de `credentials`, que também registram o ator em `CredentialAuditLog`; a restrição única no banco permite no máximo uma ativa por participação. O QR contém somente o token aleatório, nunca dados pessoais.
- Movimentações de acesso precisam ser validadas no servidor, com confirmação explícita, proteção contra concorrência e histórico/auditoria preservados; não exponha dados pessoais no QR Code.
- Use `Design-Reference/lamborghini/design-system-dark.html` e `design-system-light.html` como referências visuais obrigatórias. O PRD prefere tema escuro: use superfícies pretas/grafite, texto claro e dourado como destaque, mantendo contraste e adaptação responsiva; não copie marca ou conteúdo automotivo.
- Priorize UX mobile/tablet para operação de acesso: evento sempre identificável, leitura ou busca manual, ação sugerida clara e confirmação antes de registrar.
- Interface e mensagens em pt-BR; nomes de código em inglês. Para SEO, trabalhe páginas públicas com HTML semântico, títulos/metadados e compartilhamento adequados, desempenho e conteúdo acessível; mantenha áreas autenticadas e dados operacionais fora de indexação e de metadados públicos.
- Stack executável: Django 6 em Python 3.12+, Django Templates, Tailwind CSS 4 via npm e SQLite local. Use os comandos do `README.md`; confira `requirements.txt` e `package-lock.json` ao mexer em dependências.
