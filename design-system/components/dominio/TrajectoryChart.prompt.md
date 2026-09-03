Gráfico-assinatura: histórico sólido → linha do agora → projeção tracejada + cone de incerteza + limites.

```jsx
<TrajectoryChart history={[152,155,162,170,175,181,184]} projection={[184,190,204]}
  opLimit={190} techLimit={200} satIndex={7} satLabel="28 ago · 84%"
  xLabels={['jan','mar','mai','jul','set','dez']} events={[{index:8,label:'expansão (set)'}]}
  ariaText="NSX T1 pode atingir 190 em 28/08 (38 dias), confiança 84%" />
```

`dark` para NOC/login. O cone alarga com a incerteza — nunca omita `ariaText`.
