const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/viewport.js', 'utf8');

function setup(viewport) {
    const properties = {};
    const events = {};
    const window = { visualViewport: viewport, innerHeight: 800,
        addEventListener: (name, handler) => { events['window-' + name] = handler; } };
    if (viewport) viewport.addEventListener = (name, handler) => { events[name] = handler; };
    vm.runInNewContext(source, { window, document: { documentElement: {
        style: { setProperty: (key, value) => { properties[key] = value; } }
    } } });
    return { window, properties, events };
}

test('keyboard and viewport scrolling update shell height/offset', () => {
    const viewport = { height: 700, offsetTop: 0, scale: 1 };
    const h = setup(viewport);
    assert.equal(h.properties['--app-height'], '700px');
    viewport.height = 350; viewport.offsetTop = 40;
    h.events.resize(); h.events.scroll();
    assert.equal(h.properties['--app-height'], '350px');
    assert.equal(h.properties['--app-top'], '40px');
    viewport.height = 700; viewport.offsetTop = 0;
    h.events.resize();
    assert.equal(h.properties['--app-height'], '700px');
});

test('does not relayout on pinch zoom', () => {
    const viewport = { height: 700, offsetTop: 0, scale: 1 };
    const h = setup(viewport);
    viewport.height = 350; viewport.scale = 2;
    h.events.resize();
    assert.equal(h.properties['--app-height'], '700px');
});

test('older browsers fall back to innerHeight and window resize', () => {
    const h = setup(null);
    assert.equal(h.properties['--app-height'], '800px');
    h.window.innerHeight = 400;
    h.events['window-resize']();
    assert.equal(h.properties['--app-height'], '400px');
});
