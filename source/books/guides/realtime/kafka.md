# Kafka Integration

Yeti bridges Kafka topics to and from tables using the yeti-kafka service. Consumer reads Kafka messages into tables. Producer publishes table changes to Kafka topics via PubSub.

## Configuration

Enable Kafka in `yeti-config.yaml`:

```yaml
kafka:
  enabled: true
  brokers: ["kafka-1:9092", "kafka-2:9092"]
  consumer:
    topics:
      - topic: sensor-data
        table: SensorReading
        database: my-app
        group_id: yeti-consumer
  producer:
    topics:
      - topic: order-events
        table: Order
        database: my-app
```

## Consumer

The consumer reads messages from Kafka topics and writes them to yeti tables:

1. Connect to the Kafka cluster
2. Subscribe to configured topics
3. Parse each message as JSON
4. `PUT` the record into the target table (keyed by the Kafka message key)

Messages must be valid JSON matching the table schema. Non-JSON messages are logged and skipped.

## Producer

The producer subscribes to table PubSub notifications and publishes changes to Kafka:

1. Subscribe to PubSub notifications for configured tables
2. On each table change (put, patch, delete), serialize the record as JSON
3. Publish to the configured Kafka topic with the record ID as the message key

The producer uses the first-class PubSub API (`table.subscribe_all()`), so it receives all changes regardless of which protocol triggered them (REST, GraphQL, WebSocket, MQTT, or another resource handler).

## Feature Gate

Kafka support is behind a feature flag. Build with:

```bash
cargo build --features kafka
```

The minimal binary (`--no-default-features`) excludes Kafka.

## See Also

- [PubSub](pubsub.md) — The event system that powers the Kafka producer
- [MQTT](mqtt.md) — Native MQTT broker (no external service needed)
