# CrewPass — Product Requirements Document (PRD)

**Produto:** CrewPass  
**Versão:** 1.0  
**Status:** Base inicial do MVP — decisões em aberto identificadas  
**Data:** 06/11/2026  
**Idioma da interface:** Português do Brasil (pt-BR)

---

## 1. Visão geral

O CrewPass é uma plataforma web para credenciamento e controle de entrada e saída de profissionais que trabalham na operação de eventos.

O produto atende produtoras, organizadoras e empresas responsáveis por eventos que precisam cadastrar equipes, emitir credenciais e acompanhar a presença de profissionais como segurança, limpeza, carregadores, bombeiros civis, equipes de ambulância, produção, montagem e equipes técnicas.

A identificação será feita por **pulseiras físicas com QR Code**. Operadores utilizarão celulares ou tablets para ler os códigos e registrar as movimentações.

O CrewPass não é, no MVP, uma plataforma de venda de ingressos nem um sistema de controle de acesso do público geral.

## 2. Problema e oportunidade

O controle de equipes em eventos pode depender de planilhas, listas impressas e anotações manuais. Isso dificulta a localização de profissionais, torna a operação mais lenta e aumenta o risco de registros duplicados, incompletos ou inconsistentes.

O CrewPass pretende centralizar o processo e oferecer:

- Cadastro reutilizável de profissionais e empresas.
- Associação de profissionais a eventos, equipes e funções.
- Credenciais individuais por participação em evento.
- Registro digital de entradas e saídas.
- Consulta de quem está presente no evento.
- Histórico de movimentações e rastreabilidade.
- Indicadores e relatórios operacionais.

## 3. Objetivos

### 3.1 Objetivo principal

Digitalizar o credenciamento e o controle de entrada e saída das equipes operacionais de eventos.

### 3.2 Objetivos específicos

1. Centralizar os cadastros de organizações, eventos, empresas e profissionais.
2. Reutilizar o cadastro de um profissional em diferentes eventos.
3. Gerar credenciais individuais com QR Code.
4. Simplificar o registro de entrada e saída por celular ou tablet.
5. Identificar profissionais presentes, ainda não registrados e que já saíram.
6. Calcular períodos de permanência com base nas movimentações.
7. Disponibilizar histórico, auditoria e relatórios básicos.
8. Reduzir o trabalho manual de consolidação das informações.

## 4. Público-alvo e usuários

### 4.1 Público-alvo

- Produtoras e organizadoras de eventos.
- Empresas responsáveis pela operação de eventos.
- Empresas terceirizadas que fornecem equipes.
- Responsáveis pelo credenciamento e supervisores operacionais.

### 4.2 Perfis de acesso

**Administrador da plataforma**
- Administra organizações clientes e aspectos gerais da plataforma.
- Possui acesso administrativo separado dos usuários das organizações.

**Administrador da organização**
- Gerencia os dados da própria organização.
- Cadastra eventos, empresas, profissionais, equipes e usuários.
- Emite e cancela credenciais.
- Consulta dashboards e relatórios.

**Supervisor do evento**
- Acompanha a operação do evento.
- Consulta profissionais e movimentações.
- Pode realizar correções autorizadas, sempre com justificativa e trilha de auditoria.

**Operador de acesso**
- Acessa os eventos para os quais foi autorizado.
- Registra entradas e saídas por QR Code ou pesquisa manual.
- Não possui acesso irrestrito à administração dos cadastros.

As permissões exatas poderão ser simplificadas durante a implementação, mas o isolamento entre organizações e a separação entre administração e operação são requisitos do produto.

## 5. Escopo do MVP

### 5.1 Incluído no MVP

- Autenticação de usuários.
- Cadastro de organizações clientes.
- Cadastro e gerenciamento de eventos.
- Cadastro de empresas prestadoras de serviços.
- Cadastro de profissionais.
- Categorias de equipes e funções.
- Associação de profissionais a eventos.
- Geração e gerenciamento de credenciais com QR Code.
- Apoio à impressão/exportação da credencial para pulseira física.
- Registro de entrada e saída por leitura de QR Code.
- Pesquisa manual como alternativa à leitura.
- Sugestão automática de entrada ou saída, com possibilidade de alteração pelo operador.
- Lista de profissionais presentes.
- Histórico de movimentações.
- Dashboard e relatórios básicos.
- Importação de profissionais por Excel ou CSV, com validação.
- Auditoria de ações relevantes.

### 5.2 Fora do escopo inicial

- Venda ou validação de ingressos do público.
- Controle de acesso por áreas específicas, como palco, camarim ou backstage.
- Reconhecimento facial ou biometria.
- Integração com catracas ou equipamentos físicos.
- Aplicativos nativos Android e iOS.
- Controle de jornada trabalhista, folha de pagamento ou apuração legal de horas.
- Geolocalização dos profissionais.
- Inteligência artificial.
- Compartilhamento global de cadastros de empresas entre organizações.
- Operação offline e sincronização entre dispositivos, até que essa decisão seja tomada.

### 5.3 Princípio de escopo

O CrewPass deverá ser desenvolvido como um MVP simples e evolutivo. O PRD é uma referência viva: regras e funcionalidades poderão ser ajustadas com base no uso real, sem introduzir complexidade antes de existir necessidade validada.

## 6. Conceitos fundamentais do domínio

É importante manter separados três conceitos:

1. **Profissional (`StaffMember`):** cadastro reutilizável da pessoa.
2. **Participação no evento (`EventAssignment`):** vínculo daquela pessoa com um evento, incluindo empresa, equipe e função naquele contexto.
3. **Credencial (`Credential`):** identificação emitida para aquela participação específica.

