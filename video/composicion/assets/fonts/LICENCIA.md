# Fuentes — procedencia y licencia

Los tres `.ttf` de esta carpeta son **instancias estáticas** generadas a partir de la fuente
variable Inter, con `fontTools.varLib.instancer`, en los ejes `wght` 400 / 600 / 700 y `opsz` 20.

Se generan estáticas porque **matplotlib no lee `woff2`** —el único formato que hay en
`site/public/fonts/`— ni resuelve ejes de una fuente variable. Se cargan por ruta de archivo
explícita, no por familia y peso: pedirle a matplotlib "Inter, semibold" es frágil y acaba
cayendo en DejaVu Sans sin avisar.

## Licencia

**Inter** — Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)

(Cita literal del metadato `name` ID 0 del propio TTF.)

Distribuida bajo la **SIL Open Font License, Version 1.1**.
Texto completo: <https://openfontlicense.org> · <https://github.com/rsms/inter/blob/master/LICENSE.txt>

Lo que la OFL exige y aquí se cumple:

- La fuente se redistribuye **con esta nota de copyright y licencia**.
- Las instancias derivadas **no llevan Reserved Font Name**: Inter no declara ninguno, así que
  conservar el nombre "Inter" es legítimo.
- No se vende la fuente por separado.

La nota equivalente del sitio está en `site/public/fonts/OFL.txt`, que además reproduce el
texto completo de la OFL 1.1 — la licencia exige que el texto viaje con la fuente, no solo un
enlace a él.
