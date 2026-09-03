Tabela densa com cabeçalho caps, colunas mono para números e seleção com trilho petróleo.

```jsx
<DataTable density="comfortable" selectedId="t1" onRowClick={sel}
  columns={[{key:'r',label:'Recurso'},{key:'u',label:'Uso/limite',mono:true,align:'right'},{key:'s',label:'Estado'}]}
  rows={[{id:'t1',r:<b>NSX T1</b>,u:'184/190',s:<StatusBadge state="crit" label="▲ 38 d"/>}]} />
```

Toda coluna numérica: `mono:true` + `align:'right'`.
