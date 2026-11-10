const $ = (id) => document.getElementById(id);
let token = null;
let game = null;
let selectedLevel = 'easy';
let busy = false;
const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

for (const letter of letters) {
  const button = document.createElement('button');
  button.className = 'key';
  button.type = 'button';
  button.textContent = letter;
  button.dataset.letter = letter.toLowerCase();
  button.setAttribute('aria-label', `Guess ${letter}`);
  button.addEventListener('click', () => send('/api/guess', { guess: button.dataset.letter }));
  $('keyboard').append(button);
}

for (const option of document.querySelectorAll('.level-card')) {
  option.addEventListener('click', () => {
    selectedLevel = option.dataset.level;
    for (const card of document.querySelectorAll('.level-card')) {
      const active = card === option;
      card.classList.toggle('selected', active);
      card.setAttribute('aria-pressed', String(active));
    }
  });
}

async function send(path, payload = {}) {
  if (busy) return;
  busy = true;
  try {
    const response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, ...payload }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Something went wrong.');
    if (data.token) token = data.token;
    game = data.game;
    render();
  } catch (error) {
    $('message').textContent = error.message;
  } finally {
    busy = false;
  }
}

function render() {
  if (!game) return;
  $('setup-view').classList.add('hidden');
  $('play-view').classList.remove('hidden');
  $('round-label').textContent = game.phase === 'bonus' || game.phase.startsWith('bonus_') ? 'BONUS ROUND' : 'WORD GAME';
  $('level-tag').textContent = game.level.toUpperCase();
  $('score').textContent = game.points;
  $('guesses-left').textContent = game.guesses_left;
  $('message').textContent = game.message;
  const word = $('word');
  word.replaceChildren();
  const showAnswer = ['lost', 'bonus_lost', 'won', 'bonus_won', 'complete'].includes(game.phase);
  const visible = showAnswer && game.answer ? Array.from(game.answer) : game.masked_word;
  for (const char of visible) {
    const tile = document.createElement('span');
    tile.className = 'letter-tile' + (char ? ' revealed' : '');
    tile.textContent = char || '\u00a0';
    word.append(tile);
  }
  word.setAttribute('aria-label', visible.map((char) => char || 'blank').join(' '));
  const playing = game.phase === 'main' || game.phase === 'bonus';
  $('playing-controls').classList.toggle('hidden', !playing);
  $('end-controls').classList.toggle('hidden', playing);
  $('bonus-button').classList.toggle('hidden', game.phase !== 'won');
  $('finish-button').classList.toggle('hidden', game.phase !== 'won');
  $('play-again-button').classList.toggle('hidden', playing || game.phase === 'won');
  $('hint-button').disabled = game.phase !== 'main' || game.hint_used;
  $('word-input').value = '';
  for (const key of document.querySelectorAll('.key')) {
    const used = game.guessed_letters.includes(key.dataset.letter);
    key.disabled = used;
    key.classList.toggle('correct', used && game.answer === null && game.masked_word.includes(key.dataset.letter));
    key.classList.toggle('wrong', used && !game.masked_word.includes(key.dataset.letter));
  }
  updateSnowman();
  if (playing) $('word-input').focus();
}

function updateSnowman() {
  const scene = $('scene-panel');
  const lost = game.phase === 'lost' || game.phase === 'bonus_lost';
  const saved = game.phase === 'won' || game.phase === 'bonus_won' || game.phase === 'complete';
  const used = game.max_guesses - game.guesses_left;
  const melt = lost ? 1 : Math.min(1, used / game.max_guesses);
  scene.style.setProperty('--figure-scale', String(1 - melt * .34));
  scene.style.setProperty('--figure-drop', `${Math.round(melt * 43)}px`);
  scene.style.setProperty('--puddle-scale', String(.65 + melt * .95));
  scene.classList.toggle('is-melting', used > 0 && !saved);
  scene.classList.toggle('is-lost', lost);
  scene.classList.toggle('is-saved', saved);
  $('snowman-status').textContent = lost ? 'Melted' : saved ? 'Saved!' : used ? 'Melting' : 'Ready';
  scene.setAttribute('aria-label', `Snowman: ${$('snowman-status').textContent}`);
}

function showSetup() {
  token = null;
  game = null;
  $('setup-view').classList.remove('hidden');
  $('play-view').classList.add('hidden');
  $('round-label').textContent = 'WORD GAME';
  $('score').textContent = '0';
  const scene = $('scene-panel');
  scene.style.setProperty('--figure-scale', '1');
  scene.style.setProperty('--figure-drop', '0px');
  scene.style.setProperty('--puddle-scale', '.65');
  scene.classList.remove('is-melting', 'is-lost', 'is-saved');
  scene.setAttribute('aria-label', 'Snowman: Ready');
  $('snowman-status').textContent = 'Ready';
}

$('start-button').addEventListener('click', () => send('/api/new', { level: selectedLevel }));
$('new-game-top').addEventListener('click', showSetup);
$('play-again-button').addEventListener('click', showSetup);
$('hint-button').addEventListener('click', () => send('/api/hint'));
$('bonus-button').addEventListener('click', () => send('/api/bonus', { play: true }));
$('finish-button').addEventListener('click', () => send('/api/bonus', { play: false }));
$('submit-word').addEventListener('click', submitWord);
$('word-input').addEventListener('keydown', (event) => { if (event.key === 'Enter') submitWord(); });
function submitWord() {
  const guess = $('word-input').value.trim();
  if (guess) send('/api/guess', { guess });
  else $('message').textContent = 'Type a word first.';
}
