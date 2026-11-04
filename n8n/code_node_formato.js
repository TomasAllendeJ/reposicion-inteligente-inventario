// NODO CODE (JavaScript) - Arma los mensajes para Gmail / Telegram / registro
const out = $input.first().json.output || {};
const items = out.items || [];
const fecha = out.fecha || new Date().toISOString().slice(0, 10);

const filas = items.map(i =>
  '<tr><td>' + i.item_id + '</td><td>' + i.prioridad + '</td><td>' +
  i.recomendacion + '</td><td>' + i.justificacion + '</td><td>' +
  (i.revision_humana ? 'Si' : 'No') + '</td></tr>'
).join('');

const email_html =
  '<h3>Recomendacion de reposicion - Tienda CA_1 (' + fecha + ')</h3>' +
  '<p><b>' + (out.resumen || '') + '</b></p>' +
  '<table border="1" cellpadding="6" style="border-collapse:collapse">' +
  '<tr><th>SKU</th><th>Prioridad</th><th>Recomendacion</th><th>Justificacion</th><th>Revision humana</th></tr>' +
  filas + '</table>';

const telegram_text =
  'Reposicion CA_1 - ' + fecha + '\n' + (out.resumen || '') + '\n\n' +
  items.map(i => '- [' + i.prioridad + '] ' + i.item_id + ': ' + i.recomendacion +
    (i.revision_humana ? ' (revision humana)' : '')).join('\n');

const n_alta = items.filter(i => i.prioridad === 'alta').length;

return [{ json: {
  fecha: fecha,
  tienda: 'CA_1',
  resumen: out.resumen || '',
  n_items: items.length,
  n_prioridad_alta: n_alta,
  email_html: email_html,
  telegram_text: telegram_text
} }];
