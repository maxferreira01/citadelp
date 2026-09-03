Badge de estado semântico — glifo + cor + texto, com rótulos PT/EN embutidos.

```jsx
<StatusBadge state="crit" label="▲ 38 dias" />
<StatusBadge state="nocollect" lang="en" />
<StatusBadge state="warn" glyphOnly />
```

Estados: info, ok, warn, crit, emergency, unknown, unavailable, nocollect, stale, divergent. Exporta também `STATUS_STATES` (mapa glifo/cor).