Uma pessoa poderá participar de vários eventos, com empresas, funções e credenciais diferentes, sem que seja necessário duplicar seu cadastro permanente.

Uma credencial cancelada ou substituída não deverá ser reutilizada para outra participação.

## 7. Requisitos funcionais

### RF-01 — Organizações

O sistema deverá permitir cadastrar organizações clientes.

Cada organização deverá visualizar e administrar somente os dados aos quais seus usuários possuem autorização. Os dados de cada organização deverão permanecer isolados.

### RF-02 — Usuários e autenticação

O sistema deverá permitir autenticação por e-mail e senha, utilizando os recursos nativos de autenticação do Django com um modelo de usuário customizado configurado desde o início.

O acesso deverá respeitar a organização e as permissões do usuário.

### RF-03 — Eventos

O sistema deverá permitir criar, consultar, editar e encerrar eventos.

Campos iniciais:
- Nome.
- Descrição, opcional.
- Local.
- Data e horário de início.
- Data e horário de término.
- Status: planejamento, ativo, encerrado ou cancelado.

Uma organização poderá possuir vários eventos. Um evento poderá reunir várias empresas e equipes.

### RF-04 — Empresas

O sistema deverá permitir cadastrar empresas prestadoras de serviços dentro da organização.

Campos iniciais:
- Razão social ou nome.
- Nome fantasia, quando aplicável.
- CNPJ, quando aplicável.
- Nome do contato responsável, opcional.
- Telefone, opcional.
- E-mail, opcional.
- Status ativo/inativo.

No MVP, o cadastro da empresa será pertencente à organização que o criou. O compartilhamento de uma empresa entre organizações poderá ser avaliado futuramente.

### RF-05 — Profissionais

O sistema deverá permitir cadastrar e manter profissionais.

Campos iniciais:
- Nome completo.
- CPF, opcional conforme a necessidade operacional e a política de privacidade.
- Telefone, opcional.
- E-mail, opcional.
- Observações operacionais, opcionais.
- Status ativo/inativo.

O sistema deverá identificar possíveis duplicidades. CPF, quando coletado, deverá ser protegido e utilizado somente quando necessário.

### RF-06 — Categorias e funções

O sistema deverá permitir cadastrar categorias de equipe e suas funções em um mesmo fluxo de cadastro.

Exemplos:
- Categoria: Segurança; função: Vigilante.
- Categoria: Atendimento médico; função: Socorrista.
- Categoria: Limpeza; função: Auxiliar de limpeza.
- Categoria: Montagem; função: Carregador.

Cada função deverá pertencer a uma única categoria. Uma função com o mesmo nome em outra categoria será um cadastro separado. Categorias e suas funções poderão ser reutilizadas em diferentes eventos da organização.

A categoria e a função são vinculadas ao cadastro do profissional (perfil reutilizável), não à participação no evento. A participação no evento referencia o profissional e herda sua categoria/função.

### RF-07 — Participação do profissional no evento

O sistema deverá permitir associar um profissional a um evento por meio de uma participação (`EventAssignment`).

A participação deverá registrar, no mínimo:
- Organização.
- Evento.
- Profissional.
- Empresa responsável pelo fornecimento, quando aplicável.
- Categoria.
- Função.
- Status da participação.
- Datas/turnos de trabalho, caso façam parte do cadastro operacional adotado.

A empresa é registrada no contexto da participação, pois pode variar de um evento para outro. A categoria e a função são definidas no cadastro do profissional e herdadas pela participação.

### RF-08 — Credenciais e QR Code

O sistema deverá gerar uma credencial individual para cada participação elegível.

A credencial deverá possuir:
- Identificador interno.
- Código público único e não previsível.
- Participação vinculada.
- Status: ativa, cancelada ou substituída.
- Data de emissão.
- Data de cancelamento, quando aplicável.

O QR Code deverá conter apenas um identificador/token seguro, sem CPF, telefone ou outros dados pessoais.

O sistema deverá disponibilizar uma visualização imprimível ou exportável para aplicação na pulseira física. O formato final de impressão será definido em etapa posterior.

### RF-09 — Leitura do QR Code

O operador deverá conseguir abrir a tela operacional em um celular ou tablet e utilizar a câmera para ler o QR Code.

Após a leitura, o sistema deverá:
1. Localizar a credencial.
2. Verificar se ela existe e está ativa.
3. Verificar se pertence ao evento selecionado.
4. Identificar o profissional e os dados relevantes da participação.
5. Consultar a última movimentação válida.
6. Sugerir a próxima operação.
7. Permitir que o operador altere a sugestão.
8. Solicitar confirmação explícita.
9. Validar novamente a situação no servidor antes de gravar.

A leitura não deverá, por si só, registrar uma movimentação.

### RF-10 — Sugestão automática de entrada e saída

O sistema deverá sugerir a operação com base na última movimentação válida da participação no evento, mesmo após cancelamento/substituição da credencial anterior:

- Sem entrada anterior válida: sugerir **ENTRADA**.
- Última movimentação válida igual a **ENTRADA**: sugerir **SAÍDA**.
- Última movimentação válida igual a **SAÍDA**: sugerir **ENTRADA**.

No fluxo normal, o operador deverá confirmar a operação sugerida sem poder trocá-la. A sugestão será recalculada no servidor no momento da gravação. Se o estado tiver mudado desde a leitura, o sistema deverá bloquear a confirmação e pedir nova leitura/consulta.

O servidor deverá validar a sugestão e o estado mais recente antes de gravar. Valores enviados pelo cliente que não correspondam à sugestão atual deverão ser rejeitados; o operador deverá consultar novamente a credencial.

