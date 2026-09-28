# Web de Club Universidad Católica

Web del club en la Liga Universitaria de Deportes: tabla, partidos, rendimiento, galería y sponsors.

## Qué hay en cada archivo

| Archivo | Para qué sirve | ¿Lo toco? |
|---|---|---|
| `index.html` | La web (diseño, textos del club, sponsors) | Solo si cambia el diseño |
| `datos.json` | Tabla, resultados, fixture y goleadores | No: lo actualiza GitHub solo |
| `galeria.json` | Lista de fotos y videos de la galería | Sí, para agregar fotos o videos |
| `galeria/` | Carpeta con las fotos | Sí, acá se suben las fotos |
| `config-liga.json` | Qué tablas de la Liga se leen | Solo cuando la Liga cambia de fase |
| `actualizar.py` | Programa que lee la Liga | No |
| `.github/workflows/actualizar.yml` | Tarea automática (2 veces por día) | No |

## Agregar un video

1. Abrí `galeria.json` y tocá el lápiz (Edit this file).
2. Pegá una línea nueva **arriba de todo**, justo después del `[`, con una coma al final:

```
  {"tipo": "video", "src": "https://www.youtube.com/watch?v=XXXXXXXXXXX", "titulo": "Mayor vs City Park", "fecha": "2026-10-11", "categoria": "mayor"},
```

3. Tocá **Commit changes**. En 1 o 2 minutos aparece en la web.

## Agregar una foto

1. Entrá a la carpeta `galeria`, tocá **Add file → Upload files** y subí la foto.
   Usá nombres sin espacios ni tildes, por ejemplo `mayor-city-park-1.jpg`.
2. En `galeria.json` agregá, igual que el video:

```
  {"tipo": "foto", "src": "galeria/mayor-city-park-1.jpg", "titulo": "Festejo del gol", "fecha": "2026-10-11", "categoria": "mayor"},
```

### Reglas para que no se rompa

- Cada línea va entre `{ }` y termina con coma, **menos la última**, que va sin coma.
- `categoria`: `"mayor"`, `"reserva"`, `"reservaAzul"` o `""` si es de todo el club.
- `fecha` es opcional, con formato `AAAA-MM-DD`.
- Fotos de menos de 2 MB (las del celular conviene achicarlas). Los videos, siempre como link de YouTube o Instagram, no como archivo.
- Si algo queda mal escrito, la tarea de la pestaña **Actions** se pone en rojo, te llega un mail y la web sigue como estaba.

## Actualizar los datos a mano

Pestaña **Actions → Actualizar web de Católica → Run workflow**.
