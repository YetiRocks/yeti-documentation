# MQTT

Native MQTT 5.0 broker for IoT devices, sensors, and machine-to-machine communication.

## Enabling MQTT

```yaml
# yeti-config.yaml
interfaces:
  mqtt:
    enabled: true
```

This starts:
- **MQTTS** on port 8883 (TLS-encrypted native MQTT)
- **WebSocket proxy** at `wss://host/mqtt` for browser clients

## Schema Setup

Enable MQTT on a table with the `@export` directive:

```graphql
type SensorReading @table(database: "my-app") @export(
    rest: true
    mqtt: true
) {
    id: ID!
    deviceId: String! @indexed
    temperature: Float!
    humidity: Float!
}
```

## How It Works

MQTT delivery is powered by the same PubSub backbone as SSE and WebSocket:

1. A record is created/updated/deleted (via REST, GraphQL, or any write path)
2. PubSub publishes to the table topic
3. The MQTT bridge forwards the event to all matching MQTT subscribers

```
REST POST /my-app/SensorReading
        |
        v
   +---------+
   |  PubSub  |  notify_update()
   +---------+
     /    |    \
    v     v     v
  SSE    WS   MQTT bridge
               |
               v
         MQTT subscribers
```

## Topics

MQTT topics follow the pattern `{app_id}/{table_name}/{record_id}`:

```
my-app/SensorReading/sensor-001    # specific record
my-app/SensorReading/#             # all records in table (wildcard)
```

## Connecting

### Native MQTT (port 8883)

```bash
# Subscribe (mosquitto_sub)
mosquitto_sub -h localhost -p 8883 \
  --cafile ~/Library/Application\ Support/mkcert/rootCA.pem \
  -t "my-app/SensorReading/#"

# Publish (writes go through REST)
curl -sk -X POST https://localhost:9996/my-app/SensorReading \
  -H "Content-Type: application/json" \
  -d '{"id":"r1","deviceId":"sensor-001","temperature":22.5,"humidity":45.0}'
```

### WebSocket (browser clients)

Connect to `wss://host/mqtt` using any MQTT-over-WebSocket client library (e.g., MQTT.js):

```javascript
import mqtt from 'mqtt'

const client = mqtt.connect('wss://localhost:9996/mqtt')

client.on('connect', () => {
  client.subscribe('my-app/SensorReading/#')
})

client.on('message', (topic, message) => {
  console.log(topic, JSON.parse(message.toString()))
})
```

## Authentication

- **Anonymous**: Clients connecting without credentials can subscribe to tables with `public: [subscribe, connect]` in their `@export` directive
- **Authenticated**: Provide username/password in the MQTT CONNECT packet. Credentials are verified against the yeti-auth User table

## Configuration

| Field | Default | Description |
|-------|---------|-------------|
| `interfaces.mqtt.enabled` | `true` | Enable the MQTT broker |
| `interfaces.mqtt.port` | `8883` | MQTTS listen port |
| `interfaces.mqtt.max_clients` | `10000` | Maximum concurrent MQTT connections |
| `interfaces.mqtt.qos` | `2` | Default QoS level for bridge-published messages (0, 1, or 2) |
| `interfaces.mqtt.audit` | `false` | Enable audit logging for MQTT operations |

## Public Access

Allow unauthenticated MQTT subscribers:

```graphql
type SensorReading @table(database: "my-app") @export(
    mqtt: true
    public: [subscribe, connect]
) {
    id: ID!
    value: Float!
}
```

## See Also

- [Real-Time Overview](realtime-overview.md) -- All streaming options
- [SSE](sse.md) -- Server-Sent Events
- [WebSocket](websocket.md) -- WebSocket connections
- [PubSub](pubsub.md) -- Internal event backbone
