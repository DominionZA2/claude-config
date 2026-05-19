---
name: trello
description: Connect to the Trello REST API. Use whenever the user mentions Trello, boards, lists, cards, checklists, or labels.
---

# Trello API

- Base URL: `https://api.trello.com/1`
- Auth: every request needs `key` and `token` as query params.
- Credentials: `$env:TRELLO_KEY` and `$env:TRELLO_TOKEN`.
- In PowerShell, always wrap the URL in double quotes so `&` stays inside the string.

## Examples

### Who am I

```powershell
Invoke-RestMethod -Uri "https://api.trello.com/1/members/me?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### List boards

```powershell
Invoke-RestMethod -Uri "https://api.trello.com/1/members/me/boards?fields=name,url,closed&key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### Lists on a board

```powershell
Invoke-RestMethod -Uri "https://api.trello.com/1/boards/$boardId/lists?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### Cards on a list

```powershell
Invoke-RestMethod -Uri "https://api.trello.com/1/lists/$listId/cards?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### Search

```powershell
$q = [uri]::EscapeDataString("text")
Invoke-RestMethod -Uri "https://api.trello.com/1/search?query=$q&modelTypes=cards,boards&key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### Create card

```powershell
$body = @{ idList = $listId; name = "Title"; desc = "Description" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://api.trello.com/1/cards?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN" -ContentType "application/json" -Body $body
```

### Update card (rename, move list, set due, archive)

```powershell
$body = @{ idList = $newListId; name = "New title"; due = "2026-06-15T09:00:00Z"; closed = $false } | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "https://api.trello.com/1/cards/$cardId?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN" -ContentType "application/json" -Body $body
```

### Comment on card

```powershell
$text = [uri]::EscapeDataString("Comment body")
Invoke-RestMethod -Method Post -Uri "https://api.trello.com/1/cards/$cardId/actions/comments?text=$text&key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

### Checklists

```powershell
# List checklists on a card
Invoke-RestMethod -Uri "https://api.trello.com/1/cards/$cardId/checklists?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"

# Add checklist
$body = @{ name = "Steps" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://api.trello.com/1/cards/$cardId/checklists?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN" -ContentType "application/json" -Body $body

# Add item
$body = @{ name = "Item"; checked = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://api.trello.com/1/checklists/$checklistId/checkItems?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN" -ContentType "application/json" -Body $body
```

### Labels

```powershell
# Board labels
Invoke-RestMethod -Uri "https://api.trello.com/1/boards/$boardId/labels?key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"

# Add label to card
Invoke-RestMethod -Method Post -Uri "https://api.trello.com/1/cards/$cardId/idLabels?value=$labelId&key=$env:TRELLO_KEY&token=$env:TRELLO_TOKEN"
```

Full API reference: https://developer.atlassian.com/cloud/trello/rest/
