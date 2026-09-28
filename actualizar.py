"""Lee las tablas, resultados, partidos y goleadores de Club Universidad Católica
en ligauniversitaria.org.uy y los guarda en datos.json, que es lo que muestra la web.

Lo ejecuta GitHub todos los días (ver .github/workflows/actualizar.yml).
Qué series se leen está en config-liga.json.
Si algo falla, no toca datos.json y la tarea queda marcada en rojo.
"""
import json, re, sys, time, datetime as dt, urllib.request, urllib.parse

BASE = 'https://ligauniversitaria.org.uy'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
TZ = dt.timezone(dt.timedelta(hours=-3))  # Montevideo

cfg = json.load(open('config-liga.json', encoding='utf-8'))
CLUB = set(cfg['nombresDelClub'])
try:
    previo = json.load(open('datos.json', encoding='utf-8'))
except (FileNotFoundError, ValueError):
    previo = {}
equipos = dict(previo.get('equipos', {}))


def api(carpeta, accion, s):
    q = urllib.parse.urlencode({'action': accion, 'temporada': cfg['temporada'], 'deporte': cfg['deporte'],
                                'torneo': s['torneo'], 'categoria': s['categoria'], 'serie': s['serie']})
    url = f'{BASE}/{carpeta}/api.php?{q}'
    for intento in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode('utf-8'))
            if not isinstance(data, list):
                raise ValueError(f'respuesta inesperada: {str(data)[:120]}')
            return data
        except Exception as e:
            if intento == 2:
                raise RuntimeError(f'No se pudo leer {url}: {e}')
            time.sleep(5)


def tid(nombre):
    if nombre in CLUB:
        return 'cuc'
    return re.sub(r'[^a-z0-9]', '', nombre.lower())[:14]


def equipo(nombre):
    i = tid(nombre)
    if i not in equipos:
        limpio = re.sub(r'\buni\b', '', nombre).strip()
        corto = ''.join(w[0] for w in re.sub(r'\b(CLUB|UNIVERSITARIO|DE|LA|Y)\b', '', limpio).split())[:3].upper()
        equipos[i] = {'nombre': limpio.title(), 'corto': corto or limpio[:3].upper()}
    return i


MINUS = {'DE', 'DEL', 'Y'}
MAYUS = {'CUC', 'XXIII', 'H3O', 'II', 'III', 'LAB', 'JRS.'}


def cancha(c):
    c = re.sub(r'\s+', ' ', (c or '').strip())
    if c in cfg.get('canchas', {}):
        return cfg['canchas'][c]
    out = []
    for w in c.split(' '):
        out.append(w if w in MAYUS else (w.lower() if w in MINUS and out else w.capitalize()))
    return ' '.join(out)


def fecha_hora(s):
    d, h = s.split(' ')
    return d, ('' if h[:5] == '00:00' else h[:5])


def categoria(C):
    tablas, partidos, goles = [], [], {}
    for s in C['series']:
        pos = api('posiciones', 'cargarPosiciones', s)
        res = [p for p in api('resultados', 'cargarPartidos', s) if p['Locatario'] in CLUB or p['Visitante'] in CLUB]
        par = [p for p in api('partidos', 'cargarPartidos', s) if p['Locatario'] in CLUB or p['Visitante'] in CLUB]
        gol = [g for g in api('goleadores', 'cargarPartidos', s) if g.get('Institucion') in CLUB]

        tabla = []
        for r in pos:
            fila = {'equipo': equipo(r['Institucion'])}
            for k, v in (('pj', 'PJ'), ('g', 'PG'), ('e', 'PE'), ('p', 'PP'), ('gf', 'GF'), ('gc', 'GC')):
                fila[k] = int(r[v])
            if int(r['Puntos']) != 3 * fila['g'] + fila['e']:
                print(f"  aviso: {r['Institucion']} tiene puntos que no cierran (quizás una quita)")
            tabla.append(fila)

        jugados = []
        for p in res:
            local = p['Locatario'] in CLUB
            d, h = fecha_hora(p['Fecha_Hora'])
            jugados.append({'fecha': int(p['Fecha']), 'ronda': s['ronda'], 'dia': d, 'hora': h,
                            'rival': equipo(p['Visitante'] if local else p['Locatario']),
                            'condicion': 'L' if local else 'V', 'cancha': cancha(p['Cancha']),
                            'gf': int(p['GL'] if local else p['GV']), 'gc': int(p['GV'] if local else p['GL'])})
        ya = {(p['dia'], p['rival']) for p in jugados}
        sig = max([p['fecha'] for p in jugados] or [0]) + 1
        pendientes = []
        for p in sorted(par, key=lambda x: x['Fecha']):
            local = p['Locatario'] in CLUB
            d, h = fecha_hora(p['Fecha'])
            rival = equipo(p['Visitante'] if local else p['Locatario'])
            if (d, rival) in ya:
                continue
            pendientes.append({'fecha': sig, 'ronda': s['ronda'], 'dia': d, 'hora': h, 'rival': rival,
                               'condicion': 'L' if local else 'V', 'cancha': cancha(p['Cancha'])})
            sig += 1

        mi = next((r for r in tabla if r['equipo'] == 'cuc'), None)
        tablas.append({'nombre': s['nombre'], 'ronda': s['ronda'], 'zonas': s.get('zonas', {}),
                       'acumula': bool(mi and mi['pj'] > len(jugados)), 'tabla': tabla})
        partidos += jugados + pendientes
        for g in gol:
            goles[g['Jugador']] = goles.get(g['Jugador'], 0) + int(g['goles'])
        print(f"  {C['nombre']} / {s['nombre']}: {len(tabla)} equipos, {len(jugados)} jugados, {len(pendientes)} por jugar")

    if not any(r['equipo'] == 'cuc' for r in tablas[0]['tabla']):
        print(f"  aviso: Católica todavía no aparece en la tabla de {tablas[0]['nombre']}")
    return {'nombre': C['nombre'], 'divisional': C.get('divisional', ''), 'torneo': C.get('torneo', ''),
            'fase': C.get('fase', ''), 'ordenOficial': True, 'tablas': tablas, 'partidos': partidos,
            'goleadores': [{'nombre': j.title(), 'goles': n} for j, n in sorted(goles.items(), key=lambda x: -x[1])]}


def main():
    categorias = {}
    for k, C in cfg['categorias'].items():
        print(f'Leyendo {C["nombre"]}...')
        categorias[k] = categoria(C)
    nuevo = {'actualizado': dt.datetime.now(TZ).strftime('%d/%m/%Y'), 'equipos': equipos, 'categorias': categorias}
    # Si lo deportivo no cambió, no se reescribe el archivo (así no hay cambios vacíos todos los días).
    if {k: v for k, v in previo.items() if k != 'actualizado'} == {k: v for k, v in nuevo.items() if k != 'actualizado'}:
        print('Sin novedades en la Liga.')
        return
    with open('datos.json', 'w', encoding='utf-8') as f:
        json.dump(nuevo, f, ensure_ascii=False, indent=1)
    print('datos.json actualizado.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)
