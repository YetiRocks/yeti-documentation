# WebSocket

WebSocket provides bidirectional real-time communication. Both client and server can send messages at any time. WebSocket connections subscribe to PubSub topics, receiving the same change events as SSE and MQTT.

## Schema Configuration

```graphql
type Message @table(database: "realtime-demo") @export(
    rest: true
    ws: true
) {
    id: ID! @primaryKey
    title: String!
    content: String!
}
```

WebSocket is enabled at the server level via `interfaces.ws.enabled: true` in `yeti-config.yaml` (the default). No per-app config needed beyond the `@export(ws: true)` directive above.

## Connection

```javascript
const ws = new WebSocket('wss://localhost:9996/my-app/Message');

ws.onopen = () => console.log('Connected');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.message_type === 'Update') updateUI(data.data);
  if (data.message_type === 'Delete') removeFromUI(data.id);
};

// Send data to the server
ws.send(JSON.stringify({
  id: 'msg-new', title: 'From WebSocket', content: 'Sent via WS'
}));
```

## Message Format

Messages follow the same `SubscriptionMessage` format used by PubSub:

```json
{
  "message_type": "Update",
  "data": {"id": "msg-1", "title": "Hello", "content": "World"},
  "id": "msg-1",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Types: `Update`, `Delete`, `Publish`, `Retained`.

## Record-Level Subscriptions

```javascript
const ws = new WebSocket('wss://localhost:9996/my-app/Message/msg-1');
```

## PubSub Integration

WebSocket connections subscribe to PubSub topics. When a record is written via any path (REST, GraphQL, SDK), PubSub broadcasts the change to all subscribed WebSocket connections. A REST write from one client is instantly visible to all WebSocket subscribers.

## Heartbeat

| Setting | Value |
|---------|-------|
| Ping interval | 5 seconds |
| Client timeout | 10 seconds |

Most WebSocket libraries handle ping/pong automatically.

## Reconnection

```javascript
function connect() {
  const ws = new WebSocket('wss://localhost:9996/my-app/Message');
  ws.onclose = () => setTimeout(connect, 3000);
  ws.onmessage = (event) => handleUpdate(JSON.parse(event.data));
}
connect();
```

## SSE vs WebSocket

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Direction | Server to client | Bidirectional |
| Protocol | HTTP/1.1, HTTP/2 | WS/WSS |
| Auto-reconnect | Built-in | Manual |
| Proxy support | Excellent | Varies |
| Use case | Dashboards, feeds | Chat, collaboration |

Use SSE for server-to-client only. Use WebSocket when the client sends data back through the same connection.

## See Also

- [Real-Time Overview](realtime-overview.md) -- All real-time features
- [Server-Sent Events](sse.md) -- One-way streaming
- [PubSub](pubsub.md) -- Underlying messaging backbone
