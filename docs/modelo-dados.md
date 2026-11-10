# Modelo de Dados — CrewPass

## Entidades e Relacionamentos

```
Organization ──┬── OrganizationMembership ── User
               ├── Event ──┬── EventAssignment ──┬── StaffMember ──┬── Company
               │           │                    │                  ├── TeamCategory
               │           │                    │                  └── StaffRole ── TeamCategory
               │           │                    ├── Credential ──┬── CredentialAuditLog
               │           │                    │               └── (replaced_by) Credential
               │           │                    ├── EventAssignmentShift ── Shift
               │           │                    └── Movement ──┬── MovementCorrection
               │           │                                 └── Credential
               │           └── EventOperatorGrant ── OrganizationMembership
               ├── Company
               ├── StaffMember
               ├── TeamCategory
               ├── StaffRole ── TeamCategory
               └── Shift
```

## Tabelas Principais

| Tabela | Descrição | Chave |
|--------|-----------|-------|
| `Organization` | Organização cliente (tenant) | PK: id |
| `User` | Usuário customizado | PK: id, unique: email |
| `OrganizationMembership` | Vínculo usuário-organização | PK: id, unique: (organization, user) |
| `Event` | Evento | PK: id, FK: organization |
| `Company` | Empresa prestadora | PK: id, FK: organization |
| `StaffMember` | Profissional reutilizável | PK: id, FK: organization, company, team_category, staff_role |
| `TeamCategory` | Categoria de equipe | PK: id, FK: organization |
| `StaffRole` | Função | PK: id, FK: organization, team_category |
| `Shift` | Turno reutilizável | PK: id, FK: organization |
| `EventAssignment` | Participação profissional-evento | PK: id, FK: organization, event, staff_member, company |
| `Credential` | Credencial com QR Code | PK: id, FK: event_assignment, replaced_by (self) |
| `CredentialAuditLog` | Auditoria de credencial | PK: id, FK: credential, actor, replacement |
| `EventOperatorGrant` | Autorização de operador | PK: id, FK: event, membership |
| `Movement` | Movimentação de acesso | PK: id, FK: event, event_assignment, credential, recorded_by |
| `MovementCorrection` | Invalidação de movimentação | PK: id, FK: movement, corrected_by |
| `EventAssignmentShift` | Turno vinculado à participação | PK: id, FK: event_assignment, shift |

## Relacionamentos Chave

- **Organization 1:N** Event, Company, StaffMember, TeamCategory, StaffRole, Shift, EventAssignment
- **Event 1:N** EventAssignment, EventOperatorGrant, Movement
- **StaffMember 1:N** EventAssignment (uma pessoa pode participar de vários eventos)
- **EventAssignment 1:0..1** Credential (máximo uma ativa)
- **EventAssignment 1:N** Movement (histórico de entradas/saídas)
- **Credential 1:N** CredentialAuditLog (auditoria de emissão/cancelamento/substituição)
- **EventAssignment 1:0..1** EventAssignmentShift (um turno por participação)
- **Shift 1:N** EventAssignmentShift (turno reutilizável)

## Isolamento por Organização

Todas as entidades possuem `organization_id` (exceto Credential e Movement, que herdam via EventAssignment/Event). Todas as consultas e operações são filtradas por organização.