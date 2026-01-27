# Agent TODOs

This directory contains TODO lists for AI agents working on BlackRoad projects.

## Structure

```
todos/
├── README.md                    # This file
├── global.json                  # Global TODOs for all agents
├── kanban-manager.json          # TODOs for kanban manager agent
├── code-reviewer.json           # TODOs for code review agent
├── pr-validator.json            # TODOs for PR validator agent
├── integration-monitor.json     # TODOs for integration monitor agent
└── deployment-coordinator.json  # TODOs for deployment coordinator agent
```

## TODO Format

Each TODO file follows this JSON structure:

```json
{
  "agent": "agent-name",
  "last_updated": "2026-01-27T00:00:00Z",
  "todos": [
    {
      "id": "todo_001",
      "title": "Task title",
      "description": "Detailed description",
      "priority": "high",
      "status": "pending",
      "created_at": "2026-01-27T00:00:00Z",
      "due_date": null,
      "dependencies": [],
      "linked_cards": ["card_001"],
      "notes": []
    }
  ]
}
```

## Status Values

- `pending` - Not started
- `in_progress` - Currently working on
- `blocked` - Waiting on something
- `completed` - Done
- `cancelled` - No longer needed

## Priority Levels

1. `critical` - Must be done immediately
2. `high` - Important, do soon
3. `medium` - Normal priority
4. `low` - Do when time permits

## Usage

### Reading TODOs

```javascript
const fs = require('fs');
const todos = JSON.parse(fs.readFileSync('.kanban/agents/todos/global.json'));
const pendingTodos = todos.todos.filter(t => t.status === 'pending');
console.log(`${pendingTodos.length} pending todos`);
```

### Updating TODOs

```javascript
const todo = todos.todos.find(t => t.id === 'todo_001');
todo.status = 'in_progress';
todo.notes.push({
  timestamp: new Date().toISOString(),
  message: 'Started working on this'
});
fs.writeFileSync('.kanban/agents/todos/global.json', JSON.stringify(todos, null, 2));
```

## Best Practices

1. **Keep TODOs Atomic** - Each TODO should be a single, completable task
2. **Update Status Promptly** - Change status as soon as you start/finish
3. **Link to Cards** - Always link TODOs to relevant kanban cards
4. **Add Notes** - Document progress and blockers in notes
5. **Check Dependencies** - Don't start tasks with unmet dependencies

## Integration with Kanban

TODOs should map to kanban cards:
- A TODO can be part of a larger card
- Multiple TODOs can belong to one card
- Completing all TODOs should complete the card

## Automation

The kanban sync workflow automatically:
- Creates TODOs from new kanban cards
- Updates card status when TODOs complete
- Notifies agents of new assignments