Correções excepcionais de histórico deverão seguir um fluxo separado, autorizado e auditável, com justificativa.

### RF-11 — Registro de entrada e saída

O sistema deverá registrar cada movimentação como um registro histórico independente.

Cada movimentação deverá armazenar:
- Credencial e participação relacionadas.
- Evento.
- Tipo: `ENTRY` ou `EXIT`.
- Data e hora do evento.
- Data e hora em que o sistema registrou a informação, quando necessário.
- Usuário responsável.
- Dispositivo ou identificação operacional, se disponível.
- Informação sobre eventual correção ou invalidação.

O sistema deverá apresentar confirmação visual somente depois que o servidor confirmar a gravação.

### RF-12 — Pesquisa manual

Se a câmera não conseguir ler o QR Code, o operador poderá pesquisar o profissional por nome ou identificador permitido.

A pesquisa manual deverá aplicar as mesmas validações de credencial, evento e sequência de movimentações usadas na leitura do QR Code.

### RF-13 — Profissionais presentes

O sistema deverá apresentar a lista de profissionais cuja última movimentação válida no evento seja uma entrada sem saída posterior.

A lista deverá permitir filtros básicos, como empresa, categoria e função.

### RF-14 — Dashboard operacional

O dashboard do evento deverá apresentar, no mínimo:
- Total de profissionais credenciados.
- Total de profissionais que já registraram entrada.
- Quantidade atualmente presente.
- Quantidade que ainda não entrou.
- Quantidade que já saiu e não está presente.
- Duração total estimada de permanência da equipe, somando intervalos válidos e contando até agora as entradas ainda abertas; não representa controle de jornada.
- Tabela com todas as permanências válidas, uma linha por entrada, contendo data/hora de entrada e data/hora de saída; saídas ainda não registradas aparecem como “Em andamento”.
- Movimentações recentes.

Os indicadores deverão deixar claro o que cada contagem representa. Uma pessoa que entrou, saiu e voltou deverá ser contada como presente apenas quando sua última movimentação válida for entrada.

### RF-15 — Histórico de movimentações

O sistema deverá permitir consultar as movimentações por evento, profissional, empresa, categoria, função e período.

O histórico e os relatórios ficam restritos a administradores e supervisores com associação ativa. Operadores mantêm acesso somente à operação dos eventos autorizados. Gestores podem consultar eventos de qualquer status; somente eventos ativos aceitam novas movimentações.

O histórico não deverá ser apagado ou sobrescrito por uma simples alteração de status.

### RF-16 — Relatórios e exportação

O sistema deverá permitir consultar e exportar relatórios básicos por:
- Evento.
- Empresa.
- Categoria.
- Função.
- Profissional.
- Período.
- Situação de presença.

A exportação poderá começar por CSV e evoluir conforme a necessidade dos usuários.
O CSV deverá conter apenas os dados operacionais necessários e não incluir CPF, telefone, e-mail, observações pessoais, token ou conteúdo do QR Code.
Relatórios e exportações ficam restritos a administradores e supervisores com associação ativa. Operadores mantêm acesso somente à operação dos eventos autorizados. O CSV conterá campos operacionais mínimos e não incluirá CPF, telefone, e-mail, observações pessoais, token ou QR Code.

### RF-17 — Importação de planilhas

O sistema deverá permitir importar profissionais e participações por Excel ou CSV, conforme um modelo de planilha documentado.

A importação deverá:
- Validar campos obrigatórios.
- Identificar possíveis duplicidades.
- Apresentar uma prévia dos registros.
- Exibir erros por linha/campo.
- Permitir cancelar antes de confirmar.
- Apresentar um resumo após a conclusão.

A importação não deverá criar credenciais silenciosamente sem que o usuário compreenda e confirme o resultado.

### RF-18 — Auditoria e correções

O sistema deverá registrar ações administrativas relevantes, especialmente:
- Cancelamento ou substituição de credencial.
- Alteração de dados de participação.
- Correção ou invalidação de movimentação.
- Alteração de permissões de usuário.

Correções deverão exigir justificativa, usuário responsável, data/hora e referência ao registro afetado. O registro original deverá permanecer rastreável.

## 8. Regras de negócio

### 8.1 Organização e evento

- RN-01: Uma organização poderá possuir vários eventos.
- RN-02: Os dados de uma organização não poderão ser acessados por usuários de outra organização sem autorização explícita.
- RN-03: Um evento pertence a uma única organização no MVP.
- RN-04: Um profissional poderá participar de vários eventos.
- RN-05: A empresa, categoria e função deverão ser definidas no contexto da participação no evento.

### 8.2 Participação e credencial

- RN-06: Uma participação representa o vínculo de um profissional com um evento.
- RN-07: Uma participação poderá possuir no máximo uma credencial ativa por vez.
- RN-08: Uma credencial deverá estar vinculada a uma participação específica.
- RN-09: Uma credencial cancelada ou substituída não poderá registrar novas movimentações.
- RN-10: Uma credencial deverá pertencer ao evento selecionado pelo operador.
- RN-11: O código contido no QR Code não deverá expor dados pessoais e deverá ser difícil de adivinhar.

### 8.3 Movimentações

