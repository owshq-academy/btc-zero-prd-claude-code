# Resumos das Aulas - Bootcamp AI Data Engineering

> Resumos detalhados gerados pelo agente meeting-analyst usando o framework de 10 seções

---

## Índice das Aulas

| Aula | Tema Principal | Tamanho | Confiança | Arquivo |
|------|----------------|---------|-----------|---------|
| **Aula 01** | Paradigmas de Desenvolvimento com IA | 29KB | 0.92 (HIGH) | [aula-01-summary.md](aula-01-summary.md) |
| **Aula 02** | Vibe Coding → Spec-Driven Development | 40KB | 0.92 (HIGH) | [aula-02-summary.md](aula-02-summary.md) |
| **Aula 03** | AI-Native Engineer: Orquestração + Observabilidade | 30KB | 0.92 (HIGH) | [aula-03-summary.md](aula-03-summary.md) |

---

## Visão Geral do Bootcamp

### Aula 01 - Fundamentos e Mudança de Paradigma

**Conceitos-Chave:**

- Transição: 80% código/20% negócio → 80% negócio/20% código
- 3 Paradigmas: Vibe Coding, AI Native, Spec-Driven Development
- Novo papel: AI Data Engineer (pensamento, decisão, validação)
- Projeto real: Pipeline de processamento de notas fiscais Uber Eats

**Ferramentas:**

- Claude Code CLI
- MCP (Model Context Protocol)
- Knowledge Bases
- Sub-Agents

### Aula 02 - Metodologias Estruturadas

**Conceitos-Chave:**

- 3 Níveis de Maturidade: Vibe Coding → Dev Loop → SDD
- "Não escrever código é mais difícil que escrever código"
- Habilidades críticas 2026: Leitura, paciência, atenção
- Ralph Wingham Loop Pattern

**Demonstrações:**

- Protótipo de extração de notas fiscais
- Meeting-analyst + the-planner agents
- Structured outputs com Pydantic

### Aula 03 - Engenheiro AI-Native e Observabilidade

**Conceitos-Chave:**

- IA como frota de agentes (não apenas assistente)
- 3 Pilares: Orquestração + Investigação + Curadoria de Contexto
- Observabilidade com LangFuse
- Production hardening: smoke tests, quality gates

**Demonstrações:**

- Validação end-to-end do pipeline GCP
- Desenvolvimento paralelo de 4 features
- Structured logging (20-30% redução tokens)
- Melhoria de prompts para precisão

---

## Framework de Análise

Cada resumo segue o framework de 10 seções adaptado para contexto educacional:

1. **Conceitos-Chave** - Tópicos principais abordados
2. **Objetivos de Aprendizado** - Metas explícitas e implícitas
3. **Definições** - Termos técnicos e conceitos explicados
4. **Exemplos** - Demonstrações práticas e casos de uso
5. **Exercícios** - Atividades e tarefas para os alunos
6. **Perguntas** - Q&A dos participantes
7. **Detalhes Técnicos** - Arquitetura e implementação
8. **Próximos Passos** - Tópicos das próximas aulas
9. **Métodos de Ensino** - Abordagem pedagógica
10. **Recursos** - Ferramentas, artigos, referências

---

## Impacto Demonstrado

| Métrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| **Tempo de Desenvolvimento** | 3-6 meses | Dias/semanas | 10-20x |
| **Foco do Engenheiro** | 80% código | 80% negócio | Inversão completa |
| **Exemplo Real (Dan Ross)** | 6 meses | 2.5 meses | 2.4x |
| **Exemplo Aluno** | 1 semana | 2 horas | 20x |

---

## Tecnologias Ensinadas

### Ferramentas Core

- **Claude Code CLI** - Interface principal de desenvolvimento
- **MCP Servers** - Context7, Exa, Firecrawl, Ref-Tools
- **Knowledge Bases** - Domínios validados: Pydantic, GCP, Gemini, LangFuse, Terraform, Terragrunt, CrewAI, OpenRouter

### Stack Técnico do Projeto

- **Cloud:** GCP (Cloud Run Functions, GCS, BigQuery, Pub/Sub)
- **LLM:** Gemini 2.0 Flash + OpenRouter (fallback)
- **Observabilidade:** LangFuse
- **Validação:** Pydantic v2
- **IaC:** Terraform + Terragrunt
- **Orquestração:** CrewAI (multi-agent systems)

### Metodologias

- **Vibe Coding** - Desenvolvimento ad-hoc (<30min)
- **Dev Loop** - Iteração estruturada (1-4hrs)
- **Spec-Driven Development (SDD)** - 5 fases com rastreabilidade (dias)

---

## Evolução do Papel do Engenheiro

### Tradicional (2023)

- Escrever código manualmente
- Debugging linha por linha
- Testes manuais
- Documentação depois

### AI-Native (2026)

- **Orquestrar** agentes especializados
- **Investigar** outputs e comportamentos
- **Curar** contexto para IA
- **Validar** qualidade com observabilidade

---

## Como Usar Este Material

### Para Revisão

1. Leia o resumo da aula correspondente
2. Compare com suas anotações
3. Pratique os conceitos nos exercícios mencionados

### Para Estudo

1. Siga a progressão Aula 01 → 02 → 03
2. Implemente os exemplos demonstrados
3. Explore as ferramentas e recursos citados

### Para Referência

1. Use o índice para encontrar tópicos específicos
2. Consulte as definições técnicas
3. Revise a arquitetura e padrões ensinados

---

## Recursos Adicionais

### Artigos Mencionados

- **Andrej Karpathy** - "The Hottest New Programming Language is English"
- **Dario Amodei (Anthropic CEO)** - Building AI teams
- **Martin Fowler** - Impact of AI on software development

### Projetos de Referência

- **UberEats Invoice Pipeline** - Caso real do bootcamp
- **Dan Ross Project** - 2.5 meses, economia de 3.5 meses
- **Invoice Extractor** - Protótipo construído em aula

### Comunidade

- Slack workspace do bootcamp
- GitHub repository com código das aulas
- Sessões de Q&A ao vivo

---

## Próximos Passos

Após estudar estes resumos:

1. **Praticar** - Implemente os conceitos em projetos pessoais
2. **Explorar** - Teste as ferramentas e agentes apresentados
3. **Validar** - Use observabilidade (LangFuse) para medir resultados
4. **Compartilhar** - Discuta aprendizados com a comunidade

---

**Gerado por:** meeting-analyst agent (framework de 10 seções)
**Data:** 31 de Janeiro de 2026
**Transcrições:** 3 aulas (760KB total)
**Confiança média:** 0.92 (HIGH)
