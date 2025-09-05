def emit_event(event_type, aggregate_id, payload, tenant_id):
    AdEvent.objects.create(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
        payload=payload,
        sequence_number=AdEvent.objects.count() + 1
    )

def replay_events(aggregate_id, tenant_id):
    events = AdEvent.objects.filter(
        aggregate_id=aggregate_id,
        tenant_id=tenant_id
    ).order_by('sequence_number')
    return events