- RN-12: Uma saída normal exige uma entrada válida anterior ainda não encerrada por saída.
- RN-13: Não poderão existir duas entradas consecutivas válidas sem uma saída intermediária.
- RN-14: Não poderão existir duas saídas consecutivas válidas sem uma nova entrada intermediária.
- RN-15: Sem entrada anterior válida, o sistema sugere ENTRADA.
- RN-16: Após uma entrada válida, o sistema sugere SAÍDA.
- RN-17: Após uma saída válida, o sistema sugere ENTRADA.
- RN-18: No fluxo normal, o operador não poderá trocar a operação sugerida; se o estado mudar antes da confirmação, o servidor deverá bloquear a tentativa e solicitar nova consulta.
- RN-19: A operação escolhida deverá ser validada novamente no servidor antes da gravação.
- RN-20: Uma tentativa incompatível com o estado atual deverá ser bloqueada no fluxo normal e apresentar uma explicação.
- RN-21: Cada movimentação deverá armazenar o usuário responsável e data/hora.
- RN-22: O sistema deverá impedir inconsistências quando dois operadores tentarem registrar movimentações simultaneamente para a mesma credencial.
- RN-23: Eventos que atravessam a meia-noite deverão manter data e hora completas; não se deve armazenar apenas o horário.
- RN-24: Uma entrada sem saída posterior deverá ser considerada uma permanência em aberto.
- RN-25: A situação presente/ausente deverá ser derivada da última movimentação válida, não de um campo de status atualizado isoladamente.

### 8.4 Correções

- RN-26: Movimentações não deverão ser apagadas fisicamente por uma correção operacional comum.
- RN-27: Uma correção deverá manter referência ao registro original, justificativa, usuário e data/hora.
- RN-28: A invalidação de uma movimentação deverá provocar o recálculo da situação da participação no evento com base no histórico válido, inclusive após substituição de credencial.
- RN-29: O fluxo de correção deverá possuir permissão própria, separada da operação normal de entrada e saída, e exigir associação ativa de administrador/supervisor.
- RN-30: A substituição ou reemissão de credencial não reinicia a sequência de movimentações da participação no evento.
- RN-31: Somente a movimentação válida mais recente da participação pode ser invalidada; para corrigir uma anterior, as posteriores deverão ser invalidadas primeiro, em ordem inversa, sem cascata automática.
- RN-31: Somente a movimentação válida mais recente da participação pode ser invalidada; para corrigir uma anterior, as posteriores deverão ser invalidadas primeiro, em ordem inversa, sem cascata automática.

## 9. Fluxos operacionais

### 9.1 Credenciamento

1. Administrador acessa a organização.
2. Seleciona ou cadastra um evento.
3. Cadastra ou importa profissionais.
4. Associa profissionais ao evento, informando empresa, categoria e função.
5. Confere os dados da participação.
6. Confirma a emissão das credenciais.
7. O sistema gera códigos e QR Codes individuais.
8. O usuário imprime ou exporta as credenciais para aplicação nas pulseiras.

### 9.2 Entrada e saída — sugestão automática com confirmação

1. Operador autentica-se no CrewPass.
2. Seleciona o evento em que está autorizado a operar.
3. Abre a tela de controle de acesso.
4. Lê o QR Code da pulseira.
5. O servidor valida a credencial e o evento.
6. O sistema consulta a última movimentação válida.
7. O sistema sugere ENTRADA ou SAÍDA.
8. O sistema apresenta a sugestão sem permitir troca no fluxo normal.
9. O operador confirma explicitamente a operação sugerida.
10. O servidor valida novamente o estado atual e registra a movimentação.
11. Se o estado mudou, o sistema bloqueia a confirmação e solicita nova consulta; caso contrário, apresenta o resultado.

### 9.3 Pesquisa manual

1. Operador abre a pesquisa manual.
2. Informa nome ou identificador permitido.
3. Seleciona o profissional/participação correta.
4. O sistema apresenta a credencial e a operação sugerida.
5. O operador confirma.
6. O servidor valida e registra a movimentação.

### 9.4 Correção de movimentação

1. Usuário autorizado localiza a movimentação.
2. Informa a justificativa.
3. O sistema registra a correção/invalidação sem apagar o histórico original.
4. O sistema registra quem realizou a ação e quando.
5. Somente a movimentação válida mais recente pode ser invalidada. Para chegar a uma anterior, o supervisor corrige primeiro cada movimentação posterior.
6. A situação atual da participação é recalculada a partir das movimentações que permanecem válidas.

## 10. UX e telas do MVP

### 10.1 Login

- Login por e-mail e senha.
- Mensagens de erro claras.
- Recuperação de senha.

### 10.2 Dashboard

- Resumo dos eventos da organização.
- Eventos ativos e próximos.
- Indicadores de operação, quando aplicável.

### 10.3 Eventos

- Listagem com pesquisa e filtros.
- Cadastro e edição.
- Detalhes e situação do evento.

### 10.4 Empresas

- Listagem, cadastro, edição e ativação/inativação.
- Dados de contato básicos.

### 10.5 Profissionais

- Listagem, pesquisa, cadastro e edição.
- Identificação de possíveis duplicidades.
- Histórico de participações, conforme permissão.

### 10.6 Credenciamento

- Seleção do evento.
- Associação de profissionais.
- Importação de planilha.
- Revisão e confirmação.
- Geração e visualização de credenciais.

### 10.7 Operação de acesso

Esta é uma das telas prioritárias do produto e deverá ser otimizada para celular e tablet.

Elementos:
- Evento selecionado, sempre visível.
- Acesso à câmera/leitura do QR Code.
- Pesquisa manual.
- Resultado da identificação do profissional.
- Empresa, categoria e função.
- Operação sugerida em destaque.
- Controles claros para manter ou alterar a operação.
- Botão explícito de confirmação.
- Resultado da gravação.
- Mensagens de erro e orientação.

A tela deverá evitar registros automáticos sem confirmação.

### 10.8 Presentes no evento

- Lista dos profissionais atualmente presentes.
- Filtros por empresa, categoria e função.
- Horário da última entrada.

### 10.9 Histórico

