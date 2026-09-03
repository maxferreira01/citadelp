Campo de formulário com rótulo caps, hint e estado de erro.

```jsx
<TextField label="Usuário corporativo" value="m.ferreira" mono />
<TextField label="Bloco CIDR" mono error="Bloco já alocado em TESP02" />
```

`mono` liga JetBrains Mono (IPs, CIDRs, usuários). Erro sempre com glifo ▲ + texto, nunca só cor.
