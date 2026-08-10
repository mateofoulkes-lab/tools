from pathlib import Path

p = Path('bomber3d/rig-lab.html')
s = p.read_text(encoding='utf-8')
old = s
s = s.replace('RIG LAB v3.1', 'RIG LAB v3.2')
s = s.replace("version:'3.1'", "version:'3.2'")
s = s.replace('Los dos lados son independientes. Mové X/Y/Z de un modelo y mirá el giro. En KayKit podés <b>reordenar las filas</b> con ↑/↓ o agarrando exclusivamente el control <b>⋮⋮</b>. Los sliders nunca disparan drag-and-drop. Cuando quieras probarlos juntos, activá <b>VINCULAR FILAS</b>.', 'Por defecto, mover un slider mueve también el eje correspondiente del otro modelo. Destildá la opción si querés probar cada lado por separado. En KayKit podés <b>reordenar las filas</b> con ↑/↓ o agarrando exclusivamente <b>⋮⋮</b>. Los sliders nunca disparan drag-and-drop.')
s = s.replace('<input id="linked" type="checkbox"> <b>VINCULAR FILAS</b>', '<input id="linked" type="checkbox" checked> <b>Mover también el eje correspondiente del otro modelo</b>')
if s == old:
    print('Rig Lab v3.2 already applied or expected text not found')
else:
    p.write_text(s, encoding='utf-8')
    print('Applied Rig Lab v3.2 linked-by-default behavior')