- Lista de movimentações.
- Filtros por evento, profissional, empresa e período.
- Detalhe da movimentação.
- Acesso às correções conforme permissão.

### 10.10 Relatórios

- Resumos por evento.
- Quebra por empresa, categoria e função.
- Exportação dos dados filtrados.

## 11. Modelo de dados lógico inicial

O modelo abaixo é uma referência para a implementação. Tipos e restrições exatos serão definidos nos models Django e migrations.

### 11.1 `Organization`

Representa a organização cliente.

Campos sugeridos:
- `id`
- `name`
- `legal_name` (opcional)
- `document` (opcional)
- `status`
- `created_at`
- `updated_at`

### 11.2 `User`

Modelo de usuário customizado do Django.

Campos sugeridos:
- `id`
- `email` (único para login, conforme estratégia global escolhida)
- `name`
- `is_active`
- `is_staff`
- `is_superuser`
- `created_at`
- `updated_at`

A relação do usuário com organizações e permissões deverá ser explícita, por exemplo por meio de um vínculo de associação de usuário à organização. Caso o produto permita que um usuário participe de mais de uma organização, esse vínculo evita prender o usuário a uma única organização.

### 11.3 `OrganizationMembership`

Vínculo de usuário com organização.

Campos sugeridos:
- `id`
- `organization`
- `user`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Restrição: combinação de `organization` e `user` única.

### 11.4 `Event`

Campos sugeridos:
- `id`
- `organization`
- `name`
- `description`
- `location`
- `starts_at`
- `ends_at`
- `status`
- `created_at`
- `updated_at`

### 11.5 `Company`

Campos sugeridos:
- `id`
- `organization`
- `legal_name`
- `trade_name`
- `document`
- `contact_name`
- `phone`
- `email`
- `is_active`
- `created_at`
- `updated_at`

### 11.6 `StaffMember`

Cadastro reutilizável do profissional dentro da organização.

Campos sugeridos:
- `id`
- `organization`
- `full_name`
- `document` (opcional)
- `phone` (opcional)
- `email` (opcional)
- `company` (opcional)
- `team_category` (opcional)
- `staff_role` (opcional)
- `notes` (opcional)
- `is_active`
- `created_at`
- `updated_at`

A regra de unicidade de documento deverá considerar a organização e os casos em que o documento não foi informado. A categoria e a função são vinculadas ao profissional, não à participação no evento.

### 11.7 `TeamCategory`

Campos sugeridos:
- `id`
- `organization`
- `name`
- `is_active`
- `created_at`
- `updated_at`

O cadastro da categoria deverá permitir gerenciar suas funções vinculadas.

### 11.8 `StaffRole`

Campos sugeridos:
- `id`
- `organization`
- `team_category`
- `name`
- `is_active`
- `created_at`
- `updated_at`

Uma função pertence a uma única categoria; a combinação organização, categoria e nome deverá ser única.

### 11.9 `EventAssignment`

Representa a participação do profissional no evento.

Campos sugeridos:
- `id`
- `organization`
- `event`
- `staff_member`
- `company` (opcional, conforme operação)
- `status`
- `notes` (opcional)
- `created_at`
- `updated_at`

A participação deverá referenciar entidades pertencentes à mesma organização e o evento correspondente. Essa consistência deverá ser validada na aplicação.

### 11.10 `Credential`

Campos sugeridos:
- `id`
- `event_assignment`
- `code` (único, aleatório e não previsível)
- `status`
- `issued_at`
- `cancelled_at` (opcional)
- `created_at`
- `updated_at`

Restrição: no máximo uma credencial ativa por participação.

### 11.11 `Movement`

Campos sugeridos:
- `id`
- `event`
- `event_assignment`
- `credential`
- `movement_type` (`ENTRY` ou `EXIT`)
- `occurred_at`
- `recorded_at`
- `recorded_by`
- `request_id` (chave única de idempotência da confirmação)
- `device_label` (opcional)
- `status` ou referência de invalidação

`occurred_at` representa o momento da movimentação informado pelo sistema no fluxo online. `recorded_at` representa o momento em que o registro foi persistido. Se o MVP for exclusivamente online, ambos poderão ser preenchidos próximos um do outro, mas a distinção ajuda na rastreabilidade.

### 11.12 `AuditLog`

Campos sugeridos:
- `id`
- `organization`
- `user`
- `action`
- `entity_type`
- `entity_id`
- `reason` (quando aplicável)
- `metadata` (dados estruturados mínimos)
- `created_at`
- `updated_at`

O log deverá evitar armazenar dados pessoais desnecessários.

### 11.14 `MovementCorrection`

Registra a invalidação auditável de uma movimentação sem editar ou apagar o registro original.

Campos sugeridos:
- `id`
- `movement` (única movimentação original invalidada)
- `reason`
- `corrected_by`
- `corrected_at`

No Sprint 5, a correção aplica-se somente à movimentação válida mais recente da participação.

### 11.13 `EventOperatorGrant`

Autoriza um vínculo ativo de operador da organização a operar um evento específico. Administradores e supervisores ativos mantêm acesso de gestão aos eventos da organização.

Campos sugeridos:
- `id`
- `event`
- `membership` (vínculo de operador na organização do evento)
- `is_active`
- `granted_by` e `granted_at`
- `revoked_by` e `revoked_at` (quando revogada)

Uma revogação deverá preservar o histórico. Uma associação inativa ou removida não concede acesso operacional.

### 11.14 `MovementCorrection`

Registra a invalidação auditável de uma movimentação sem editar ou apagar o registro original.

Campos sugeridos:
- `id`
- `movement` (única movimentação original invalidada)
- `reason`
- `corrected_by`
- `corrected_at`

