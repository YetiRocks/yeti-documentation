# Server-Sent Events

SSE provides one-way streaming from server to clients over standard HTTP.

## Schema Configuration

```graphql
type Message @table(database: "realtime-demo") @export(
    name: "message"
    rest: true
    sse: true
) {
    id: ID! @primaryKey
    title: String!
    content: String!
}
```

## Connecting

Add `?stream=sse` to any table endpoint:

```bash
curl -sk "https://localhost:9996/realtime-demo/message?stream=sse"
```

## Event Types

| Event | Description | Trigger |
|-------|-------------|---------|
| `message` | Connection confirmed, retained data | Connect |
| `update` | Record created or updated | POST, PUT |
| `delete` | Record deleted | DELETE |
| `publish` | Custom message | PubSub |
| `ping` | Heartbeat | Timer |

```
event: message
data: {"type":"connected","status":"ok"}

event: update
id: msg-1
data: {"id":"msg-1","title":"Hello","content":"World"}

event: delete
id: msg-1
data: {"id":"msg-1"}
```

## JavaScript Client

```javascript
const source = new EventSource(
  'https://localhost:9996/realtime-demo/message?stream=sse'
);

source.addEventListener('update', (event) => {
  const record = JSON.parse(event.data);
  console.log('Updated:', record);
});

source.addEventListener('delete', (event) => {
  const data = JSON.parse(event.data);
  console.log('Deleted:', data.id);
});

source.close();
```

## Record-Level Subscriptions

Subscribe to a single record:

```bash
curl -sk "https://localhost:9996/realtime-demo/message/msg-1?stream=sse"
```

## Testing

**Terminal 1** - listen:
```bash
curl -sk --max-time 60 "https://localhost:9996/realtime-demo/message?stream=sse"
```

**Terminal 2** - write:
```bash
curl -sk -X POST https://localhost:9996/realtime-demo/message \
  -H "Content-Type: application/json" \
  -d '{"id":"test-1","title":"Live","content":"SSE is working"}'
```

## GraphQL Subscriptions

SSE also powers GraphQL subscriptions:

```bash
curl -sk -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "subscription { message { id title content } }"}' \
  https://localhost:9996/realtime-demo/graphql
```

## See Also

- [Real-Time Overview](realtime-overview.md) - All real-time features
- [WebSocket](websocket.md) - Bidirectional alternative
- [PubSub](pubsub.md) - Underlying messaging system
