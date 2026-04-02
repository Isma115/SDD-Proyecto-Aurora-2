# EMS 3D Model Editor

Editor 3D por bloques hecho con HTML, CSS, JavaScript y Three.js, servido con
Python.

## Ejecutar

```bash
python3 server.py
```

Después abre `http://127.0.0.1:8000`.

## Controles

- Flechas: mover y colocar en horizontal según la orientación de la cámara.
- `Q` / `E` o `PgUp` / `PgDn`: subir y bajar.
- `Espacio` o `Enter`: colocar en la posición actual.
- Ratón: cámara orbital.

## Qué hace diferente el mallado

- Cada celda ocupada se guarda en una cuadrícula 3D.
- Al regenerar la malla, las caras internas entre bloques adyacentes
  desaparecen.
- Las caras visibles coplanares se fusionan en rectángulos grandes para evitar
  geometría duplicada.
- La misma base sirve para figuras compuestas por varias celdas, no solo cubos.

## Nota

Three.js y OrbitControls se cargan desde CDN, así que el navegador necesita
acceso a internet para abrir el editor.