No Sprint 5, a correção aplica-se somente à movimentação válida mais recente da participação.

## 12. Arquitetura técnica

### 12.1 Stack proposta

- Linguagem: Python.
- Backend: Django 6.0.
- Interface: Django Template Language.
- Estilização: Tailwind CSS.
- Interações de interface: JavaScript.
- Banco de desenvolvimento inicial: SQLite.
- Banco recomendado para produção: PostgreSQL.
- Autenticação: Django com modelo de usuário customizado e login por e-mail.
- Geração de QR Code: biblioteca Python `qrcode`.
- Leitura de QR Code: `@zxing/browser`, empacotado localmente via esbuild e usado somente após ação explícita para abrir a câmera.
- Versionamento: Git.

A escolha da biblioteca de leitura deverá ser validada com testes nos navegadores e dispositivos que serão utilizados nos eventos.

### 12.2 Organização Django sugerida

- `accounts`: usuário, autenticação, associação e permissões.
- `organizations`: organizações e configurações.
- `events`: eventos.
- `staff`: empresas, profissionais, categorias, funções e participações.
- `credentials`: emissão, consulta, cancelamento e QR Code.
- `access_control`: autorização de operadores por evento, movimentações e validações; correções auditáveis evoluem conforme o escopo definido.
- `reports`: dashboards, consultas e exportações.

A divisão final poderá ser simplificada se algum módulo ficar pequeno demais. O objetivo é manter responsabilidades claras, não multiplicar apps sem necessidade.

### 12.3 Diretrizes de implementação

- Arquitetura monolítica modular.
- Código simples, legível e aderente à PEP 8.
- Preferir aspas simples em Python quando possível.
- Regras de negócio importantes no backend, não apenas no JavaScript.
- Validar organização e permissões em todas as consultas e operações.
- Utilizar transações e proteção contra concorrência ao registrar movimentações.
- Não confirmar sucesso na interface antes da persistência no servidor.
- Manter `created_at` e `updated_at` nos modelos, quando aplicável.
- Não introduzir Docker, microsserviços, filas ou infraestrutura complexa sem necessidade comprovada.
- Preparar configuração por ambiente e segredos fora do código-fonte.

### 12.4 Banco de dados

SQLite será utilizado no desenvolvimento inicial, conforme a diretriz do MVP. Para uma implantação real com vários operadores simultâneos, PostgreSQL é a opção recomendada.

A decisão de produção deverá ser tomada antes da implantação em evento real, considerando volume, concorrência, disponibilidade e infraestrutura.

## 13. Requisitos não funcionais

### Segurança e privacidade

- Isolamento dos dados por organização.
- Controle de acesso por perfil e vínculo com organização.
- Proteção de dados pessoais conforme a LGPD.
- Coleta mínima de dados pessoais.
- QR Code sem dados pessoais em texto aberto.
- HTTPS obrigatório em produção.
- Registro de ações administrativas relevantes.
- Proteção contra acesso direto a registros de outra organização por alteração de URL ou parâmetros.

### Usabilidade

- Interface responsiva para desktop, tablet e celular.
- Tela operacional com botões grandes e poucos passos.
- Feedback visual imediato.
- Mensagens claras em português do Brasil.
- Padrão visual consistente entre as telas.

### Confiabilidade

- Evitar movimentações duplicadas.
- Preservar histórico e auditoria.
- Tratar falhas de comunicação sem apresentar sucesso indevido.
- Validar novamente no servidor antes de persistir uma movimentação.
- Registrar datas e horários completos.

### Desempenho

- Consultas filtradas por organização e evento.
- Índices para campos utilizados em pesquisas e relacionamentos frequentes.
- Tela de operação otimizada para reduzir o tempo entre leitura e confirmação.

### Limite de uso

O CrewPass registra movimentações de acesso ao evento. Os dados não deverão ser apresentados como controle legal de jornada, folha de pagamento ou ponto trabalhista.

## 14. Diretrizes de UX e identidade visual

- Interface moderna, profissional e responsiva.
- Tema escuro como padrão inicial.
- Paleta harmoniosa com tons de azul e cores de destaque.
- Cards para indicadores.
- Tabelas organizadas e filtros objetivos.
- Componentes reutilizáveis e consistentes.
- Interface operacional priorizada para uso em celular e tablet.
- Todos os textos da interface em pt-BR.
- Nomes técnicos, apps, classes e variáveis em inglês.

**Tagline provisória:** “Sua equipe identificada. Seu evento sob controle.”

## 15. Plano de desenvolvimento por sprints

A ordem abaixo é uma proposta inicial e poderá ser ajustada conforme a validação técnica.

### Sprint 1 — Fundação

- [x] Criar projeto Django.
- [x] Configurar ambiente e dependências.
- [x] Configurar Tailwind CSS.
- [x] Criar modelo de usuário customizado com login por e-mail.
- [x] Implementar organizações e associação de usuários.
- [x] Criar layout base, navegação e identidade visual.
- [x] Configurar SQLite para desenvolvimento.
- [x] Criar migrations iniciais.

**Critério de conclusão:** usuário consegue autenticar e acessar uma organização, com isolamento básico de dados.

### Sprint 2 — Cadastros e eventos

- [x] Cadastro e edição de eventos.
- [x] Cadastro e edição de empresas.
- [x] Cadastro e edição de profissionais.
- [x] Cadastro de categorias e funções.
- [x] Associação de profissionais a eventos.
- [x] Listagens, pesquisas e filtros básicos.

**Critério de conclusão:** organização consegue preparar um evento e cadastrar suas equipes.

### Sprint 3 — Credenciamento

