const fs = require('fs');
const path = require('path');

const htmlPath = path.join(__dirname, '..', 'surf.html');
const html = fs.readFileSync(htmlPath, 'utf-8');
const match = html.match(/<script id="logique">([\s\S]*?)<\/script>/);
if (!match) {
  console.error('Bloc <script id="logique"> introuvable dans surf.html');
  process.exit(1);
}
const factory = new Function(match[1] + '; return { SPOTS, POIDS, interpole, bornes, scoreHauteur, scorePeriode, ecartAngulaire, scoreVent, scoreThermique, scorePression, avisPour, evaluer, annoter };');
const m = factory();

let echecs = 0;
function ok(cond, nom) {
  if (cond) { console.log('ok - ' + nom); } else { console.error('ECHEC - ' + nom); echecs++; }
}
function proche(a, b, nom) { ok(Math.abs(a - b) < 0.01, nom + ' (attendu ~' + b + ', obtenu ' + a + ')'); }

const spot = { cle: 'test', latitude: 43.0, longitude: -1.5, orientation_deg: 300 };

ok(m.interpole(-5, [[0, 10], [10, 20]]) === 10, 'interpole borne basse');
ok(m.interpole(50, [[0, 10], [10, 20]]) === 20, 'interpole borne haute');
proche(m.interpole(5, [[0, 10], [10, 20]]), 15, 'interpole milieu');

ok(m.scoreHauteur(1.5) === 100, 'hauteur ideale = 100');
ok(m.scoreHauteur(0.1) < 30, 'hauteur trop faible');
ok(m.scoreHauteur(6.0) < 30, 'hauteur trop forte');
ok(m.scorePeriode(12) === 100, 'periode longue = 100');
ok(m.scorePeriode(2) < 40, 'periode courte faible');

proche(m.ecartAngulaire(350, 10), 20, 'ecart angulaire 350/10');
proche(m.scoreVent(20, 300, 300), 50, 'vent onshore penalise');
proche(m.scoreVent(20, 120, 300), 80, 'vent offshore bonus');
proche(m.scoreVent(20, 30, 300), 67, 'vent sideshore');
proche(m.scoreVent(20, null, 300), 75, 'vent sans direction');

ok(m.scoreThermique(24, 22) === 100, 'thermique ideal = 100');
ok(m.scoreThermique(null, null) === null, 'thermique sans donnees = null');
ok(m.scorePression(1032) === 100, 'pression haute = 100');
ok(m.scorePression(995) < 60, 'pression basse faible');

const ideal = { hauteur_vagues_m: 1.5, periode_vagues_s: 12, vent_vitesse_kmh: 5, vent_direction_deg: 120, temperature_air_c: 24, temperature_eau_c: 22, pression_hpa: 1024 };
proche(m.evaluer(ideal, spot), 99.7, 'evaluer conditions ideales');
ok(m.evaluer({}, spot) === 0, 'evaluer sans donnees = 0');
proche(m.evaluer({ hauteur_vagues_m: 1.5 }, spot), 100, 'evaluer renormalise');
const mauvais = { hauteur_vagues_m: 0.1, periode_vagues_s: 2, vent_vitesse_kmh: 45, vent_direction_deg: 300, temperature_air_c: 8, temperature_eau_c: 11, pression_hpa: 995 };
ok(m.evaluer(mauvais, spot) < 40, 'evaluer mauvaises conditions < 40');

ok(m.avisPour(80) === 'Excellent', 'avis 80 = Excellent');
ok(m.avisPour(79.9) === 'Bon', 'avis 79.9 = Bon');
ok(m.avisPour(60) === 'Bon', 'avis 60 = Bon');
ok(m.avisPour(40) === 'Moyen', 'avis 40 = Moyen');
ok(m.avisPour(20) === 'Mauvais', 'avis 20 = Mauvais');
ok(m.avisPour(19.9) === 'Très mauvais', 'avis 19.9 = Très mauvais');

const annote = m.annoter({ hauteur_vagues_m: 1.5 }, spot);
ok(annote.score === 100 && annote.avis === 'Excellent', 'annoter renseigne score et avis');

ok(m.SPOTS.length === 7, '7 spots connus');
ok(m.SPOTS.some(s => s.cle === 'hossegor'), 'spot hossegor present');

if (echecs > 0) { console.error(echecs + ' test(s) en echec'); process.exit(1); }
console.log('Tous les tests JS du scoring de surf.html passent.');