- [x] Criar modelo de credencial.
- [x] Gerar identificadores únicos e não previsíveis.
- [x] Gerar QR Codes.
- [x] Criar visualização imprimível.
- [x] Ativar, cancelar e substituir credenciais.
- [x] Validar vínculo da credencial com evento e participação.

**Critério de conclusão:** cada profissional participante pode receber uma credencial identificável por QR Code.

### Sprint 4 — Operação de acesso

- [x] Criar tela operacional responsiva.
- [x] Implementar leitura do QR Code pela câmera.
- [x] Implementar pesquisa manual.
- [x] Implementar sugestão automática de entrada/saída.
- [x] Exibir a sugestão sem permitir troca no fluxo normal; bloquear confirmação desatualizada.
- [x] Implementar confirmação explícita.
- [x] Validar credencial, evento e sequência no backend.
- [x] Implementar proteção contra registros simultâneos inconsistentes.
- [x] Implementar autorização explícita de operadores por evento.
- [x] Exibir mensagens de sucesso e erro.
- [x] Executar suíte e checks no Python 3.12/Django 6; validar no código confirmações desatualizadas e idempotência.

**Critério de conclusão:** operadores conseguem registrar entradas e saídas de forma confiável no ambiente de teste.

**Status:** implementação e suíte/checks locais concluídos. Teste de capacidade com dispositivos simultâneos permanece no Sprint 6.

### Sprint 5 — Dashboard, histórico e relatórios

- [x] Dashboard do evento.
- [x] Lista de profissionais presentes.
- [x] Histórico de movimentações.
- [x] Filtros por empresa, categoria, função e período.
- [x] Exportação CSV.
- [x] Correções autorizadas e auditáveis.
- [x] Card de permanência total estimada, com movimentos invalidados excluídos e entradas abertas contadas até o momento da consulta; não é apuração de jornada.
- [x] Tabela de permanências por profissional, com data/hora de entrada e saída na mesma linha e entradas em aberto identificadas.

**Critério de conclusão:** supervisores conseguem acompanhar a operação e consultar o histórico.

**Status:** concluído. Correções invalidam somente a movimentação válida mais recente; registros originais permanecem preservados.

### Sprint 6 — Jornada intuitiva e operação por turnos (replanejado)

**Objetivo:** tornar a preparação e o acompanhamento de eventos mais guiados, usando o material do cliente como referência de requisitos, sem importar diretamente suas abas, fórmulas ou dados pessoais.

- [x] Guiar a preparação do evento em etapas: equipe, credenciais e operação, indicando o próximo passo e o que falta.
- [x] Permitir cadastrar um novo profissional e associá-lo ao evento na mesma tela, mantendo `StaffMember` separado de `EventAssignment`.
- [x] Cadastrar categorias e suas funções em um único fluxo; filtrar as funções pela categoria na participação.
- [ ] Simplificar a operação para identificar, conferir a ação sugerida e confirmar, com pesquisa manual como alternativa clara à câmera.
- [ ] Revisar o modelo completo de presença operacional: separar turno previsto de movimentações reais e representar entrada, saída, duração e checkout pendente.
- [x] Associar o turno à participação do profissional no evento, com horário de início e término (turnos noturnos podem atravessar a meia-noite); não bloqueiam movimentações reais.
- [ ] Validar com o cliente se o número físico da pulseira precisa ser armazenado; somente então definir campo opcional, unicidade e comportamento na substituição da credencial.
- [x] Apresentar permanências em aberto como “Em andamento”, sem registrar saída automática; recalcular períodos após correções mantendo a auditoria.
- [ ] Filtrar o acompanhamento por data e turno.
- [x] Revisar a linguagem da ação de invalidação para indicar que é opcional e só deve ser usada se o registro estiver incorreto.
- [ ] Testar fluxos de turno noturno, múltiplos dias, ausência de checkout, substituição/dobra e correções.
- [ ] Validar em celulares/tablets reais, com múltiplos operadores, permissões e isolamento entre organizações.

**Critério de conclusão:** um gestor consegue preparar um evento sem depender de orientação externa; a equipe consegue operar e consultar permanências por data/turno, mantendo histórico, isolamento e correções auditáveis. A duração é calculada a partir das movimentações reais e continua sendo permanência operacional estimada — não inclui regras de ponto, intervalos legais, horas extras ou folha de pagamento.

**Status:** em andamento. A página do evento guia a preparação; um profissional novo pode ser cadastrado e associado ao evento na mesma tela, mantendo os modelos separados; categorias e funções são gerenciadas juntas, com atalho para reabrir uma categoria existente e função filtrada pela categoria na participação; participações permitem cadastrar um turno por data; e a ação de invalidação ficou mais clara. Fluxo de operação e filtros por data/turno continuam pendentes. A inclusão do número físico da pulseira aguarda validação do cliente. O arquivo `MaterialApoio/EVENTO DELL.xlsx` será usado como referência, não como formato de importação direta.

### Sprint 7 — Importação e preparação para piloto (replanejado)

- [ ] Importação genérica Excel/CSV a partir de formato documentado.
- [ ] Prévia, validação de registros e identificação de duplicidades.
- [ ] Testes dos fluxos críticos e preparação do piloto.
- [ ] Revisão final de permissões, isolamento entre organizações e operação com múltiplos operadores.
- [ ] Preparação de ambiente de produção, banco adequado, backups e monitoramento.

**Critério de conclusão:** MVP validado em ambiente controlado e pronto para um piloto operacional.

## 16. Indicadores de sucesso

- Tempo médio para registrar entrada ou saída.
- Percentual de movimentações feitas por QR Code.
- Quantidade de tentativas inválidas ou duplicadas.
- Percentual de profissionais com credenciamento completo.
- Tempo para localizar um profissional.
- Tempo para gerar um relatório do evento.
- Quantidade de eventos operados pela plataforma.

Os indicadores deverão ser medidos no piloto para estabelecer metas realistas.

## 17. Riscos e mitigações

| Risco | Mitigação inicial |
|---|---|
| Internet indisponível | MVP online; avaliar offline após validar a necessidade operacional |
| QR Code ilegível | Pesquisa manual como alternativa |
| Pulseira compartilhada | Exibir dados básicos para conferência visual do operador |
| Registro duplicado | Validação no backend e proteção contra concorrência |
| Erro operacional | Confirmação explícita e histórico auditável |
| Acesso indevido a dados | Isolamento por organização e controle de permissões |
| Grande volume de acessos | Testes com múltiplos operadores e banco PostgreSQL em produção |
| Dados incorretos importados | Prévia, validação e confirmação da importação |

## 18. Decisões já tomadas

- [x] Nome do produto: CrewPass.
- [x] Público-alvo: equipes operacionais de eventos, não o público geral.
- [x] Credencial física por pulseira com QR Code.
- [x] Controle inicial de entrada e saída do evento, sem áreas específicas.
- [x] Operação por aplicação web em celular ou tablet.
- [x] Sugestão automática da próxima movimentação; sem troca no fluxo normal do Sprint 4.
- [x] Confirmação explícita antes de registrar movimentação.
- [x] Histórico de movimentações preservado.
- [x] MVP simples, com possibilidade de ajustar regras.
- [x] Arquitetura proposta: Django monolítico modular.
- [x] Profissional separado da participação no evento e da credencial.
- [x] Sprint 4 online-only; operação permitida somente em eventos ativos.
- [x] Operadores precisam de associação ativa à organização e autorização explícita por evento; administradores/supervisores mantêm acesso de gestão.
- [x] Busca manual no Sprint 4 por nome ou CPF completo; CPF não aparece em resultados nem na URL.
- [x] No fluxo normal, a ação sugerida não pode ser trocada; correções excepcionais permanecem em fluxo autorizado e auditável.
- [x] Turnos/escalas ficam fora do Sprint 4.
- [x] Relatórios e exportações são restritos a administradores/supervisores ativos; operadores continuam limitados à operação autorizada.
- [x] Relatórios permitem consulta histórica em eventos de qualquer status, mas novas movimentações só são aceitas em eventos ativos.
- [x] CSV operacional não inclui CPF, contatos, observações pessoais, token ou conteúdo do QR Code.
- [x] Correção invalida somente a última movimentação válida; movimentos posteriores devem ser tratados em ordem inversa, sem cascata automática.
- [x] O CrewPass acompanha presença operacional no evento; não calcula jornada trabalhista, horas extras, intervalos legais ou folha de pagamento.
- [x] Cada função pertence a uma categoria; o mesmo nome em outra categoria representa outro cadastro.

## 19. Decisões pendentes

As decisões abaixo não devem ser tratadas como já aprovadas:

1. **Operação offline:** não faz parte do Sprint 4, que será online-only; avaliar modo offline somente após validar conectividade em eventos reais.
2. **Impressão da pulseira:** definir se o QR Code será acompanhado de nome, empresa e função e qual será o formato de impressão.
3. **Turnos e escalas:** confirmado que o turno pertence à participação do profissional no evento, possui horário de início e término, pode atravessar a meia-noite e não bloqueia movimentações reais. Permanece pendente definir como os relatórios agrupam as movimentações reais em relação ao turno previsto.
4. **Capacidade com múltiplos operadores:** não há meta quantitativa definida para o Sprint 4; validar capacidade e concorrência antes do piloto/produção.
5. **Modelo comercial:** definir cobrança por evento, por organização ou assinatura.
6. **Dados pessoais:** definir se CPF será obrigatório, opcional ou não coletado, conforme a necessidade operacional.
7. **Produção:** definir hospedagem, banco PostgreSQL, backups e monitoramento antes do piloto real.
8. **Número físico da pulseira:** validar com o cliente se o identificador físico deve ser armazenado; se confirmado, definir escopo de unicidade e comportamento ao substituir uma credencial.

## 20. Critérios gerais de aceite do MVP

O MVP será considerado funcional quando for possível:

1. Criar uma organização e seus usuários.
2. Cadastrar um evento.
3. Cadastrar empresas e profissionais.
4. Associar profissionais a um evento com empresa, categoria e função.
5. Emitir credenciais individuais com QR Code.
6. Ler uma credencial usando a câmera de um celular ou tablet.
7. Sugerir a próxima movimentação com base no histórico.
8. Confirmar a operação sugerida e bloquear uma confirmação desatualizada ou incompatível.
9. Bloquear credenciais inválidas, canceladas ou de outro evento.
10. Registrar entradas e saídas com usuário e data/hora.
11. Consultar quem está presente no evento.
12. Consultar o histórico de movimentações.
13. Visualizar indicadores básicos.
14. Garantir que uma organização não acesse dados de outra.
15. Tratar tentativas simultâneas de movimentação sem gerar sequência inconsistente.

---

## Resultado esperado

O CrewPass deverá permitir que uma organização prepare um evento, cadastre ou importe seus profissionais, emita pulseiras com QR Code e controle digitalmente as entradas e saídas das equipes operacionais. Supervisores poderão acompanhar quem está presente, consultar o histórico e obter relatórios básicos.

**Diretriz final:** entregar primeiro um fluxo operacional confiável e simples. Evoluções como modo offline, controle por áreas, integrações e recursos avançados deverão ser priorizadas somente após validação do MVP em eventos reais.
